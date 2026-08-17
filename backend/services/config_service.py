"""Configuration service: loads and manages YAML configs."""
import os
from typing import Any, Dict, Optional
from ai_engine.common.utils import load_yaml_config, get_project_root


class ConfigService:
    """Centralized configuration management."""

    def __init__(self):
        self._project_root = get_project_root()
        self._configs_dir = os.path.join(self._project_root, "configs")
        self._app_config: Optional[Dict[str, Any]] = None

    @property
    def app_config(self) -> Dict[str, Any]:
        """Load and cache app_config.yaml."""
        if self._app_config is None:
            path = os.path.join(self._configs_dir, "app_config.yaml")
            self._app_config = load_yaml_config(path)
        return self._app_config

    def get_sport_config(self, sport_name: str) -> Dict[str, Any]:
        """Load sport-specific config from configs/<sport>.yaml."""
        path = os.path.join(self._configs_dir, f"{sport_name}.yaml")
        config = load_yaml_config(path)

        # Also check sports/<sport>/config.yaml as fallback
        if not config:
            alt_path = os.path.join(self._project_root, "sports", sport_name, "config.yaml")
            config = load_yaml_config(alt_path)

        return config

    @property
    def upload_dir(self) -> str:
        """Get upload directory path."""
        rel_dir = self.app_config.get("upload", {}).get("upload_dir", "data/raw")
        return os.path.join(self._project_root, rel_dir)

    @property
    def output_dir(self) -> str:
        """Get output directory path."""
        rel_dir = self.app_config.get("upload", {}).get("output_dir", "data/outputs")
        return os.path.join(self._project_root, rel_dir)

    @property
    def max_file_size_mb(self) -> int:
        """Get max upload file size in MB."""
        return self.app_config.get("upload", {}).get("max_file_size_mb", 500)

    @property
    def allowed_extensions(self) -> list:
        """Get allowed video file extensions."""
        return self.app_config.get("upload", {}).get(
            "allowed_extensions", [".mp4", ".avi", ".mov", ".mkv", ".webm"]
        )


# Singleton instance
config_service = ConfigService()
