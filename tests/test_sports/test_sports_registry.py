"""Test dynamic registration of sport pipelines and analytics."""
import pytest
from ai_engine.registry import SportRegistry
import sports

def test_available_sports():
    available = SportRegistry.available_sports()
    for s in ["running", "basketball", "football", "volleyball", "cricket"]:
        assert s in available

def test_get_running_pipeline():
    pipeline = SportRegistry.get_pipeline("running")
    assert pipeline is not None
