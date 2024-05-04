"""Batching configuration module for the histopath simulation model."""
import pandas as pd
import pydantic as pyd
from openpyxl import Workbook

from .. import excel


class BatchSizes(pyd.BaseModel):
    """Information for tracking batch sizes in a model.  This is the number of
    specimens, blocks, or slides in a machine or delivery batch.  Batches in the model
    are homogeneous, i.e. all items in a batch are of the same type.

    The field titles in this class MUST match the rows of the Excel input file
    ("Batch Sizes" tab)."""

    deliver_reception_to_cut_up: pyd.PositiveInt =\
        pyd.Field(title='Delivery (reception to cut-up)')
    """Delivery batch size, reception to cut-up (specimens)."""

    deliver_cut_up_to_processing: pyd.PositiveInt =\
        pyd.Field(title='Delivery (cut-up to processing)')
    """Delivery batch size, cut-up to processing (specimens)."""

    deliver_processing_to_microtomy: pyd.PositiveInt =\
        pyd.Field(title='Delivery (processing to microtomy)')
    """Delivery batch size, processing to microtomy (specimens)."""

    deliver_microtomy_to_staining: pyd.PositiveInt =\
        pyd.Field(title='Delivery (microtomy to staining)')
    """Delivery batch size, microtomy to staining (specimens)."""

    deliver_staining_to_labelling: pyd.PositiveInt =\
        pyd.Field(title='Delivery (staining to labelling)')
    """Delivery batch size, staining to labelling (specimens)."""

    deliver_labelling_to_scanning: pyd.PositiveInt =\
        pyd.Field(title='Delivery (labelling to scanning)')
    """Delivery batch size, labelling to scanning (specimens)."""

    deliver_scanning_to_qc: pyd.PositiveInt = pyd.Field(title='Delivery (scanning to QC)')
    """Delivery batch size, scanning to QC (specimens)."""

    bone_station: pyd.PositiveInt = pyd.Field(title='Bone station (blocks)')
    """Bone station (machine) batch size (blocks)."""

    processing_regular: pyd.PositiveInt =\
        pyd.Field(title='Processing machine (regular blocks)')
    """Processing machine batch size, regular blocks."""

    processing_megas: pyd.PositiveInt = pyd.Field(title='Processing machine (mega blocks)')
    """Processing machine batch size, mega blocks."""

    staining_regular: pyd.PositiveInt = pyd.Field(title='Staining (regular slides)')
    """Staining machine batch size, regular slides."""

    staining_megas: pyd.PositiveInt = pyd.Field(title='Staining (mega slides)')
    """Staining machine batch size, mega slides."""

    digital_scanning_regular: pyd.PositiveInt = pyd.Field(title='Scanning (regular slides)')
    """Scanning machine batch size, regular slides."""

    digital_scanning_megas: pyd.PositiveInt = pyd.Field(title='Scanning (mega slides)')
    """Scanning machine batch size, mega slides."""

    @staticmethod
    def from_workbook(wbook: Workbook) -> 'BatchSizes':
        """Construct a dataclass instance from an Excel workbook.

        Args:
            wbook: The Excel workbook to parse.

        Returns:
            The parsed dataclass instance.
        """
        batch_sizes_df = pd.DataFrame(
            (
                table := excel.get_table(wbook, 'Batch Sizes', 'BatchSizes')
            )[1:],
            columns=table[0]
        ).set_index('Batch Name')
        return BatchSizes.model_validate({
            key: batch_sizes_df.loc[field.title, 'Size']
            for key, field in BatchSizes.model_fields.items()
        })
