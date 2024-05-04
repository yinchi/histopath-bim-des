"""Random distributions for the simulation model.

This module overrides the `salabim.Constant` and
`salabim.Triangular` classes to provide better
string representations, and adds a PERT distribution.

See: https://en.wikipedia.org/wiki/PERT_distribution
"""

from typing import Union, Self, Callable

import salabim as sim


class Constant(sim.Constant):
    """Constant distribution.

    Attributes:
        _value (float)
    """

    def __repr__(self) -> str:
        return f'Constant({self._value}, time_unit={self.time_unit})'


class Tri(sim.Triangular):
    """Triangular distribution.

    Attributes:
        _low: Minimum of the distribution
        _mode: Mode of the distribution. If None, replaced with the mean of `_low` and `_high`.
        _high:
            Maximum of the distribution. If None, replaced with `_min`, thus
            forming a constant distribution.
    """

    def __init__(
            self,
            low: float,
            mode: float | None = None,
            high: float | None = None,
            time_unit: str | None = None,
            randomstream=None,
            env: sim.Environment | None = None
    ) -> None:
        # Reorder low,high,mode parameters
        super().__init__(low, high, mode, time_unit, randomstream, env)

    def __repr__(self) -> str:
        return f"Triangular(low={self._low}, mode={self._mode}, high={self._high}, "\
            f"time_unit={self.time_unit})"


class PERT(sim.Triangular):
    """PERT distribution.

    A three-point distribution with more probability mass around the mode than the
    triangular distribution.  The mean of the distribution is
    `(_low + _shape * _mode + _high) / (_shape + 2)`.
    By default, `_shape = 4`.

    Attributes:
        _low: Minimum of the distribution.
        _mode: Mode of the distribution. If None, replaced with the mean of `_low` and `_high`.
        _high:
            Maximum of the distribution. If None, replaced with `_min`,
            thus forming a constant distribution.
    """

    def __init__(
        self,
        low: float,
        mode: float | None = None,
        high: float | None = None,
        time_unit: str | None = None,
        randomstream=None,
        env: sim.Environment | None = None,
    ) -> None:
        super().__init__(low, high, mode, time_unit, randomstream, env)
        self._shape = 4

        self._range = high - low
        self._alpha = 1 + self._shape * (mode - low) / self._range
        self._beta = 1 + self._shape * (high - mode) / self._range

        self._mean = (low + self._shape * mode + high) / (self._shape + 2)

    def __repr__(self) -> str:
        return f"PERT(low={self._low}, mode={self._mode}, high={self._high}, "\
            f"shape={self._shape}, time_unit={self.time_unit})"

    def print_info(self, as_str: bool = False, file: sim.TextIO | None = None) -> str:
        """ Print info about the distribution."""
        result = []
        result.append("PERT " + hex(id(self)))
        result.append("  low=" + str(self._low) + " " + self.time_unit)
        result.append("  high=" + str(self._high) + " " + self.time_unit)
        result.append("  mode=" + str(self._mode) + " " + self.time_unit)
        result.append("  shape=" + str(self._shape))
        result.append("  randomstream=" + hex(id(self.randomstream)))
        return sim.return_or_print(result, as_str, file)

    def sample(self) -> float:
        beta = self.randomstream.betavariate
        val = self._low + beta(self._alpha, self._beta) * self._range
        return val * self.time_unit_factor

    def mean(self) -> float:
        return self._mean * self.time_unit_factor


Distribution = Union[Constant, Tri, PERT]
"""A continuous distribution (constant, triangular, or PERT)."""


class IntPERT:
    """Discretized PERT distribution."""

    def __init__(
        self,
        low: int,
        mode: int,
        high: int,
        randomstream=None,
        env: sim.Environment | None = None
    ):
        self.low = low
        """Minimum of the distribution."""

        self.mode = mode
        """Mode of the distribution."""

        self.high = high
        """Maximum of the distribution."""

        self.pert = PERT(low-mode-0.5, 0, high-mode+0.5, randomstream=randomstream, env=env)
        """Underlying continuous PERT distribution, i.e.
        `PERT(low-mode-0.5, 0, high-mode+0.5)`."""

    def sample(self) -> int:
        """Sample the distribution."""
        return self()

    def __call__(self) -> int:
        # Round towards 0 and add the mode
        return int(self.pert.sample()) + self.mode

    def __repr__(self) -> str:
        return f'IntPERT({self.low}, {self.mode}, {self.high})'


class IntTri:
    """Discretized Triangular distribution."""

    def __init__(
        self,
        low: int,
        mode: int,
        high: int,
        randomstream=None,
        env: sim.Environment | None = None
    ):
        self.low = low
        """Minimum of the distribution."""

        self.mode = mode
        """Mode of the distribution."""

        self.high = high
        """Maximum of the distribution."""

        self.tri = Tri(low-mode-0.5, 0, high-mode+0.5, randomstream=randomstream, env=env)
        """Underlying continuous Tri distribution, i.e.
        `Tri(low-mode-0.5, 0, high-mode+0.5)`."""

    def sample(self) -> int:
        """Sample the distribution."""
        return self()

    def __call__(self) -> int:
        # Round towards 0 and add the mode
        return int(self.tri.sample()) + self.mode

    def __repr__(self) -> str:
        return f'IntPERT({self.low}, {self.mode}, {self.high})'


class IntConstant(sim.Constant):
    """Alias of sim.Constant for integers."""
    value: int

    def __init__(
        self, value: int, randomstream=None, env: sim.Environment = None
    ):
        super().__init__(value, None, randomstream, env)

    sample: Callable[[Self], int]
    __call__: Callable[[Self], int]


IntDistribution = Union[IntConstant, IntTri, IntPERT]
"""A continuous distribution (constant, triangular, or PERT)."""
