"""Recipe category data model with ideal ranges for validation."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class RangeSpec:
    """A numeric range with min and max values."""

    min_val: float
    max_val: float

    def contains(self, value: float) -> bool:
        """Check if value is within range (inclusive)."""
        return self.min_val <= value <= self.max_val

    def is_near(self, value: float, tolerance_pct: float = 10.0) -> bool:
        """Check if value is within tolerance of the range edges."""
        span = self.max_val - self.min_val
        margin = span * tolerance_pct / 100.0
        return (self.min_val - margin) <= value <= (self.max_val + margin)

    def to_dict(self) -> dict:
        return {"min": self.min_val, "max": self.max_val}

    @classmethod
    def from_dict(cls, data: dict) -> RangeSpec:
        return cls(min_val=data["min"], max_val=data["max"])


@dataclass
class RecipeCategory:
    """A recipe category with ideal composition ranges for validation."""

    id: str
    name: str
    description: str = ""

    # Ideal ranges (percentages)
    sugar_range: Optional[RangeSpec] = None
    fat_range: Optional[RangeSpec] = None
    dry_matter_range: Optional[RangeSpec] = None
    liquid_range: Optional[RangeSpec] = None

    # Technical ranges
    pod_range: Optional[RangeSpec] = None
    pac_range: Optional[RangeSpec] = None

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }
        for range_name in ("sugar_range", "fat_range", "dry_matter_range",
                           "liquid_range", "pod_range", "pac_range"):
            val = getattr(self, range_name)
            result[range_name] = val.to_dict() if val else None
        return result

    @classmethod
    def from_dict(cls, data: dict) -> RecipeCategory:
        def _parse_range(key: str) -> Optional[RangeSpec]:
            r = data.get(key)
            if r and isinstance(r, dict):
                return RangeSpec.from_dict(r)
            return None

        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            sugar_range=_parse_range("sugar_range"),
            fat_range=_parse_range("fat_range"),
            dry_matter_range=_parse_range("dry_matter_range"),
            liquid_range=_parse_range("liquid_range"),
            pod_range=_parse_range("pod_range"),
            pac_range=_parse_range("pac_range"),
        )
