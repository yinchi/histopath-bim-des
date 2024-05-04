"""Histopath reporting processes."""

from typing import TYPE_CHECKING

from ..specimens import Specimen
from .core import register_process

if TYPE_CHECKING:
    from ..model import Model


def register_processes(env: 'Model') -> None:
    """Register processes to the simulation environment."""
    register_process(env, Specimen, assign_histopath)
    register_process(env, Specimen, report)


def assign_histopath(self: Specimen) -> None:
    """Assign a histopathologist to the specimen."""
    self.request((self.env.resources.qc_staff, 1, self.prio))
    self.hold(self.env.task_durations.assign_histopathologist)
    self.release()
    self.enter(self.env.processes['report'].in_queue)


def report(self: Specimen) -> None:
    """Write the final histopathological report."""
    self.env.wips.in_reporting.value += 1
    self.timestamp('report_start')

    self.request((self.env.resources.histopathologist, 1, self.prio))
    self.hold(self.env.task_durations.write_report)
    self.release()

    self.env.wips.in_reporting.value -= 1
    self.timestamp('report_end')
    self.env.wips.total.value -= 1

    # FINISHED - NO self.enter
