from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Mapping

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "default.yaml"


def deep_update(base: dict, updates: Mapping[str, Any]) -> dict:
    for key, value in updates.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), dict):
            deep_update(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base


def load_config(path: str | Path | None = None, overrides: Mapping[str, Any] | None = None) -> dict:
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    with open(config_path, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if overrides:
        deep_update(config, overrides)
    return config
