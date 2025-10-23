"""
Legacy data models.

This module contains older data models that are being phased out
but need to remain for backward compatibility.
"""
from dataclasses import dataclass


@dataclass
class MyMainModel:
    """Legacy main model (to be deprecated)."""
    name: str
    value: int
    
    def __post_init__(self):
        """Validate model fields after initialization."""
        if not self.name:
            raise ValueError("Name cannot be empty")
        if self.value < 0:
            raise ValueError("Value must be positive")
