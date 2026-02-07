"""Ingredient profile data model."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class IngredientProfile:
    """Nutritional and technical profile of a pastry ingredient.

    All _pct fields represent percentage per 100g of ingredient.
    The sum of all component percentages should equal ~100%.
    """

    id: str
    name: str
    group: str = ""

    # Component percentages (must sum to ~100%)
    sugar_pct: float = 0.0
    oil_pct: float = 0.0          # Vegetable fat / oil
    butter_fat_pct: float = 0.0   # Dairy fat (butter/cream)
    cocoa_butter_pct: float = 0.0 # Cocoa butter
    cocoa_pct: float = 0.0        # Cocoa solids (non-fat)
    amp_pct: float = 0.0          # Milk proteins (MSNF)
    lactose_pct: float = 0.0      # Lactose
    other_solids_pct: float = 0.0 # Other solids
    water_pct: float = 0.0        # Water
    alcohol_pct: float = 0.0      # Alcohol

    # Derived / technical properties
    pod: float = 0.0              # Sweetening power (relative, sucrose = 100)
    pac: float = 0.0              # Anti-freezing power
    kcal_per_100g: float = 0.0    # Kilocalories per 100g

    # Cost
    cost_per_kg: float = 0.0      # EUR per kilogram

    @property
    def component_sum(self) -> float:
        """Sum of all component percentages. Should be ~100%."""
        return (
            self.sugar_pct
            + self.oil_pct
            + self.butter_fat_pct
            + self.cocoa_butter_pct
            + self.cocoa_pct
            + self.amp_pct
            + self.lactose_pct
            + self.other_solids_pct
            + self.water_pct
            + self.alcohol_pct
        )

    @property
    def total_fat_pct(self) -> float:
        """Total fat percentage (oil + butter fat + cocoa butter)."""
        return self.oil_pct + self.butter_fat_pct + self.cocoa_butter_pct

    @property
    def total_dry_matter_pct(self) -> float:
        """Total dry matter (cocoa + amp + lactose + other solids)."""
        return self.cocoa_pct + self.amp_pct + self.lactose_pct + self.other_solids_pct

    @property
    def total_liquid_pct(self) -> float:
        """Total liquid percentage (water + alcohol)."""
        return self.water_pct + self.alcohol_pct

    def is_valid(self) -> bool:
        """Check if the ingredient profile is valid (components sum to ~100%)."""
        return abs(self.component_sum - 100.0) < 1.5  # Allow small rounding tolerance

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> IngredientProfile:
        """Deserialize from dictionary."""
        # Only pass known fields to avoid errors from extra keys
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

    def __str__(self) -> str:
        return f"{self.name} ({self.group})"
