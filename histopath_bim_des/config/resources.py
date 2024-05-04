"""Resource configuration module for the histopath simulation model."""
import typing as ty

import pandas as pd
import pydantic as pyd
from annotated_types import Annotated, Len
from openpyxl import Workbook

from .. import excel


class ResourceSchedule(pyd.BaseModel):
    """A resource allocation schedule."""

    day_flags: Annotated[ty.Sequence[bool], Len(7, 7)]
    """True/1 if resource is scheduled for the day (MON to SUN), False/0 otherwise."""

    allocation: Annotated[ty.Sequence[pyd.NonNegativeInt], Len(48, 48)]
    """Number of resource units allocated for the day (in 30-min intervals),
    if the corresponding day flag is set to 1. The list length is expected to be 48."""

    @staticmethod
    def from_pd(df: pd.DataFrame, row_name: str) -> 'ResourceSchedule':
        """Construct a resource schedule from a DataFrame row.

        Args:
            df:
                The dataframe containing the resource allocation information.
            row_name:
                The name of the resource, matching a row index in the inputted dataframe.
        """
        return __class__(
            day_flags=df.loc[row_name, 'MON':'SUN'].tolist(),
            allocation=df.loc[row_name, '00:00':'23:30'].tolist()
        )


class ResourceInfo(pyd.BaseModel):
    """Contains information about a resource."""
    name: str
    """The name of the resource, e.g. "Scanning machine"."""

    type: ty.Literal['staff', 'machine']
    """Whether the resource is a staff or machine resource."""

    schedule: ResourceSchedule
    """A schedule defining the number of allocated resource units over the course of a week."""


class ResourcesInfo(pyd.BaseModel):
    """Dataclass for tracking the staff resources of a model.

    The fields in this dataclass **MUST** match the rows of the configuration
    Excel template ("Resources" tab), with all letters to lowercase, spaces to
    underscores, and other characters removed."""

    booking_in_staff: ResourceInfo =\
        pyd.Field(title='Booking-in staff', json_schema_extra={'resource_type': 'staff'})
    bms: ResourceInfo =\
        pyd.Field(title='BMS', json_schema_extra={'resource_type': 'staff'})
    cut_up_assistant: ResourceInfo =\
        pyd.Field(title='Cut-up assistant', json_schema_extra={'resource_type': 'staff'})
    processing_room_staff: ResourceInfo =\
        pyd.Field(title='Processing room staff', json_schema_extra={'resource_type': 'staff'})
    microtomy_staff: ResourceInfo =\
        pyd.Field(title='Microtomy staff', json_schema_extra={'resource_type': 'staff'})
    staining_staff: ResourceInfo =\
        pyd.Field(title='Staining staff', json_schema_extra={'resource_type': 'staff'})
    scanning_staff: ResourceInfo =\
        pyd.Field(title='Scanning staff', json_schema_extra={'resource_type': 'staff'})
    qc_staff: ResourceInfo =\
        pyd.Field(title='QC staff', json_schema_extra={'resource_type': 'staff'})
    histopathologist: ResourceInfo =\
        pyd.Field(title='Histopathologist', json_schema_extra={'resource_type': 'staff'})
    bone_station: ResourceInfo =\
        pyd.Field(title='Bone station', json_schema_extra={'resource_type': 'machine'})
    processing_machine: ResourceInfo =\
        pyd.Field(title='Processing machine', json_schema_extra={'resource_type': 'machine'})
    staining_machine: ResourceInfo =\
        pyd.Field(title='Staining machine', json_schema_extra={'resource_type': 'machine'})
    coverslip_machine: ResourceInfo =\
        pyd.Field(title='Coverslip machine', json_schema_extra={'resource_type': 'machine'})
    scanning_machine_regular: ResourceInfo = pyd.Field(
        title='Scanning machine (regular)', json_schema_extra={'resource_type': 'machine'})
    scanning_machine_megas: ResourceInfo = pyd.Field(
        title='Scanning machine (megas)', json_schema_extra={'resource_type': 'machine'})

    @staticmethod
    def from_workbook(wbook: Workbook) -> 'ResourcesInfo':
        """Construct a dataclass instance from an Excel workbook.

        Args:
            wbook: The Excel workbook to parse.

        Returns:
            The parsed dataclass instance.
        """
        resources_df = (
            pd.DataFrame(
                (
                    table := excel.get_table(wbook, 'Resource Allocation', 'Resources')
                )[1:],
                columns=table[0]
            )
            .fillna(0.)
            .set_index('Resource')
        )
        return ResourcesInfo.model_validate({
            key: ResourceInfo(
                name=field.title,
                type=field.json_schema_extra['resource_type'],
                schedule=ResourceSchedule.from_pd(resources_df, row_name=field.title)
            )
            for key, field in ResourcesInfo.model_fields.items()
        })
