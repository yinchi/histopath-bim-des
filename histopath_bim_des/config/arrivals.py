"""Arrival process configuration module for the histopath simulation model."""

import typing as ty

import pandas as pd
import pydantic as pyd
from annotated_types import Annotated, Len
from openpyxl import Workbook

from .. import excel


class ArrivalSchedule(pyd.BaseModel):
    """An arrival schedule for specimens."""

    rates: Annotated[ty.Sequence[pyd.NonNegativeFloat], Len(168, 168)]
    "Hourly arrival rates for the arrival process, for one week (168 hours)."

    @staticmethod
    def from_pd(df: pd.DataFrame) -> 'ArrivalSchedule':
        """Construct an arrival schedule from a dataframe with the 24 hours the day as rows
        and the seven days of the week as columns (starting on Monday).  Each value is the
        arrival rate for one hour of the week

        Args:
            df: The dataframe containing the arrival schedule information.

        Returns:
            The ArrivalSchedule object.
        """
        return __class__(rates=df.to_numpy().flatten('F').tolist())  # F = column-major order


class ArrivalSchedules(pyd.BaseModel):
    """Dataclass for tracking the specimen arrival schedules of the histopathology model."""

    cancer: ArrivalSchedule
    """Arrival schedule for cancer pathway specimens."""

    noncancer: ArrivalSchedule
    """Arrival schedule for non-cancer pathway specimens."""

    @staticmethod
    def from_workbook(wbook: Workbook) -> 'ArrivalSchedules':
        """Construct a dataclass instance from an Excel workbook.

        Args:
            wbook: The Excel workbook to parse.

        Returns:
            The parsed dataclass instance.
        """
        arrival_schedule_cancer_df = (
            df := pd.DataFrame(
                (
                    table := excel.get_table(wbook, 'Arrival Schedules', 'ArrivalScheduleCancer')
                )[1:],
                columns=table[0]
            ).set_index('Hour')
        ).loc[df.index != 'Total']

        arrival_schedule_noncancer_df = (
            df := pd.DataFrame(
                (
                    table := excel.get_table(wbook, 'Arrival Schedules', 'ArrivalScheduleNonCancer')
                )[1:],
                columns=table[0]
            ).set_index('Hour')
        ).loc[df.index != 'Total']

        return ArrivalSchedules(
            cancer=ArrivalSchedule.from_pd(arrival_schedule_cancer_df),
            noncancer=ArrivalSchedule.from_pd(arrival_schedule_noncancer_df),
        )
