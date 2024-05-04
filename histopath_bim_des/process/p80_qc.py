"""Block and quality check processes."""

from typing import TYPE_CHECKING

from ..specimens import Specimen
from .core import register_process

if TYPE_CHECKING:
    from ..model import Model


def register_processes(env: 'Model') -> None:
    """Register processes to the simulation environment."""
    register_process(env, Specimen, qc)

    # Since slides are already scanned, no need to hand to histopathologist after QC,
    # therefore, batching and delivery are not part of this stage.


def qc(self: Specimen) -> None:
    """Block and quality check."""
    self.env.wips.in_qc.value += 1
    self.timestamp('qc_start')

    self.request((self.env.resources.qc_staff, 1, self. prio))
    self.hold(self.env.task_durations.block_and_quality_check)
    self.release()

    self.env.wips.in_qc.value -= 1
    self.timestamp('qc_end')

    self.enter(self.env.processes['assign_histopath'].in_queue)
