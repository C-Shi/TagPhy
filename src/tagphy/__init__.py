"""TagPhy package."""

import os, sys
from pathlib import Path


def app_root() -> Path:
    if override := os.environ.get("TAGPHY_ROOT"):
        return Path(override).resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("Cannot determine TagPhy root; set TAGPHY_ROOT")
