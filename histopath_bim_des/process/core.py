"""Common definitions for salabim processes."""

from dataclasses import dataclass
import itertools
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Generic, Type, TypeVar

import salabim as sim

from ..specimens import Batch, Component, Priority, Specimen
from ..util import ARR_RATE_INTERVAL_HOURS, RESOURCE_ALLOCATION_INTERVAL_HOURS

if TYPE_CHECKING:
    from ..config.arrivals import ArrivalSchedule
    from ..config.resources import ResourceSchedule
    from ..model import Model


class ArrivalGenerator(sim.Component):
    """Specimen arrival generator process.

    Attributes:
        iterator (itertools.cycle):
            Iterator yielding the arrival rate for each hourly period.
        cls_args (dict[str, typing.Any]):
            Arguments passed to the :py:class:`~histopath.specimens.Specimen` constructor.
    """

    def __init__(
            self, *args,
            schedule: 'ArrivalSchedule',
            env: 'Model',
            **kwargs) -> None:
        """Constructor.

        Args:
            args (dict[str, typing.Any]):
                Positional arguments passed to the `super()` constructor.
            schedule (ArrivalSchedule): The arrival schedule as a dataclass instance.
            env (Model): The simulation model this arrival generator is attached to.
            kwargs (dict[str, typing.Any]):
                Additional keyword arguments. Arguments not consumed by the
                `super()` constructor become `self.cls_args`.
        """
        super().__init__(*args, **kwargs, env=env, rates=schedule.rates)

    def setup(self, *, rates: list[float], **kwargs) -> None:  # pylint: disable=arguments-differ
        """Set up the component, called immediately after initialisation."""
        self.iterator = itertools.cycle(rates)
        self.cls_args = kwargs

    def process(self) -> None:
        """The generator process. Creates a sub-generator for
        each interval (of length `ARR_RATE_INTERVAL_HOURS`) with the specified rate."""
        for rate in self.iterator:
            if rate > 0:
                sim.ComponentGenerator(
                    Specimen,
                    generator_name=f'{self.name()}_sub',
                    duration=self.env.hours(ARR_RATE_INTERVAL_HOURS),
                    iat=sim.Exponential(rate=rate, randomstream=self.env.rng, env=self.env)
                )
            self.hold(self.env.hours(ARR_RATE_INTERVAL_HOURS))


class ResourceScheduler(sim.Component):
    """Resource scheduler class. The resource level is set every
    `RESOURCE_ALLOCATION_INTERVAL_HOURS` hours. The resource level
    is set to 0 if the day entry in the `ResourceSchedule` is 0.

    Attributes:
        resource (salabim.Resource): The resource to control the allocation of.
        schedule (ResourceSchedule): The resource schedule in dataclass form.
        env (Model): The simulation model this arrival generator is attached to.
    """

    def __init__(self, *args,
                 resource: sim.Resource,
                 schedule: 'ResourceSchedule',
                 env: 'Model',
                 **kwargs) -> None:
        """Constructor.

        Args:
            args (dict[str, typing.Any]):
                Positional arguments passed to the `super()` constructor.
            resource (salabim.Resource)
            schedule (ResourceSchedule)
            env (Model)
            kwargs (dict[str, typing.Any]):
                Additional keyword arguments passed to the `super()` constructor.
        """
        # super().__init__ consumes args and a bunch of kwargs and passes the rest to setup()
        super().__init__(*args, **kwargs, env=env, resource=resource, schedule=schedule)

    def setup(self, *,  # pylint: disable=arguments-differ
              resource: sim.Resource, schedule: 'ResourceSchedule') -> None:
        """Set up the component, called immediately after initialisation."""
        self.resource = resource
        self.schedule = schedule

    def process(self) -> None:
        """Change the resource capacity based on the schedule.
        Capacities are given in 30-min intervals."""
        for day_flag in itertools.cycle(self.schedule.day_flags):
            if day_flag == 0:
                self.resource.set_capacity(0)
                self.hold(self.env.days(1))
            else:
                for allocation in self.schedule.allocation:
                    if allocation != self.resource.capacity() or self.env.now() == 0:
                        self.resource.set_capacity(allocation)
                    self.hold(self.env.hours(RESOURCE_ALLOCATION_INTERVAL_HOURS))


