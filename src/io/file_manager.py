"""File manager for saving/loading recipes and ingredient databases."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from src.models.ingredient import IngredientProfile
from src.models.recipe import Recipe
from src.models.category import RecipeCategory


def _data_dir() -> Path:
    """Return the path to the bundled data directory.

    Handles both development (src/data/) and PyInstaller (sys._MEIPASS) paths.
    """
    import sys
    if getattr(sys, 'frozen', False):
        # Running from PyInstaller bundle
        base = Path(sys._MEIPASS)  # type: ignore
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "data"


class FileManager:
    """Manages loading/saving of recipes, ingredients, and categories."""

    @staticmethod
    def load_ingredients(path: Optional[str] = None) -> dict[str, IngredientProfile]:
        """Load ingredient database from JSON. Returns dict keyed by id."""
        if path is None:
            path = str(_data_dir() / "ingredients.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {item["id"]: IngredientProfile.from_dict(item) for item in data}

    @staticmethod
    def save_ingredients(ingredients: dict[str, IngredientProfile], path: str) -> None:
        """Save ingredient database to JSON."""
        data = [ing.to_dict() for ing in ingredients.values()]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_categories(path: Optional[str] = None) -> dict[str, RecipeCategory]:
        """Load categories from JSON. Returns dict keyed by id."""
        if path is None:
            path = str(_data_dir() / "categories.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {item["id"]: RecipeCategory.from_dict(item) for item in data}

    @staticmethod
    def load_recipe(path: str) -> Recipe:
        """Load a recipe from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Recipe.from_dict(data)

    @staticmethod
    def save_recipe(recipe: Recipe, path: str) -> None:
        """Save a recipe to a JSON file."""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(recipe.to_dict(), f, ensure_ascii=False, indent=2)
