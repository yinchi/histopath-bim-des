"""Defines specimens, blocks, and slides."""
from enum import IntEnum
from abc import ABC
from typing import TYPE_CHECKING, Generic, TypeVar

import salabim as sim

if TYPE_CHECKING:
    from .model import Model


class Priority(IntEnum):
    """Specimen priority. Lower value = higher priority."""
    ROUTINE = 0
    CANCER = -1
    PRIORITY = -2
    URGENT = -3


class Component(sim.Component, ABC):
    """A salabim component with additional fields."""

    prio: Priority
    """Priority of the component (Urgent, Priority, Cancer, or Routine)."""

    parent: 'Component | None'
    """The parent component, if it exists."""


C = TypeVar('C', bound=Component)


class Specimen(Component):
    """A tissue specimen.

    Atrributes:
        blocks:
            The list of blocks produced from this specimen, empty if cut-up has not yet started.
    """

    def setup(self, **kwargs) -> None:
        """Set up the component, called immediately after initialisation."""
        self.env: Model

        self.env.specimen_data[self.name()] = kwargs
        self.blocks: list[Block] = []

        self.env.specimen_data[self.name()]['source'] = sim.CumPdf(
            spec=('Internal', 'External'),
            cumprobabilities=(self.env.globals.prob_internal, 1),
            randomstream=self.env.rng,
            env=self.env
        ).sample()

        dist = 'cancer' if kwargs.get('cancer', False) else 'non_cancer'
        self.prio: Priority = sim.CumPdf(
            spec=(
                Priority.URGENT,
                Priority.PRIORITY,
                Priority.CANCER if dist == 'cancer' else Priority.ROUTINE
            ),
            cumprobabilities=(
                getattr(self.env.globals, f'prob_urgent_{dist}'),
                getattr(self.env.globals, f'prob_urgent_{dist}')
                + getattr(self.env.globals, f'prob_priority_{dist}'),
                1
            ),
            randomstream=self.env.rng,
            env=self.env
        ).sample()
        self.env.specimen_data[self.name()]['priority'] = self.prio.name

    def process(self):
        """Insert specimen into the `arrive_reception` in-queue."""
        self.enter(self.env.processes['arrive_reception'].in_queue)

    def timestamp(self, name: str):
        """Save timestamp data to `self.env.specimen_data`."""
        self.env.specimen_data[self.name()][name] = self.env.now()


class Block(Component):
    """A wax block (or cassette to be turned into a wax block).
    
    Atrributes:
        slides:
            The list of slides produced from this specimen, empty if microtomy has not yet started.
        data:
            A dict of additional data associated with the block.
    """

    def setup(self, parent: Specimen, **kwargs) -> None:  # pylint: disable=arguments-differ
        """Set up the component, called immediately after initialisation."""
        self.env: Model

        self.parent = parent
        self.prio = self.parent.prio
        self.slides: list[Slide] = []
        self.data = kwargs


class Slide(Component):
    """A glass slide.
    
    Atrributes:
        data:
            A dict of additional data associated with the slide.
    """

    def setup(self, parent: Block, **kwargs) -> None:  # pylint: disable=arguments-differ
        """Set up the component, called immediately after initialisation."""
        self.env: Model

        self.parent: Block = parent
        self.prio = self.parent.prio
        self.data = kwargs


class Batch(Component, Generic[C]):
    """A batch of Component objects.
    
    Attributes:
        items: The list of items within the batch.
        data:
            A dict of additional data associated with the batch.
    """

    def setup(self, **kwargs) -> None:  # pylint: disable=arguments-differ
        """Set up the component, called immediately after initialisation."""
        self.env: Model

        self.data = kwargs
        self.items: list[C] = []
