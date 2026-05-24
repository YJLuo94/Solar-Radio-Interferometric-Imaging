"""Shared helpers for the solar radio processing workflow.

The scripts in this repository are intended to run inside CASA.  CASA tasks are
obtained either from the CASA 6 ``casatasks`` package or, as a fallback, from the
``__main__`` namespace used by older ``execfile``-style CASA sessions.
"""

from __future__ import annotations

import importlib
import os
import shutil
import sys
from pathlib import Path
from typing import Iterable, Optional


def add_extra_python_paths(paths: Iterable[str]) -> None:
    """Append external software paths used by legacy CASA scripts."""
    for path in paths:
        if path and path not in sys.path:
            sys.path.append(path)


def get_casa_task(name: str):
    """Return a CASA task by name.

    This keeps the module code usable in both CASA 6, where tasks are available
    from ``casatasks``, and older CASA sessions where tasks may exist in the
    top-level execution namespace.
    """
    try:
        casatasks = importlib.import_module("casatasks")
        return getattr(casatasks, name)
    except Exception:
        import __main__

        task = getattr(__main__, name, None)
        if task is None:
            raise ImportError(
                f"CASA task '{name}' was not found. Run this workflow inside CASA "
                "or make sure casatasks is importable."
            )
        return task


def get_msmetadata_tool():
    """Return a CASA msmetadata tool instance."""
    try:
        from casatools import msmetadata

        return msmetadata()
    except Exception:
        import __main__

        msmd = getattr(__main__, "msmd", None)
        if msmd is None:
            raise ImportError(
                "CASA msmetadata tool was not found. Run this workflow inside CASA."
            )
        return msmd


def get_image_tool():
    """Return a CASA image tool instance."""
    try:
        from casatools import image

        return image()
    except Exception:
        import __main__

        ia = getattr(__main__, "ia", None)
        if ia is None:
            raise ImportError("CASA image tool was not found. Run this workflow inside CASA.")
        return ia


def ensure_dir(path: str | Path) -> Path:
    """Create a directory if needed and return it as a ``Path``."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_clean_dir(path: str | Path) -> Path:
    """Remove and recreate a directory.

    The original one-file script removed ``cal/``, ``qlimg/``, and ``sciimg/``
    before regenerating products.  This helper preserves that behavior.
    """
    path = Path(path)
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def init_log(logfile: str | Path) -> None:
    """Initialize the pipeline log file."""
    Path(logfile).write_text("This is the Log file.\n", encoding="utf-8")


def append_log(logfile: str | Path, message: str) -> None:
    """Append a formatted message to the pipeline log."""
    with open(logfile, "a", encoding="utf-8") as file:
        file.write("###################\n")
        file.write(message.rstrip() + "\n")


def setup_workdir(workfolder: str | Path) -> Path:
    """Create and change into the working directory."""
    workfolder = ensure_dir(workfolder)
    os.chdir(workfolder)
    return workfolder
