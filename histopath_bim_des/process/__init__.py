"""Definitions for Histopathology processes."""

from . import (p10_reception, p20_cutup, p30_processing, p40_microtomy,
               p50_staining, p60_labelling, p70_scanning, p80_qc,
               p90_reporting)
from .core import (ArrivalGenerator, BaseProcess, BatchingProcess,
                       CollationProcess, DeliveryProcess, Process,
                       ResourceScheduler, RunnerDurations, register_process)
