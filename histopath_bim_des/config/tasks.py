"""Task configuration module for the histopath simulation model."""
import pandas as pd
import pydantic as pyd
from openpyxl import Workbook

from .. import excel
from .distributions import DistributionInfo


class TaskDurationsInfo(pyd.BaseModel):
    """Information for tracking task durations in a model.

    The field titles in this class **MUST** match the rows of the Excel input file
    ("Task Durations" tab)."""

    receive_and_sort: DistributionInfo = pyd.Field(title='Receive and sort')
    """Time for reception to receive a new specimen and assign a priority value."""

    pre_booking_in_investigation: DistributionInfo = pyd.Field(title='Pre-booking-in investigation')
    """Time to conduct a pre-booking-in investigation, if required."""

    booking_in_internal: DistributionInfo = pyd.Field(title='Booking-in (internal)')
    """Time to book in the specimen if the specimen was received internally, i.e. it already
    exists on the EPIC sytem."""

    booking_in_external: DistributionInfo = pyd.Field(title='Booking-in (external)')
    """Time to book in the specimen if the specimen was received externally, i.e. a new entry
    must be created on EPIC."""

    booking_in_investigation_internal_easy: DistributionInfo =\
        pyd.Field(title='Booking-in investigation (internal, easy)')
    """Time to conduct a booking-in investigation for an internal specimen, if the investigation
    is classified as "easy"."""

    booking_in_investigation_internal_hard: DistributionInfo =\
        pyd.Field(title='Booking-in investigation (internal, hard)')
    """Time to conduct a booking-in investigation for an internal specimen, if the investigation
    is classified as "hard"."""

    booking_in_investigation_external: DistributionInfo =\
        pyd.Field(title='Booking-in investigation (external)')
    """Time to conduct a booking-in investigation for an external specimen."""

    cut_up_bms: DistributionInfo = pyd.Field(title='Cut-up (BMS)')
    """Time to conduct a BMS cut-up."""

    cut_up_pool: DistributionInfo = pyd.Field(title='Cut-up (pool)')
    """Time to conduct a pool cut-up."""

    cut_up_large_specimens: DistributionInfo = pyd.Field(title='Cut-up (large specimens)')
    """Time to conduct a large specimens cut-up."""

    load_bone_station: DistributionInfo = pyd.Field(title='Load bone station')
    """Time to load a batch of blocks into a bone station."""

    decalc: DistributionInfo = pyd.Field(title='Decalc')
    """Time to decalcify a bony specimen."""

    unload_bone_station: DistributionInfo = pyd.Field(title='Unload bone station')
    """Time to unload a batch of blocks into a bone station."""

    load_into_decalc_oven: DistributionInfo = pyd.Field(title='Load into decalc oven')
    """Time to load a single block into a bone station."""

    unload_from_decalc_oven: DistributionInfo = pyd.Field(title='Unload from decalc oven')
    """Time to unload a single block into a bone station."""

    load_processing_machine: DistributionInfo = pyd.Field(title='Load processing machine')
    """Time to load a batch of blocks into a processing machine."""

    unload_processing_machine: DistributionInfo = pyd.Field(title='Unload processing machine')
    """Time to unload a batch of blocks from a processing machine."""

    processing_urgent: DistributionInfo = pyd.Field(title='Processing machine (urgent)')
    """Programme length for the processing of urgent blocks."""

    processing_small_surgicals: DistributionInfo =\
        pyd.Field(title='Processing machine (small surgicals)')
    """Programme length for the processing of small surgical blocks."""

    processing_large_surgicals: DistributionInfo =\
        pyd.Field(title='Processing machine (large surgicals)')
    """Programme length for the processing of large surgical blocks."""

    processing_megas: DistributionInfo = pyd.Field(title='Processing machine (megas)')
    """Programme length for the processing of mega blocks."""

    embedding: DistributionInfo = pyd.Field(title='Embedding')
    """Time to embed a block in paraffin wax (staffed)."""

    embedding_cooldown: DistributionInfo = pyd.Field(title='Embedding (cooldown)')
    """Time for a wax block to cool (unstaffed)."""

    block_trimming: DistributionInfo = pyd.Field(title='Block trimming')
    """Time to trim excess wax from the edges of a block."""

    microtomy_serials: DistributionInfo = pyd.Field(title='Microtomy (serials)')
    """Time to produce serial slides from a block."""

    microtomy_levels: DistributionInfo = pyd.Field(title='Microtomy (levels)')
    """Time to produce level slides from a block."""

    microtomy_larges: DistributionInfo = pyd.Field(title='Microtomy (larges)')
    """"Time to produce large-section slides from a block. These are regular-sized slides,
    but with larger tissue sections."""

    microtomy_megas: DistributionInfo = pyd.Field(title='Microtomy (megas)')
    """Time to produce mega slides from a mega block."""

    load_staining_machine_regular: DistributionInfo =\
        pyd.Field(title='Load staining machine (regular)')
    """Time to load a batch of regular-sized slides into a staining machine."""

    load_staining_machine_megas: DistributionInfo =\
        pyd.Field(title='Load staining machine (megas)')
    """Time to load a batch of mega slides into a staining machine."""

    staining_regular: DistributionInfo = pyd.Field(title='Staining (regular)')
    """Time to stain a batch of regular slides."""

    staining_megas: DistributionInfo = pyd.Field(title='Staining (megas)')
    """Time to stain a batch of mega slides."""

    unload_staining_machine_regular: DistributionInfo =\
        pyd.Field(title='Unload staining machine (regular)')
    """Time to unload a batch of regular slides from a staining machine."""

    unload_staining_machine_megas: DistributionInfo =\
        pyd.Field(title='Unload staining machine (megas)')
    """Time to unload a batch of mega slides from a staining machine."""

    load_coverslip_machine_regular: DistributionInfo =\
        pyd.Field(title='Load coverslip machine (regular)')
    """Time to load a batch of regular slides into a coverslip machine."""

    coverslip_regular: DistributionInfo = pyd.Field(title='Coverslipping (regular)')
    """Time to affix coverslips to a batch of regular slides."""

    coverslip_megas: DistributionInfo = pyd.Field(title='Coverslipping (megas)')
    """Time to affix a coverslip to a mega slide (manual task)."""

    unload_coverslip_machine_regular: DistributionInfo =\
        pyd.Field(title='Unload coverslip machine (regular)')
    """Time to unload a batch of regular slides into a coverslip machine."""

    labelling: DistributionInfo = pyd.Field(title='Labelling')
    """Time to label a slide."""

    load_scanning_machine_regular: DistributionInfo =\
        pyd.Field(title='Load scanning machine (regular)')
    """Time to load a batch of regular slides into a scanning machine."""

    load_scanning_machine_megas: DistributionInfo =\
        pyd.Field(title='Load scanning machine (megas)')
    """Time to load a batch of mega slides into a scanning machine. There are dedicated scanning
    machines for mega slides."""

    scanning_regular: DistributionInfo = pyd.Field(title='Scanning (regular)')
    """Time to scan a batch of regular slides."""

    scanning_megas: DistributionInfo = pyd.Field(title='Scanning (megas)')
    """Time to scan a batch of mega slides."""

    unload_scanning_machine_regular: DistributionInfo =\
        pyd.Field(title='Unload scanning machine (regular)')
    """Time to unload a batch of regular slides from a scanning machine."""

    unload_scanning_machine_megas: DistributionInfo =\
        pyd.Field(title='Unload scanning machine (megas)')
    """Time to unload a batch of mega slides from a scanning machine."""

    block_and_quality_check: DistributionInfo = pyd.Field(title='Block and quality check')
    """Time to perform the block and quality checks for a specimen."""

    assign_histopathologist: DistributionInfo = pyd.Field(title='Assign histopathologist')
    """Time to assign a histopathologist to a specimen."""

    write_report: DistributionInfo = pyd.Field(title='Write histopathological report')
    """Time to write the histopathological report for a specimen."""

    @staticmethod
    def from_workbook(wbook: Workbook) -> 'TaskDurationsInfo':
        """Construct a dataclass instance from an Excel workbook.

        Args:
            wbook: The Excel workbook to parse.

        Returns:
            The parsed dataclass instance.
        """
        tasks_df = pd.DataFrame(
            (
                table := excel.get_table(wbook, 'Task Durations', 'TaskDurations')
            )[1:],
            columns=table[0]
        ).set_index('Task')
        return TaskDurationsInfo.model_validate({
            key: DistributionInfo(
                type=tasks_df.loc[field.title, 'Distribution'],
                low=tasks_df.loc[field.title, 'Optimistic'],
                mode=tasks_df.loc[field.title, 'Most Likely'],
                high=tasks_df.loc[field.title, 'Pessimistic'],
                time_unit=tasks_df.loc[field.title, 'Units'],
            )
            for key, field in TaskDurationsInfo.model_fields.items()
        })
