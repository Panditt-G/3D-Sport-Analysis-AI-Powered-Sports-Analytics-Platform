"""Dynamic Sport & Model Registry for seamless multi-sport extensibility."""
from typing import Any, Callable, Dict, Type, Optional
from ai_engine.base.base_pipeline import BaseSportPipeline
from ai_engine.base.base_analytics import BaseSportAnalytics

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
    def available_sports(cls):
        return list(cls._pipelines.keys())

def register_sport(sport_name: str):
    """Decorator to register a sport pipeline."""
    return SportRegistry.register_pipeline(sport_name)
