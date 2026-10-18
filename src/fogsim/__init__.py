"""MobiCare-Fog: a discrete-event simulation framework for fog-assisted smart healthcare."""

from .config import DEFAULT_CONFIG_PATH, load_config

__all__ = ["load_config", "DEFAULT_CONFIG_PATH"]
__version__ = "1.0.0"
