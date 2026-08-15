"""Validates sport modules and ensures compliance with BaseSportPipeline & BaseSportAnalytics."""
import inspect
from typing import Type
from ai_engine.base.base_pipeline import BaseSportPipeline
from ai_engine.base.base_analytics import BaseSportAnalytics
from .validation_result import ValidationResult

class SportValidator:
    @staticmethod
    def validate_sport_module(sport_name: str, pipeline_cls: Type, analytics_cls: Type) -> ValidationResult:
        errors = []
        warnings = []

        if not issubclass(pipeline_cls, BaseSportPipeline):
            errors.append(f"{pipeline_cls.__name__} must inherit from BaseSportPipeline")

        if not issubclass(analytics_cls, BaseSportAnalytics):
            errors.append(f"{analytics_cls.__name__} must inherit from BaseSportAnalytics")

        return ValidationResult(
            is_valid=len(errors) == 0,
            sport_name=sport_name,
            errors=errors,
            warnings=warnings
        )
