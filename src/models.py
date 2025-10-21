"""Data models for my AI application."""
from dataclasses import dataclass

@dataclass
class MyMainModel:
    name: str
    value: int
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Name cannot be empty")
        if self.value < 0:
            raise ValueError("Value must be positive")