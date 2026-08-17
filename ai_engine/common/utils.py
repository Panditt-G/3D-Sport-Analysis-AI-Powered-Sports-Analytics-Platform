"""Common helper functions: YAML config loaders, geometry tools, file utilities."""
import os
import math
import yaml
from typing import Any, Dict, Optional, Tuple, Union


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file and return as dictionary.

    Args:
        config_path: Absolute or relative path to .yaml file.

    Returns:
        Dictionary with parsed config. Empty dict if file not found.
    """
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def load_sport_config(sport_name: str, configs_dir: str = "configs") -> Dict[str, Any]:
    """
    Load sport-specific YAML config by sport name.

    Args:
        sport_name: Name of the sport (e.g. "cricket").
        configs_dir: Directory containing config files.

    Returns:
        Sport config dictionary.
    """
    config_path = os.path.join(configs_dir, f"{sport_name}.yaml")
    return load_yaml_config(config_path)


def euclidean_distance(
    p1: Union[Tuple[float, float], Dict[str, float]],
    p2: Union[Tuple[float, float], Dict[str, float]],
) -> float:
    """
    Calculate 2D Euclidean distance between two points.

    Args:
        p1, p2: Points as (x, y) tuples or dicts with 'x', 'y' keys.

    Returns:
        Distance as float.
    """
    x1, y1 = _extract_xy(p1)
    x2, y2 = _extract_xy(p2)
    return math.hypot(x2 - x1, y2 - y1)


def midpoint(
    p1: Union[Tuple[float, float], Dict[str, float]],
    p2: Union[Tuple[float, float], Dict[str, float]],
) -> Tuple[float, float]:
    """
    Calculate midpoint between two 2D points.

    Returns:
        (mid_x, mid_y) tuple.
    """
    x1, y1 = _extract_xy(p1)
    x2, y2 = _extract_xy(p2)
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def _extract_xy(point) -> Tuple[float, float]:
    """Extract (x, y) from tuple, list, or dict."""
    if isinstance(point, dict):
        return float(point.get("x", 0)), float(point.get("y", 0))
    elif isinstance(point, (list, tuple)) and len(point) >= 2:
        return float(point[0]), float(point[1])
    return 0.0, 0.0


def ensure_directory(dir_path: str) -> str:
    """Create directory if it doesn't exist. Returns the path."""
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def get_project_root() -> str:
    """Get the project root directory path."""
    # Go up from ai_engine/common/ to project root
    current = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current, "..", ".."))
