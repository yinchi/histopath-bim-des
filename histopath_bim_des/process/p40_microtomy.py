"""Microtomy processes."""

from typing import TYPE_CHECKING

from ..specimens import Priority, Slide, Specimen
from .core import (BatchingProcess, DeliveryProcess, RunnerDurations,
                       register_process)

if TYPE_CHECKING:
    from ..model import Model


def register_processes(env: 'Model') -> None:
    """Register processes to the simulation environment."""
    register_process(env, Specimen, microtomy)

    env.processes['batcher.microtomy_to_staining'] = BatchingProcess[Specimen](
        'batcher.microtomy_to_staining',
        batch_size=env.batch_sizes.deliver_microtomy_to_staining,
        out_process='microtomy_to_staining',
        env=env
    )

    env.processes['microtomy_to_staining'] = DeliveryProcess(
        'microtomy_to_staining',
        runner=env.resources.microtomy_staff,
        durations=RunnerDurations(
            env.runner_times.extra_loading,
            env.runner_times.microtomy_staining,
            env.runner_times.extra_unloading,
            env.runner_times.microtomy_staining  # FUTURE: different outbound and return times?
        ),
        out_process='staining_start',
        env=env
    )


def microtomy(self: Specimen) -> None:
    """Generate all slides for a specimen."""
    self.env.wips.in_microtomy.value += 1
    self.timestamp('microtomy_start')
    self.env.specimen_data[self.name()]['total_slides'] = 0

    for block in self.blocks:
        # Each block is a separate seize-release
        self.request((self.env.resources.microtomy_staff, 1, self.prio))

        if block.data['block_type'] == 'small surgical':
            if self.env.u01() < self.env.globals.prob_microtomy_levels:
                slide_type = 'levels'
                self.hold(self.env.task_durations.microtomy_levels)
                num_slides = self.env.globals.num_slides_levels.sample()
            else:
                slide_type = 'serials'
                self.hold(self.env.task_durations.microtomy_serials)
                num_slides = self.env.globals.num_slides_serials.sample()
        elif block.data['block_type'] == 'large surgical':
            slide_type = 'larges'
            self.hold(self.env.task_durations.microtomy_larges)
            num_slides = self.env.globals.num_slides_larges()
        else:  # 'mega'
            slide_type = 'megas'
            self.hold(self.env.task_durations.microtomy_megas)
            num_slides = self.env.globals.num_slides_megas()

        for _ in range(num_slides):
            block.slides.append(
                Slide(
                    f'{block.name()}.',
                    parent=block,
                    slide_type=slide_type,
                    env=self.env
                )
            )
        block.data['num_slides'] = num_slides
        self.env.specimen_data[self.name()]['total_slides'] += num_slides

        self.release()

    self.env.wips.in_microtomy.value -= 1
    self.timestamp('microtomy_end')

    # Delivery
    if self.prio == Priority.URGENT:
        self.enter_sorted(self.env.processes['microtomy_to_staining'].in_queue, Priority.URGENT)
    else:
        self.enter(self.env.processes['batcher.microtomy_to_staining'].in_queue)
