"""Defines the top-level dataclass for the histopathology
simulation model configuration parameters.
"""

from typing import Self

import pydantic as pyd
from openpyxl import Workbook

from .arrivals import ArrivalSchedules
from .batching import BatchSizes
from .global_vars import Globals
from .resources import ResourcesInfo
from .runners import RunnerTimesConfig
from .tasks import TaskDurationsInfo


class Config(pyd.BaseModel):
    """Top-level config dataclass for the histopathology simulation model."""
    arrivals: ArrivalSchedules
    batch_sizes: BatchSizes
    global_vars: Globals
    resources: ResourcesInfo
    runner_times: RunnerTimesConfig
    task_durations: TaskDurationsInfo

    sim_hours: pyd.PositiveFloat
    num_reps: pyd.PositiveInt

    @staticmethod
    def from_workbook(
        wbook: Workbook,
        sim_hours: float,
        num_reps: int,
        runner_speed: float | None = None
    ) -> Self:
        """Load a config from an Excel workbook.

        Args:
            wbook: The configuration file (an Excel workbook).
            sim_hours: Number of hours to run the simulation.
            num_reps: Number of times to run the simulation.
            runner_speed:
                Runner speed in m/s. If None, default to the value found in the Excel file.

        Returns:
            Config: The configuration as a Pydantic dataclass.
        """

        arrival_schedules = ArrivalSchedules.from_workbook(wbook)
        resources = ResourcesInfo.from_workbook(wbook)
        task_durations = TaskDurationsInfo.from_workbook(wbook)
        batch_sizes = BatchSizes.from_workbook(wbook)
        global_vars = Globals.from_workbook(wbook)
        runner_cfg = RunnerTimesConfig.from_workbook(wbook, speed=runner_speed)

        return Config(
            arrivals=arrival_schedules,
            batch_sizes=batch_sizes,
            global_vars=global_vars,
            resources=resources,
            runner_times=runner_cfg,
            task_durations=task_durations,
            sim_hours=sim_hours,
            num_reps=num_reps
        )
