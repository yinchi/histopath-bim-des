"""Staining and cover-slip processes."""

from typing import TYPE_CHECKING

from ..specimens import Batch, Priority, Slide, Specimen
from .core import (BatchingProcess, CollationProcess, DeliveryProcess,
                       RunnerDurations, register_process)

if TYPE_CHECKING:
    from ..model import Model


def register_processes(env: 'Model') -> None:
    """Register processes to the simulation environment."""
    register_process(env, Specimen, staining_start)
    register_process(env, Batch[Slide], staining_regular)
    register_process(env, Batch[Slide], staining_megas)
    register_process(env, Specimen, post_staining)

    # Staining machine batches
    env.processes['batcher.staining_regular'] = BatchingProcess[Slide](
        'batcher.staining_regular',
        batch_size=env.batch_sizes.staining_regular,
        out_process='staining_regular',
        env=env
    )
    env.processes['batcher.staining_megas'] = BatchingProcess[Slide](
        'batcher.staining_megas',
        batch_size=env.batch_sizes.staining_megas,
        out_process='staining_megas',
        env=env
    )

    # Collation
    env.processes['collate.staining.slides'] = CollationProcess(
        'collate.staining.slides',
        counter_name='num_slides',
        out_process='collate.staining.blocks',
        env=env
    )
    env.processes['collate.staining.blocks'] = CollationProcess(
        'collate.staining.blocks',
        counter_name='num_blocks',
        out_process='post_staining',
        env=env
    )

    # Delivery
    env.processes['batcher.staining_to_labelling'] = BatchingProcess[Specimen](
        'batcher.staining_to_labelling',
        batch_size=env.batch_sizes.deliver_staining_to_labelling,
        out_process='staining_to_labelling',
        env=env
    )
    env.processes['staining_to_labelling'] = DeliveryProcess(
        'staining_to_labelling',
        runner=env.resources.microtomy_staff,
        durations=RunnerDurations(
            env.runner_times.extra_loading,
            env.runner_times.staining_labelling,
            env.runner_times.extra_unloading,
            env.runner_times.staining_labelling  # FUTURE: different outbound and return times?
        ),
        out_process='labelling',
        env=env
    )


def staining_start(self: Specimen) -> None:
    """Separate specimen slides and send to batching process for staining."""
    self.env.wips.in_staining.value += 1
    self.timestamp('staining_start')

    for block in self.blocks:
        for slide in block.slides:
            slide.enter_sorted(
                self.env.processes[
                    'batcher.staining_megas'
                    if slide.data['slide_type'] == 'megas'
                    else 'batcher.staining_regular'
                ].in_queue,
                self.prio
            )


def staining_regular(self: Batch[Slide]) -> None:
    """Stain and cover-slip a batch of regular-sized slides."""

    # LOAD
    self.request(self.env.resources.staining_staff, self.env.resources.staining_machine)
    self.hold(self.env.task_durations.load_staining_machine_regular)
    self.release(self.env.resources.staining_staff)

    # STAIN
    self.hold(self.env.task_durations.staining_regular)

    # TRANSFER TO COVERSLIP MACHINE
    self.request(self.env.resources.staining_staff)
    self.hold(self.env.task_durations.unload_staining_machine_regular)
    self.release()

    self.request(self.env.resources.staining_staff, self.env.resources.coverslip_machine)
    self.hold(self.env.task_durations.load_coverslip_machine_regular)
    self.release(self.env.resources.staining_staff)

    # COVERSLIP
    self.hold(self.env.task_durations.coverslip_regular)

    # UNLOAD COVERSLIP MACHINE
    self.request(self.env.resources.staining_staff)
    self.hold(self.env.task_durations.unload_coverslip_machine_regular)
    self.release()  # release all

    for slide in self.items:
        slide.enter(self.env.processes['collate.staining.slides'].in_queue)


def staining_megas(self: Batch[Slide]) -> None:
    """Stain and cover-slip a batch of mega slides."""

    # LOAD
    self.request(self.env.resources.staining_staff, self.env.resources.staining_machine)
    self.hold(self.env.task_durations.load_staining_machine_megas)
    self.release(self.env.resources.staining_staff)

    # STAIN
    self.hold(self.env.task_durations.staining_megas)

    # UNLOAD
    self.request(self.env.resources.staining_staff)
    self.hold(self.env.task_durations.unload_staining_machine_megas)
    self.release(self.env.resources.staining_machine)
    # Keep staining staff for coverslipping tasks

    for slide in self.items:
        # MANUAL COVERSLIPPING FOR MEGA SLIDES
        self.hold(self.env.task_durations.coverslip_megas)
        slide.enter(self.env.processes['collate.staining.slides'].in_queue)

    self.release()  # release all


def post_staining(self: Specimen) -> None:
    """Post-staining tasks."""
    self.env.wips.in_staining.value -= 1
    self.timestamp('staining_end')

    if self.prio == Priority.URGENT:
        self.enter_sorted(self.env.processes['staining_to_labelling'].in_queue, Priority.URGENT)
    else:
        self.enter(self.env.processes['batcher.staining_to_labelling'].in_queue)
