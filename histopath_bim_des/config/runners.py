"""Runner-related configuration module for the histopath simulation model."""
from collections.abc import Sequence
from typing import Self

import pandas as pd
from openpyxl import Workbook
from pydantic import AliasChoices, BaseModel, Field, NonNegativeFloat

from .. import excel


class ProcessDoorMap(BaseModel):
    """A mapping of process stages to door names.
    Each door name corresponds to a room where the the
    process takes place.

    Note that some processes (e.g., cutup) may take place in multiple rooms.
    """
    reception: str | Sequence[str] = Field(validation_alias='Reception')
    cutup: str | Sequence[str] = Field(validation_alias=AliasChoices('Cutup', 'Cut-up'))
    processing: str | Sequence[str] = Field(validation_alias='Processing')
    microtomy: str | Sequence[str] = Field(validation_alias='Microtomy')
    staining: str | Sequence[str] = Field(validation_alias='Staining')
    labelling: str | Sequence[str] = Field(validation_alias='Labelling')
    scanning: str | Sequence[str] = Field(validation_alias='Scanning')
    qc: str | Sequence[str] = Field(validation_alias='QC')


class PathDefinition(BaseModel):
    """Defines a direct path between two doors, with a travel duration."""
    path: tuple[str, str]
    duration_seconds: float


class RunnerExtraDurations(BaseModel):
    """Defines runner durations independent of the travel distance,
    i.e. loading and unloading times."""
    loading_time: float | str = Field(validation_alias='Loading time (per batch)')
    unloading_time: float | str = Field(validation_alias='Unloading time (per batch)')


class RunnerConfig(BaseModel):
    """Configuration dataclass for runner-related parameters."""
    door_map: ProcessDoorMap
    runner_speed: float
    cutup_dist: Sequence[float]
    extra_paths: Sequence[PathDefinition]
    extra_durations: RunnerExtraDurations

    @staticmethod
    def from_excel(wbook: Workbook) -> Self:
        """Generate a `RunnerConfig` from an Excel file.

        Args:
            wbook (Workbook): The Excel file to parse.

        Returns:
            RunnerConfig: the parsed `RunnerConfig`.
        """
        t = excel.get_table(
            wbook, 'Runner Times', 'tableProcessStageDoors'
        )
        door_map = {
            k: (
                v['doors'].split(' ') if ' ' in v['doors'] else v['doors']
            ) for k, v in (
                pd.DataFrame(t[1:], columns=t[0])
                .set_index('stage')
                .to_dict('index')
            ).items()
        }

        runner_speed = excel.get_name(wbook, 'runnerSpeed')

        print(excel.get_name(wbook, 'runnerCutupDist'))
        cutup_dist = [v[0] for v in excel.get_name(wbook, 'runnerCutupDist')]  # flatten

        t = excel.get_table(
            wbook, 'Runner Times', 'tableAdditionalPaths'
        )
        extra_paths = [
            {
                'path': v['path'].split(' '),
                'duration_seconds': float(v['seconds'])
            }
            for v in dict(
                pd.DataFrame(t[1:], columns=t[0])
                .set_index('path_name')
                .to_dict('index')
            ).values()
        ]

        t = excel.get_table(
            wbook, 'Runner Times', 'tableExtraTasks'
        )
        extra_durations = {
            k: float(v['seconds'])
            for k, v in (
                pd.DataFrame(t[1:], columns=t[0])
                .set_index('runner_task')
                .to_dict('index')
            ).items()
        }

        return RunnerConfig(
            door_map=door_map,
            runner_speed=runner_speed,
            cutup_dist=cutup_dist,
            extra_paths=extra_paths,
            extra_durations=extra_durations
        )


class RunnerTimesConfig(BaseModel):
    """Configuration dataclass containing runner times between process stages."""

    reception_cutup: NonNegativeFloat = Field(alias='(reception, cutup)')
    cutup_processing: NonNegativeFloat = Field(alias='(cutup, processing)')
    processing_microtomy: NonNegativeFloat = Field(alias='(processing, microtomy)')
    microtomy_staining: NonNegativeFloat = Field(alias='(microtomy, staining)')
    staining_labelling: NonNegativeFloat = Field(alias='(staining, labelling)')
    labelling_scanning: NonNegativeFloat = Field(alias='(labelling, scanning)')
    scanning_qc: NonNegativeFloat = Field(alias='(scanning, qc)')

    extra_loading: NonNegativeFloat
    extra_unloading: NonNegativeFloat

    @staticmethod
    def from_workbook(wbook: Workbook, speed: float | None = None) -> 'RunnerTimesConfig':
        """Construct a dataclass instance from an Excel workbook.

        Args:
            wbook (Workbook): The Excel workbook to parse.

        Returns:
            RunnerTimesConfig: The parsed dataclass instance.
        """
        if speed is None:
            speed = excel.get_name(wbook, 'runnerSpeed')
        df = pd.DataFrame(
            (
                table := excel.get_table(wbook, 'Runner Times output', 'tableRunnerDistances')
            )[1:],
            columns=table[0]
        ).set_index('runner_journey')

        times = dict(df.to_records())
        return RunnerTimesConfig(
            **times,
            extra_loading=excel.get_name(wbook, 'runnerLoadingTime'),
            extra_unloading=excel.get_name(wbook, 'runnerUnloadingTime'),
        )
