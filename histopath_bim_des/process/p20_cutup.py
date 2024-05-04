"""Cut-up processes.

For simplicity, specialities are ignored and all
four cut-up rooms are combined into a single unit
with pooled resources.
"""

from typing import TYPE_CHECKING, Literal

from ..specimens import Block, Priority, Specimen
from .core import BatchingProcess, DeliveryProcess, RunnerDurations, register_process

if TYPE_CHECKING:
    from ..model import Model


def register_processes(env: 'Model') -> None:
    """Register processes to the simulation environment."""
    register_process(env, Specimen, cutup_start)
    register_process(env, Specimen, cutup_bms)
    register_process(env, Specimen, cutup_pool)
    register_process(env, Specimen, cutup_large)

    runner_durations=RunnerDurations(
        env.runner_times.extra_loading,
        env.runner_times.cutup_processing,
        env.runner_times.extra_unloading,
        env.runner_times.cutup_processing  # FUTURE: different outbound and return times?
    )

    # BMS cut-up
    env.processes['batcher.cutup_bms_to_processing'] = BatchingProcess[Specimen](
        'batcher.cutup_bms_to_processing',
        batch_size=env.batch_sizes.deliver_cut_up_to_processing,
        out_process='cutup_bms_to_processing',
        env=env
    )
    env.processes['cutup_bms_to_processing'] = DeliveryProcess(
        'cutup_bms_to_processing',
        runner=env.resources.bms,
        durations=runner_durations,
        out_process='processing_start',
        env=env
    )

    # Pool cut-up
    env.processes['batcher.cutup_pool_to_processing'] = BatchingProcess[Specimen](
        'batcher.cutup_pool_to_processing',
        batch_size=env.batch_sizes.deliver_cut_up_to_processing,
        out_process='cutup_pool_to_processing',
        env=env
    )
    env.processes['cutup_pool_to_processing'] = DeliveryProcess(
        'cutup_pool_to_processing',
        runner=env.resources.cut_up_assistant,
        durations=runner_durations,
        out_process='processing_start',
        env=env
    )

    # Large specimens cut-up
    env.processes['batcher.cutup_large_to_processing'] = BatchingProcess[Specimen](
        'batcher.cutup_large_to_processing',
        batch_size=env.batch_sizes.deliver_cut_up_to_processing,
        out_process='cutup_large_to_processing',
        env=env
    )
    env.processes['cutup_large_to_processing'] = DeliveryProcess(
        'cutup_large_to_processing',
        runner=env.resources.cut_up_assistant,
        durations=runner_durations,
        out_process='processing_start',
        env=env
    )


def cutup_start(self: Specimen) -> None:
    """Take specimens arriving at cut-up and sort to the correct cut-up queue."""
    self.env.wips.in_cut_up.value += 1
    self.timestamp('cutup_start')

    suffix = '_urgent' if self.prio == Priority.URGENT else ''
    if (r := self.env.u01()) < getattr(self.env.globals, f'prob_bms_cutup{suffix}'):
        cutup_type, next_process = 'BMS', 'cutup_bms'
    elif r < getattr(self.env.globals, f'prob_bms_cutup{suffix}')\
            + getattr(self.env.globals, f'prob_pool_cutup{suffix}'):
        cutup_type, next_process = 'Pool', 'cutup_pool'
    else:
        cutup_type, next_process = 'Large specimens', 'cutup_large'

    self.env.specimen_data[self.name()]['cutup_type'] = cutup_type
    self.enter_sorted(self.env.processes[next_process].in_queue, self.prio)


def cutup_generic(self: Specimen, cutup_type: Literal['bms', 'pool', 'large']) -> None:
    """Generic process function for specimen cut-up.

    Args:
        self (Specimen): The specimen to cut up.
        cutup_type (Literal['bms', 'pool', 'large']): The type of cut-up task.
    """
    resource = (
        self.env.resources.bms if cutup_type == 'bms'
        else self.env.resources.cut_up_assistant
    )

    duration = (
        self.env.task_durations.cut_up_bms if cutup_type == 'bms'
        else self.env.task_durations.cut_up_pool if cutup_type == 'pool'
        else self.env.task_durations.cut_up_large_specimens
    )

    r = self.env.u01()
    block_type = (
        'small surgical' if cutup_type == 'bms'
        else 'large surgical' if cutup_type == 'pool'
        else 'large surgical' if (self.prio == Priority.URGENT
                                  or r < self.env.globals.prob_mega_blocks)
        else 'mega'
    )

    n_blocks = (
        (
            self.env.globals.num_blocks_mega() if block_type == 'mega'
            else self.env.globals.num_blocks_large_surgical()
        ) if cutup_type == 'large'
        else 1
    )

    # Generate blocks
    self.request((resource, 1, self.prio))

    self.hold(duration)
    for _ in range(n_blocks):
        self.blocks.append(
            Block(
                f'{self.name()}.',
                env=self.env,
                parent=self,
                block_type=block_type
            )
        )
    self.env.specimen_data[self.name()]['num_blocks'] = n_blocks

    self.release()

    # Cut-up complete
    self.env.wips.in_cut_up.value -= 1
    self.timestamp('cutup_end')

    # Delivery
    if self.prio == Priority.URGENT:
        self.enter_sorted(
            self.env.processes[f'cutup_{cutup_type}_to_processing'].in_queue, Priority.URGENT)
    else:
        self.enter(self.env.processes[f'batcher.cutup_{cutup_type}_to_processing'].in_queue)


def cutup_bms(self: Specimen) -> None:
    """BMS cut-up. Always produces 1 small surgical block."""
    cutup_generic(self, 'bms')


def cutup_pool(self: Specimen) -> None:
    """Pool cut-up. Always produces 1 large surgical block."""
    cutup_generic(self, 'pool')


def cutup_large(self: Specimen) -> None:
    """BMS cut-up. Produces a random number of large surgical blocks."""
    cutup_generic(self, 'large')
