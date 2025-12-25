"""CDBAI Agent Package"""
from .pipeline import cdbai_chat

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("cdbai")
except PackageNotFoundError:
    __version__ = "0.0.x"

__version__ = 0
__all__ = ["cdbai_chat"]
