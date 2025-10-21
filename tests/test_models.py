"""Tests for data models."""
import pytest
from src.models import MyMainModel

def test_create_my_model():
    """Test creating the main model."""
    model = MyMainModel(name="test", value=42)
    assert model.name == "test"
    assert model.value == 42

def test_model_validation():
    """Test that model validates input."""
    with pytest.raises(ValueError):
        MyMainModel(name="", value=-1)