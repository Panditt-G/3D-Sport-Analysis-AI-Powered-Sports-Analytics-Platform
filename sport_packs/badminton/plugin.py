"""
Badminton Sport Pack Plugin.
============================
Integrates Badminton movement recognition, reference dataset, and
rules into the shared sport pack registry.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import json

from ai_engine.vision.pose.base_pose import PoseFrame
from sport_packs.badminton.movements.overhead_clear import OverheadClearAnalyzer


class BadmintonSportPack:
    """Sport Pack implementation for Badminton."""

    def __init__(self, pack_dir: Optional[Path] = None):
        self.pack_dir = pack_dir or Path(__file__).resolve().parent
        self.manifest = self._load_manifest()
        self.references = self._load_references()
        self.rules = self._load_rules()
        self.overhead_clear_analyzer = OverheadClearAnalyzer()

    def _load_manifest(self) -> Dict[str, Any]:
        manifest_path = self.pack_dir / "pack.yaml"
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _load_references(self) -> Dict[str, Any]:
        ref_path = self.pack_dir / "references" / "overhead_clear_ref.json"
        if ref_path.exists():
            with open(ref_path, "r", encoding="utf-8") as f:
                return {"overhead_clear": json.load(f)}
        return {}

    def _load_rules(self) -> List[Dict[str, Any]]:
        rule_path = self.pack_dir / "rules" / "overhead_clear_rules.yaml"
        if rule_path.exists():
            with open(rule_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return data.get("rules", [])
        return []

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": "badminton",
            "display_name": self.manifest.get("display_name", "Badminton"),
            "version": self.manifest.get("version", "1.0.0"),
            "supported_movements": list(self.manifest.get("supported_movements", {}).keys()),
            "default_pose_model": self.manifest.get("default_pose_model", "mediapipe_blazepose"),
            "supported_camera_views": self.manifest.get("supported_camera_views", []),
        }

    def analyze_sequence(
        self,
        frames: List[PoseFrame],
        movement_name: str = "overhead_clear",
    ) -> Dict[str, Any]:
        """Analyze a sequence of PoseFrames for badminton."""
        if movement_name == "overhead_clear":
            phases = self.overhead_clear_analyzer.segment_phases(frames)
            metrics = self.overhead_clear_analyzer.compute_movement_metrics(frames, phases)
            ref_data = self.references.get("overhead_clear", {})

            return {
                "sport": "badminton",
                "movement": "overhead_clear",
                "phases": phases,
                "metrics": metrics,
                "reference": ref_data,
                "rules": self.rules,
            }

        # Fallback for generic / unrecognized movement
        return {
            "sport": "badminton",
            "movement": movement_name,
            "phases": {},
            "metrics": {},
            "reference": {},
            "rules": [],
        }
