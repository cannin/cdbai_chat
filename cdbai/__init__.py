"""CDBAI BigQuery agent package."""
from .pipeline import cdbai_chat

import tomllib
from pathlib import Path


def _load_version():
    # Locate pyproject.toml relative to this file
    base_dir = Path(__file__).parent.parent
    pyproject = base_dir / "pyproject.toml"

    # Parse TOML and extract version
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)

    # Support both [project] and [tool.poetry] layouts
    if "project" in data and "version" in data["project"]:
        return data["project"]["version"]
    raise KeyError("version not found in pyproject.toml")


__version__ = _load_version()


__all__ = ["cdbai_chat"]
