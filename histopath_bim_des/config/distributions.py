"""Defines a dataclass for a discrete probability distribution on the integers."""
import typing as ty

import pydantic as pyd


class DistributionInfo(pyd.BaseModel):
    """Information describing a three-point random distributions for task durations."""

    type: ty.Literal['Constant', 'Triangular', 'PERT']  # Supported distribution types
    """The type of the distribution, one of 'Constant', 'Triangular', or 'PERT'."""

    low: pyd.NonNegativeFloat
    """The minimum value of the distribution."""

    mode: pyd.NonNegativeFloat
    """The most likely value of the distribution."""

    high: pyd.NonNegativeFloat
    """The maximum of the distribution."""

    time_unit: ty.Literal['s', 'm', 'h']
    """The time unit of the distribution, i.e. seconds, minutes, or hours.  Represented by the
    first letter; the validator will accept any string starting with 's', 'm', or 'h'."""

    @pyd.field_validator('time_unit', mode='before')
    @classmethod
    def _first_letter(cls, time_unit_str: str) -> str:
        """Take only the first letter from a time-unit string.

        For simplicity, only the first character of time-unit strings are checked, i.e.
        "hours", "hour", and "hxar" are identical.
        """
        assert time_unit_str[0] in ['s', 'm', 'h']
        return time_unit_str[0]

    @pyd.model_validator(mode='after')
    def _enforce_ordering(self) -> 'DistributionInfo':
        """Ensure that the the ``low``, ``mode`` and ``high`` parameters of the distribution
        are in non-decreasing order."""
        # Constant case
        if self.type == 'Constant':
            return __class__.model_construct(
                type='Constant', low=self.mode, mode=self.mode, high=self.mode,
                time_unit=self.time_unit
            )
        # Other cases
        assert self.mode >= self.low, 'Failed requirement: mode >= low'
        assert self.high >= self.mode, 'Failed requirement: high >= mode'
        return self


class IntDistributionInfo(pyd.BaseModel):
    """Information describing a discretised three-point random distribution.
    The underlying continuous distribution is constructed with parameters
    `(low - 0.5, mode, high + 0.5)`.
    """

    type: ty.Literal['Constant', 'IntTriangular', 'IntPERT']  # Supported distribution types
    """Type of the distribution."""

    low: pyd.NonNegativeInt
    """Minimum value of the distribution."""

    mode: pyd.NonNegativeInt
    """Most likely value of the distribution, before discretisation."""

    high: pyd.NonNegativeInt
    """Maximum value of the distribution."""

    @pyd.model_validator(mode='after')
    def _enforce_ordering(self) -> ty.Self:
        """Ensure that the the ``low``, ``mode`` and ``high`` parameters of the distribution
        are in non-decreasing order."""
        # Constant case
        if self.type == 'Constant':
            return __class__.model_construct(
                type='Constant', low=self.mode, mode=self.mode, high=self.mode)
        # Other cases
        assert self.mode >= self.low, 'Failed requirement: mode >= low'
        assert self.high >= self.mode, 'Failed requirement: high >= mode'
        return self
