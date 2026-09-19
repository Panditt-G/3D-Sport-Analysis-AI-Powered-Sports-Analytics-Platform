"""Test dynamic registration of sport pipelines and analytics."""
import pytest
from ai_engine.registry import SportRegistry
import sports

def test_available_sports():
    available = SportRegistry.available_sports()
    assert "running" in available
    assert len(available) >= 1

def test_get_running_pipeline():
    pipeline = SportRegistry.get_pipeline("running")
    assert pipeline is not None

def test_get_running_analytics():
    analytics = SportRegistry.get_analytics("running")
    assert analytics is not None
