"""Recipe data model."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class RecipeItem:
    """A single ingredient entry in a recipe."""

    ingredient_id: str
    quantity_g: float  # Grams

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> RecipeItem:
        return cls(
            ingredient_id=data["ingredient_id"],
            quantity_g=float(data["quantity_g"]),
        )


@dataclass
class Recipe:
    """A pastry recipe with metadata and ingredient list."""

    name: str = "Nueva receta"
    category_id: str = ""
    status: str = "Borrador"  # Borrador, Confirmada, Prueba
    author: str = ""
    origin: str = ""
    notes: str = ""
    items: list[RecipeItem] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def total_weight_g(self) -> float:
        """Total recipe weight in grams."""
        return sum(item.quantity_g for item in self.items)

    def add_item(self, ingredient_id: str, quantity_g: float) -> None:
        """Add an ingredient to the recipe."""
        # Check if ingredient already exists
        for item in self.items:
            if item.ingredient_id == ingredient_id:
                item.quantity_g = quantity_g
                self._touch()
                return
        self.items.append(RecipeItem(ingredient_id=ingredient_id, quantity_g=quantity_g))
        self._touch()

    def remove_item(self, ingredient_id: str) -> bool:
        """Remove an ingredient. Returns True if found and removed."""
        for i, item in enumerate(self.items):
            if item.ingredient_id == ingredient_id:
                self.items.pop(i)
                self._touch()
                return True
        return False

    def update_quantity(self, ingredient_id: str, quantity_g: float) -> bool:
        """Update the quantity of an existing ingredient. Returns True if found."""
        for item in self.items:
            if item.ingredient_id == ingredient_id:
                item.quantity_g = quantity_g
                self._touch()
                return True
        return False

    def scale_to_weight(self, target_weight_g: float) -> None:
        """Scale all ingredients proportionally to reach the target weight."""
        current = self.total_weight_g
        if current <= 0:
            return
        factor = target_weight_g / current
        for item in self.items:
            item.quantity_g = round(item.quantity_g * factor, 1)
        self._touch()

    def duplicate(self) -> Recipe:
        """Create a copy of this recipe."""
        new = Recipe(
            name=f"{self.name} (copia)",
            category_id=self.category_id,
            status="Borrador",
            author=self.author,
            origin=self.origin,
            notes=self.notes,
            items=[RecipeItem(i.ingredient_id, i.quantity_g) for i in self.items],
        )
        return new

    def get_item_percentage(self, ingredient_id: str) -> float:
        """Get the percentage of total weight for a specific ingredient."""
        total = self.total_weight_g
        if total <= 0:
            return 0.0
        for item in self.items:
            if item.ingredient_id == ingredient_id:
                return (item.quantity_g / total) * 100.0
        return 0.0

    def _touch(self) -> None:
        """Update the modified timestamp."""
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category_id": self.category_id,
            "status": self.status,
            "author": self.author,
            "origin": self.origin,
            "notes": self.notes,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Recipe:
        items = [RecipeItem.from_dict(i) for i in data.get("items", [])]
        return cls(
            name=data.get("name", "Nueva receta"),
            category_id=data.get("category_id", ""),
            status=data.get("status", "Borrador"),
            author=data.get("author", ""),
            origin=data.get("origin", ""),
            notes=data.get("notes", ""),
            items=items,
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )
