"""Data structure holding validation results."""
from dataclasses import dataclass, field
from typing import List

@dataclass
class ValidationResult:
    is_valid: bool
    sport_name: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
