"""
Unit tests for legacy models.

This tests the old MyMainModel that exists in models.py
"""
import pytest
from src.models import MyMainModel


class TestMyMainModel:
    """Test MyMainModel legacy model."""
    
    def test_create_valid_model(self):
        """Test creating a valid MyMainModel."""
        model = MyMainModel(name="test", value=42)
        
        assert model.name == "test"
        assert model.value == 42
    
    def test_model_validates_empty_name(self):
        """Test that model rejects empty name."""
        with pytest.raises(ValueError, match="Name cannot be empty"):
            MyMainModel(name="", value=10)
    
    def test_model_validates_negative_value(self):
        """Test that model rejects negative value."""
        with pytest.raises(ValueError, match="Value must be positive"):
            MyMainModel(name="test", value=-1)
    
    def test_model_validates_both_errors(self):
        """Test that model validates both fields."""
        # Empty name is checked first
        with pytest.raises(ValueError, match="Name cannot be empty"):
            MyMainModel(name="", value=-1)
