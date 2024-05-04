"""Global variable configuration module for the histopath simulation model"""
from annotated_types import Annotated, Ge, Le
from openpyxl import Workbook
import pydantic as pyd

from .. import excel
from .distributions import IntDistributionInfo

Probability = Annotated[float, Ge(0), Le(1)]


class Globals(pyd.BaseModel):
    """Stores the global variables of a model.

    Field titles should match the corresponding named range in the Excel input file
    and therefore should not contain any spaces or symbols."""

    prob_internal: Probability = pyd.Field(title='ProbInternal')
    """Probability that a specimen comes from an internal source, i.e. one that uses the
    EPIC system."""

    prob_urgent_cancer: Probability = pyd.Field(title='ProbUrgentCancer')
    """Probability that a cancer-pathway specimen has Urgent priority."""

    prob_urgent_non_cancer: Probability = pyd.Field(title='ProbUrgentNonCancer')
    """Probability that a non-cancer-pathway specimen has Urgent priority."""

    prob_priority_cancer: Probability = pyd.Field(title='ProbPriorityCancer')
    """Probability that a cancer-pathway specimen has Priority priority."""

    prob_priority_non_cancer: Probability = pyd.Field(title='ProbPriorityNonCancer')
    """Probability that a non-cancer-pathway specimen has Priority priority."""

    prob_prebook: Probability = pyd.Field(title='ProbPrebook')
    """Probability that a specimen requires pre-booking-in investigation."""

    prob_invest_easy: Probability = pyd.Field(title='ProbInvestEasy')
    """Probability that an internal specimen requires booking-in investigation, and
    the investigation is classified as "easy"."""

    prob_invest_hard: Probability = pyd.Field(title='ProbInvestHard')
    """Probability that an internal specimen requires booking-in investigation, and
    the investigation is classified as "hard"."""

    prob_invest_external: Probability = pyd.Field(title='ProbInvestExternal')
    """Probability that an external specimen requires booking-in investigation."""

    prob_bms_cutup: Probability = pyd.Field(title='ProbBMSCutup')
    """Probability that a non-urgent specimen goes to BMS cut-up."""

    prob_bms_cutup_urgent: Probability = pyd.Field(title='ProbBMSCutupUrgent')
    """Probability that an urgent specimen goes to BMS cut-up."""

    prob_large_cutup: Probability = pyd.Field(title='ProbLargeCutup')
    """Probability that a non-urgent specimen goes to large specimens cut-up."""

    prob_large_cutup_urgent: Probability = pyd.Field(title='ProbLargeCutupUrgent')
    """Probability that an urgent specimen goes to large specimens cut-up."""

    prob_pool_cutup: Probability = pyd.Field(title='ProbPoolCutup')
    """Probability that a non-urgent specimen goes to Pool cut-up."""

    prob_pool_cutup_urgent: Probability = pyd.Field(title='ProbPoolCutupUrgent')
    """Probability that an urgent specimen goes to Pool cut-up."""

    prob_mega_blocks: Probability = pyd.Field(title='ProbMegaBlocks')
    """Probability that a large specimen cut-up produces mega blocks. With the remaining
    probability, large surgical blocks are produced instead."""

    prob_decalc_bone: Probability = pyd.Field(title='ProbDecalcBone')
    """Probability that an specimen requires decalcification at a bone station."""

    prob_decalc_oven: Probability = pyd.Field(title='ProbDecalcOven')
    """Probability that an specimen requires decalcification in a decalc oven."""

    prob_microtomy_levels: Probability = pyd.Field(title='ProbMicrotomyLevels')
    """Probability that a small surgical block produces a "levels" microtomy task.
    With remaining probability, a "serials" microtomy task is produced."""

    num_blocks_large_surgical: IntDistributionInfo = pyd.Field(title='NumBlocksLargeSurgical')
    """Parameters for the number of large surgical blocks produced in a cut-up that produces
    such blocks."""

    num_blocks_mega: IntDistributionInfo = pyd.Field(title='NumBlocksMega')
    """Parameters for the number of mega blocks produced in a cut-up that produces such blocks."""

    num_slides_larges: IntDistributionInfo = pyd.Field(title='NumSlidesLarges')
    """Parameters for the number of slides produced for a large surgical microtomy task."""

    num_slides_levels: IntDistributionInfo = pyd.Field(title='NumSlidesLarges')
    """Parameters for the number of slides produced for a levels microtomy task."""

    num_slides_megas: IntDistributionInfo = pyd.Field(title='NumSlidesLarges')
    """Parameters for the number of slides produced for a megas microtomy task."""

    num_slides_serials: IntDistributionInfo = pyd.Field(title='NumSlidesLarges')
    """Parameters for the number of slides produced for a serials microtomy task."""

    @staticmethod
    def from_workbook(wbook: Workbook) -> 'Globals':
        """Construct a dataclass instance from an Excel workbook.

        Args:
            wbook: The Excel workbook to parse.

        Returns:
            The parsed dataclass instance.
        """
        globals_floats = {
            key: excel.get_name(wbook, field.title) for key, field in Globals.model_fields.items()
            if field.annotation == float
        }
        globals_dists = {
            key: IntDistributionInfo(
                type=excel.get_name(wbook, field.title)[0][0],
                low=excel.get_name(wbook, field.title)[0][1],
                mode=excel.get_name(wbook, field.title)[0][2],
                high=excel.get_name(wbook, field.title)[0][3]
            )
            for key, field in Globals.model_fields.items()
            if field.annotation == IntDistributionInfo
        }
        return Globals(**globals_floats, **globals_dists)
