"""Compatibility wrapper for MS partitioning.

The actual implementation is kept in ``pre_processing.pre_calibration`` because
it is part of the initial data inspection and preparation stage.  This wrapper
is provided so users can still find the MS partitioning function under the
``ms_processing`` namespace.
"""

from pre_processing.pre_calibration import partition_ms

__all__ = ["partition_ms"]
