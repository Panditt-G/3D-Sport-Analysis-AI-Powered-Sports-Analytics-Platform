"""Dynamic Sport & Model Registry for seamless multi-sport extensibility."""
from typing import Any, Callable, Dict, Type, Optional, List
from ai_engine.base.base_pipeline import BaseSportPipeline
from ai_engine.base.base_analytics import BaseSportAnalytics

# Sport metadata: description, icon, supported metrics
# Pre-configured metadata for running pipeline
SPORT_METADATA = {
    "running": {
        "display_name": "Running",
        "description": "Gait analysis, stride detection, speed tracking, joint kinematics",
        "icon": "🏃",
        "metrics": ["total_distance_m", "avg_speed_kmh", "avg_cadence_spm", "stride_length_m", "gait_symmetry"],
    },
}


class SportRegistry:
    """Central registry to dynamically discover and instantiate sport pipelines."""
    _pipelines: Dict[str, Type[BaseSportPipeline]] = {}
    _analytics: Dict[str, Type[BaseSportAnalytics]] = {}

    @classmethod
    def register_pipeline(cls, sport_name: str):
        def decorator(subclass: Type[BaseSportPipeline]):
            cls._pipelines[sport_name.lower()] = subclass
            return subclass
        return decorator

    @classmethod
    def register_analytics(cls, sport_name: str):
        def decorator(subclass: Type[BaseSportAnalytics]):
            cls._analytics[sport_name.lower()] = subclass
            return subclass
        return decorator

    @classmethod
    def get_pipeline(cls, sport_name: str, config: Optional[Dict[str, Any]] = None) -> BaseSportPipeline:
        sport_name = sport_name.lower()
        if sport_name not in cls._pipelines:
            raise ValueError(f"Sport '{sport_name}' is not registered. Available: {cls.available_sports()}")
        return cls._pipelines[sport_name](config=config)

    @classmethod
    def get_analytics(cls, sport_name: str, config: Optional[Dict[str, Any]] = None) -> BaseSportAnalytics:
        sport_name = sport_name.lower()
        if sport_name not in cls._analytics:
            raise ValueError(f"Analytics for '{sport_name}' not registered. Available: {cls.available_sports()}")
        return cls._analytics[sport_name](config=config)

    @classmethod
    def available_sports(cls) -> List[str]:
        """Return list of all registered sport names."""
        return list(cls._pipelines.keys())

    @classmethod
    def get_sport_info(cls, sport_name: str) -> Dict[str, Any]:
        """
        Get detailed info about a registered sport.

        Returns dict with: name, display_name, description, icon, metrics,
        has_pipeline, has_analytics.
        """
        sport_name = sport_name.lower()
        meta = SPORT_METADATA.get(sport_name, {})

        return {
            "name": sport_name,
            "display_name": meta.get("display_name", sport_name.title()),
            "description": meta.get("description", f"{sport_name.title()} AI analysis"),
            "icon": meta.get("icon", "🏅"),
            "metrics": meta.get("metrics", []),
            "has_pipeline": sport_name in cls._pipelines,
            "has_analytics": sport_name in cls._analytics,
        }

    @classmethod
    def get_all_sports_info(cls) -> List[Dict[str, Any]]:
        """Get info for all registered sports."""
        return [cls.get_sport_info(name) for name in cls.available_sports()]

    @classmethod
    def is_registered(cls, sport_name: str) -> bool:
        """Check if a sport is registered."""
        return sport_name.lower() in cls._pipelines


def register_sport(sport_name: str):
    """Decorator to register a sport pipeline."""
    return SportRegistry.register_pipeline(sport_name)
