"""Labelling processes."""

from typing import TYPE_CHECKING

from ..specimens import Priority, Specimen
from .core import (BatchingProcess, DeliveryProcess, RunnerDurations,
                       register_process)

if TYPE_CHECKING:
    from ..model import Model


def register_processes(env: "Model") -> None:
    """Register processes to the simulation environment."""
    # Labelling is done in the "main lab", i.e. microtomy

    register_process(env, Specimen, labelling)

    env.processes['batcher.labelling_to_scanning'] = BatchingProcess[Specimen](
        'batcher.labelling_to_scanning',
        batch_size=env.batch_sizes.deliver_labelling_to_scanning,
        out_process='labelling_to_scanning',
        env=env
    )
    env.processes['labelling_to_scanning'] = DeliveryProcess(
        'labelling_to_scanning',
        runner=env.resources.microtomy_staff,
        durations=RunnerDurations(
            env.runner_times.extra_loading,
            env.runner_times.labelling_scanning,
            env.runner_times.extra_unloading,
            env.runner_times.labelling_scanning  # FUTURE: different outbound and return times?
        ),
        out_process='scanning_start',
        env=env
    )


def labelling(self: Specimen) -> None:
    """Label all slides of a specimen."""
    self.env.wips.in_labelling.value += 1
    self.timestamp('labelling_start')

    self.request((self.env.resources.microtomy_staff, 1, self. prio))
    for block in self.blocks:
        for _ in block.slides:
            self.hold(self.env.task_durations.labelling)
    self.release()

    self.env.wips.in_labelling.value -= 1
    self.timestamp('labelling_end')

    if self.prio == Priority.URGENT:
        self.enter_sorted(self.env.processes['labelling_to_scanning'].in_queue, Priority.URGENT)
    else:
        self.enter(self.env.processes['batcher.labelling_to_scanning'].in_queue)