class BaseProcess(sim.Component, ABC):
    """A process with an in-queue. Typically does work on Components
    arriving to the in-queue and pushes completed components to another
    process' in-queue.

    Attributes:
        in_queue (salabim.Store): The in-queue of the process from which entities are taken.
    """

    def __init__(self, *args, env: 'Model', **kwargs) -> None:
        """Constructor."""
        super().__init__(*args, **kwargs, env=env)

    def setup(self) -> None:  # pylint:disable=arguments-differ
        """Set up the component, called immediately after initialisation."""
        self.in_queue = sim.Store(name=f'{self.name()}.in_queue', env=self.env)

    @abstractmethod
    def process(self) -> None:
        """Process launched by the simulation upon instantiation."""


class Process(BaseProcess):
    """A looped processed that takes one entity from its in-queue at a time
    and activates it.

    For example, `Process(name='do_this', Specimen, do_this)` creates
    `Specimen.do_this = do_this` and calls it for every arriving `Specimen`.

    Attributes:
        in_queue (salabim.Store): The in-queue of the process from which entities are taken.
        in_type (typing.Type): The type of the entities to be processed.
        fn (typing.Callable): The function to be activated by each new arrival to the process.
        env (Model): The simulation model this arrival generator is attached to.
    """

    def __init__(
            self, *args, in_type: Type,
            fn: Callable[[Component], None], env: 'Model', **kwargs) -> None:
        super().__init__(*args, in_type=in_type, fn=fn, env=env, **kwargs)

    def setup(  # pylint:disable=arguments-differ
            self, in_type: Type, fn: Callable[[Component], None]) -> None:
        """Set up the component, called immediately after initialisation."""
        super().setup()
        self.in_type = in_type
        # print(self.in_type, self.name())
        setattr(self.in_type, self.name(), fn)

    def process(self) -> None:
        while True:
            self.from_store(self.in_queue)
            entity: Component = self.from_store_item()
            entity.activate(process=self.name())


def register_process(env: 'Model', in_type: Type, fn: Callable[[Component], None]):
    """Register a process to a simulation environment."""
    env.processes[fn.__name__] = Process(
        fn.__name__, in_type=in_type, fn=fn, env=env
    )


C = TypeVar('C', bound=Component)


class BatchingProcess(BaseProcess, Generic[C]):
    """Takes `batch_size` entites from `in_queue` and inserts a single
    instance of `out_type` to `env.processes[out_process].in_queue`.

    Attributes:
        batch_size (int | typing.Callable[[], int]):
            The batch size or its distribution.  Can take `salabim` distributions or any
            other type with ``__call__`` implemented.
        in_queue (salabim.Store): The in-queue of the process from which entities are taken.
        out_process (str): The name of the process receiving the batch.
        env (Model): The simulation model this arrival generator is attached to.
    """

    def __init__(self,
                 *args,
                 batch_size: int | Callable[[], int],
                 out_process: str,
                 env: 'Model',
                 **kwargs) -> None:
        super().__init__(*args, batch_size=batch_size, out_process=out_process, env=env, **kwargs)

    def setup(self,  # pylint:disable=arguments-differ
              batch_size: int | Callable[[], int], out_process: str) -> None:
        """Set up the component, called immediately after initialisation."""
        super().setup()
        self.batch_size = batch_size
        self.out_process = out_process

    def process(self) -> None:
        self.env: 'Model'
        while True:
            batch_size = self.batch_size() if callable(self.batch_size) else self.batch_size
            batch = Batch[C](env=self.env)
            for _ in range(batch_size):
                # FUTURE: implement fail_duration support for partial batching
                self.from_store(self.in_queue)
                item: C = self.from_store_item()
                item.register(batch.items)
            batch.enter(self.env.processes[self.out_process].in_queue)


