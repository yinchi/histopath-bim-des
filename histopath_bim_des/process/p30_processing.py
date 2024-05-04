"""Tissue processing processes.

Todo list :
    - TODO Fix machine start times
    - TODO Weekends as special cases
    - TODO Reduced batch size for urgents (update Model and Config classes)
    - TODO Enforce no splitting of specimen blocks across batches
"""

from typing import TYPE_CHECKING

from ..specimens import Batch, Block, Priority, Specimen
from .core import (BatchingProcess, CollationProcess, DeliveryProcess,
               RunnerDurations, register_process)

if TYPE_CHECKING:
    from ..model import Model


def register_processes(env: 'Model') -> None:
    """Register processes to the simulation environment."""
    register_process(env, Specimen, processing_start)

    register_process(env, Batch[Block], decalc_bone_station)
    register_process(env, Block, decalc_oven)

    register_process(env, Block, processing_assign_queue)
    register_process(env, Batch[Block], processing_urgents)
    register_process(env, Batch[Block], processing_smalls)
    register_process(env, Batch[Block], processing_larges)
    register_process(env, Batch[Block], processing_megas)

    register_process(env, Block, embed_and_trim)
    register_process(env, Specimen, post_processing)

    # Bone station and processing machine batches
    for out, batch_size in zip(
        [
            'decalc_bone_station', 'processing_urgents', 'processing_smalls',
            'processing_larges', 'processing_megas'
        ],
        [
            env.batch_sizes.bone_station,
            env.batch_sizes.processing_regular,
            env.batch_sizes.processing_regular,
            env.batch_sizes.processing_regular,
            env.batch_sizes.processing_megas
        ]
    ):
        env.processes[f'batcher.{out}'] = BatchingProcess[Block](
            f'batcher.{out}',
            batch_size=batch_size,
            out_process=out,
            env=env
        )

    # Collation
    env.processes['collate.processing'] = CollationProcess(
        'collate.processing',
        counter_name='num_blocks',
        out_process='post_processing',
        env=env
    )

    # Delivery
    env.processes['batcher.processing_to_microtomy'] = BatchingProcess[Specimen](
        'batcher.processing_to_microtomy',
        batch_size=env.batch_sizes.deliver_processing_to_microtomy,
        out_process='processing_to_microtomy',
        env=env
    )
    env.processes['processing_to_microtomy'] = DeliveryProcess(
        'processing_to_microtomy',
        runner=env.resources.processing_room_staff,
        durations=RunnerDurations(
            env.runner_times.extra_loading,
            env.runner_times.processing_microtomy,
            env.runner_times.extra_unloading,
            env.runner_times.processing_microtomy  # FUTURE: different outbound and return times?
        ),
        out_process='microtomy',
        env=env
    )


def processing_start(self: Specimen) -> None:
    """Take specimens arriving a processing and send to decalc if necessary.
    Else, send to queue assignment."""
    self.env.wips.in_processing.value += 1
    self.timestamp('processing_start')

    r = self.env.u01()
    if r < self.env.globals.prob_decalc_bone:
        self.env.specimen_data[self.name()]['decalc_type'] = 'bone station'
        out_queue = self.env.processes['batcher.decalc_bone_station'].in_queue
    elif r < self.env.globals.prob_decalc_bone + self.env.globals.prob_decalc_oven:
        self.env.specimen_data[self.name()]['decalc_type'] = 'decalc oven'
        out_queue = self.env.processes['decalc_oven'].in_queue
    else:
        out_queue = self.env.processes['processing_assign_queue'].in_queue

    for block in self.blocks:
        block.enter_sorted(out_queue, self.prio)


def decalc_bone_station(self: Batch[Block]) -> None:
    """Decalc a batch of blocks in a bone station."""
    self.request(self.env.resources.bone_station)

    # Load
    self.request(self.env.resources.bms)
    self.hold(self.env.task_durations.load_bone_station)
    self.release(self.env.resources.bms)

    self.hold(self.env.task_durations.decalc)

    # Unload
    self.request(self.env.resources.bms)
    self.hold(self.env.task_durations.unload_bone_station)
    self.release(self.env.resources.bms)

    self.release()

    # Unbatch and forward to next queue
    for block in self.items:
        block.enter_sorted(self.env.processes['processing_assign_queue'].in_queue, block.prio)


