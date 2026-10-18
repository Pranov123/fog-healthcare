"""MobiCare-Fog: a discrete-event simulation framework for fog-assisted smart healthcare."""

from .config import DEFAULT_CONFIG_PATH, load_config
from .simulator import FogSimulation

__all__ = ["FogSimulation", "load_config", "DEFAULT_CONFIG_PATH"]
__version__ = "1.0.0"