class CollationProcess(BaseProcess):
    """Takes entities from `in_queue` and places them into a pool.
    Once all entities with the same parent are found (based on comparing
    with a counter), the parent is inserted into
    `env.processes[out_process].in_queue`.

    Attributes:
        counter_name (str):
            The name of the counter in the parent entity defining
            the number of child entities.
        in_queue (salabim.Store): The in-queue of the process from which entities are taken.
        out_process (str):
            The name of the process receiving the reconstituted parent entity.
        env (Model): The simulation model this arrival generator is attached to.
    """

    def __init__(self, *args,
                 counter_name: str,
                 out_process: str,
                 env: 'Model' = None,
                 **kwargs) -> None:
        super().__init__(
            *args, env=env, counter_name=counter_name, out_process=out_process, **kwargs)

    def setup(  # pylint: disable=arguments-differ
            self, counter_name: str, out_process: str) -> None:
        """Set up the component, called immediately after initialisation."""
        super().setup()
        self.counter_name = counter_name
        self.out_process = out_process
        self.dict: dict[str, list[Component]] = {}

    def process(self) -> None:
        self.env: 'Model'

        while True:
            self.from_store(self.in_queue)
            item: Component = self.from_store_item()
            key = item.parent.name()
            if key not in self.dict:
                self.dict[key] = []
            self.dict[key].append(item)

            # Check counter to see if we have all items in the group
            data = (
                self.env.specimen_data[key] if isinstance(item.parent, Specimen)
                else item.parent.data
            )
            if len(self.dict[key]) == data[self.counter_name]:
                item.parent.enter_sorted(
                    self.env.processes[self.out_process].in_queue, item.parent.prio)
                del self.dict[key]


@dataclass
class RunnerDurations:
    """Durations for collecting/unloading the delivery batch and travelling to/from the
    destination.
    """
    collect: float | sim.Distribution  # time to collect delivery batch
    out: float | sim.Distribution     # outbound trip duration
    unload: float | sim.Distribution  # time to unload delivery batch
    retur: float | sim.Distribution     # return trip duration


class DeliveryProcess(BaseProcess):
    """Takes entities/batches from the `in_queue` and places them
    in `env.processes[out_process].in_queue`, after some delay.
    A resource is required to move the entity/batch and requires
    time to travel between the locations associated with the two
    processes.  Batches are unbatched upon arrival.

    Attributes:
        runner (salabim.Resource):
            The resource (e.g. staff) responsible for the delivery.
        durations (RunnerDurations):
            Durations for collecting/unloading the delivery batch and travelling to/from the
            destination.
        out_process (str):
            The name of the process receiving the delivery.
        env (Model): The simulation model this arrival generator is attached to.
    """

    def __init__(self, *args,
                 runner: sim.Resource,
                 durations: RunnerDurations,
                 out_process: str,
                 env: 'Model',
                 **kwargs) -> None:
        super().__init__(*args, env=env, runner=runner, durations=durations,
                         out_process=out_process, **kwargs)

    def setup(  # pylint: disable=arguments-differ
        self,
        runner: sim.Resource,
        durations: RunnerDurations,
        out_process: str
    ) -> None:
        """Set up the component, called immediately after initialisation."""
        super().setup()
        self.runner = runner
        self.durations = durations
        self.out_process = out_process

    def process(self) -> None:
        self.env: Model
        out_queue = self.env.processes[self.out_process].in_queue

        while True:
            self.from_store(self.in_queue)
            entity: Component = self.from_store_item()

            # Deliveries of single items are given the priority of that item (expected to be URGENT)
            delivery_prio = (entity.prio if not isinstance(entity, Batch)
                             else Priority.ROUTINE)

            self.request((self.runner, 1, delivery_prio))

            self.hold(self.durations.collect)
            self.hold(self.durations.out)
            self.hold(self.durations.unload)

            # Unload delivery items
            if isinstance(entity, Batch):
                item: Component
                for item in entity.items:
                    item.enter_sorted(
                        out_queue,
                        priority=item.prio)
            else:
                entity.enter_sorted(
                    out_queue,
                    priority=entity.prio)

            # print(f'Delivered {self.name()} to {out_queue.name()}')

            # return runner to origin station
            self.hold(self.durations.retur)
            self.release()
