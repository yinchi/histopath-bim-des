"""Reception processes."""

from typing import TYPE_CHECKING

from ..specimens import Priority, Specimen
from .core import (BatchingProcess, DeliveryProcess, RunnerDurations,
               register_process)

if TYPE_CHECKING:
    from ..model import Model


def register_processes(env: 'Model') -> None:
    """Register processes to the simulation environment."""
    register_process(env, Specimen, arrive_reception)
    register_process(env, Specimen, booking_in)

    env.processes['batcher.reception_to_cutup'] = BatchingProcess[Specimen](
        'batcher.reception_to_cutup',
        batch_size=env.batch_sizes.deliver_reception_to_cut_up,
        out_process='reception_to_cutup',
        env=env
    )
    env.processes['reception_to_cutup'] = DeliveryProcess(
        '',
        runner=env.resources.booking_in_staff,
        durations=RunnerDurations(
            env.runner_times.extra_loading,
            env.runner_times.reception_cutup,
            env.runner_times.extra_unloading,
            env.runner_times.reception_cutup  # FUTURE: different outbound and return times?
        ),
        out_process='cutup_start',
        env=env
    )


def arrive_reception(self: Specimen) -> None:
    """Called for each new Specimen arrival."""
    self.env.wips.total.value += 1
    self.env.wips.in_reception.value += 1
    self.timestamp('reception_start')

    # For booking-in staff, receiving new specimens always takes priority
    # over all non-urgent booking-in tasks
    self.request((self.env.resources.booking_in_staff, 1, Priority.URGENT))
    self.hold(self.env.task_durations.receive_and_sort)
    self.release()
    self.enter_sorted(self.env.processes['booking_in'].in_queue, self.prio)


def booking_in(self: Specimen) -> None:
    """Book a specimen into the system."""
    is_internal = self.env.specimen_data[self.name()]['source'] == 'Internal'
    global_vars = self.env.globals
    task_durations = self.env.task_durations

    self.request((self.env.resources.booking_in_staff, 1, self.prio))

    # Pre-booking-in investigation
    if self.env.u01() < global_vars.prob_prebook:
        self.hold(task_durations.pre_booking_in_investigation)

    # Booking-in
    if is_internal:
        self.hold(task_durations.booking_in_internal)
    else:
        self.hold(task_durations.booking_in_external)

    # Additional investigation
    if is_internal:
        if (r := self.env.u01()) < global_vars.prob_invest_easy:
            self.hold(task_durations.booking_in_investigation_internal_easy)
        elif r < global_vars.prob_invest_hard:
            self.hold(task_durations.booking_in_investigation_internal_hard)

    elif self.env.u01() < global_vars.prob_invest_external:
        self.hold(task_durations.booking_in_investigation_external)

    # Booking-in complete
    self.release()
    self.timestamp('reception_end')
    self.env.wips.in_reception.value -= 1

    # Delivery
    if self.prio == Priority.URGENT:
        self.enter_sorted(self.env.processes['reception_to_cutup'].in_queue, Priority.URGENT)
    else:
        self.enter(self.env.processes['batcher.reception_to_cutup'].in_queue)