def decalc_oven(self: Block) -> None:
    """Decalc a single block in an oven. Oven capacity is not modelled."""
    # Load
    self.request(self.env.resources.bms)
    self.hold(self.env.task_durations.load_into_decalc_oven)
    self.release()

    self.hold(self.env.task_durations.decalc)

    # Unload
    self.request(self.env.resources.bms)
    self.hold(self.env.task_durations.unload_from_decalc_oven)
    self.release()

    self.enter_sorted(self.env.processes['processing_assign_queue'].in_queue, self.prio)


def processing_assign_queue(self: Block) -> None:
    """Assign incoming blocks to the correct BatchingProcess, according to type."""
    if self.prio == Priority.URGENT:
        out_queue = self.env.processes['batcher.processing_urgents'].in_queue
    elif self.data['block_type'] == 'small surgical':
        out_queue = self.env.processes['batcher.processing_smalls'].in_queue
    elif self.data['block_type'] == 'large surgical':
        out_queue = self.env.processes['batcher.processing_larges'].in_queue
    else:  # 'mega'
        out_queue = self.env.processes['batcher.processing_megas'].in_queue

    self.enter_sorted(out_queue, self.prio)


def processing_urgents(self: Batch[Block]) -> None:
    """Processing machine program for urgent batches."""
    # LOAD
    self.request(
        (self.env.resources.processing_room_staff, 1, Priority.URGENT),
        (self.env.resources.processing_machine, 1, Priority.URGENT)
    )
    self.hold(self.env.task_durations.load_processing_machine)
    self.release(self.env.resources.processing_room_staff)

    # PROCESSING
    self.hold(self.env.task_durations.processing_urgent)

    # UNLOAD
    self.request((self.env.resources.processing_room_staff, 1, Priority.URGENT))
    self.hold(self.env.task_durations.unload_processing_machine)
    self.release()  # all

    # Unbatch and forward to next process
    for block in self.items:
        block.enter_sorted(self.env.processes['embed_and_trim'].in_queue, block.prio)


def processing_generic(self: Batch[Block], duration=float) -> None:
    """Generic processing machine process for non-urgent batches."""
    # LOAD
    self.request(
        self.env.resources.processing_room_staff,
        self.env.resources.processing_machine
    )
    self.hold(self.env.task_durations.load_processing_machine)
    self.release(self.env.resources.processing_room_staff)

    # PROCESSING
    self.hold(duration)

    # UNLOAD
    self.request(self.env.resources.processing_room_staff)
    self.hold(self.env.task_durations.unload_processing_machine)
    self.release()  # all

    # Unbatch and forward to next process
    for block in self.items:
        block.enter_sorted(self.env.processes['embed_and_trim'].in_queue, block.prio)


def processing_smalls(self: Batch[Block]) -> None:
    """Processing machine program for small surgical blocks."""
    processing_generic(self, self.env.task_durations.processing_small_surgicals)


def processing_larges(self: Batch[Block]) -> None:
    """Processing machine program for large surgical blocks."""
    processing_generic(self, self.env.task_durations.processing_large_surgicals)


def processing_megas(self: Batch[Block]) -> None:
    """Processing machine program for mega blocks."""
    processing_generic(self, self.env.task_durations.processing_megas)


def embed_and_trim(self: Block) -> None:
    """Embed a block in wax and trim the excess."""
    # EMBED
    self.request(self.env.resources.processing_room_staff)
    self.hold(self.env.task_durations.embedding)
    self.release()

    # COOLDOWN (no resources tracked)
    self.hold(self.env.task_durations.embedding_cooldown)

    # TRIM
    self.request(self.env.resources.processing_room_staff)
    self.hold(self.env.task_durations.block_trimming)
    self.release()

    self.enter_sorted(self.env.processes["collate.processing"].in_queue, self.prio)


def post_processing(self: Specimen) -> None:
    """Post-processing tasks."""
    self.env.wips.in_processing.value -= 1
    self.timestamp('processing_end')

    if self.prio == Priority.URGENT:
        self.enter_sorted(self.env.processes['processing_to_microtomy'].in_queue, Priority.URGENT)
    else:
        self.enter(self.env.processes['batcher.processing_to_microtomy'].in_queue)
