"""Tests for file manager (save/load) and CSV export."""
import json
import os
import tempfile
import pytest

from src.models.recipe import Recipe
from src.models.ingredient import IngredientProfile
from src.io.file_manager import FileManager
from src.io.export import CSVExporter
from src.engine.calculator import RecipeCalculator, RecipeAnalysis


class TestFileManagerRecipes:
    """Tests for recipe save/load."""

    def test_save_and_load_recipe(self, tmp_path):
        """Save a recipe and load it back - should be identical."""
        recipe = Recipe(
            name="Test Ganache",
            category_id="ganache_molded",
            status="Confirmada",
            author="Chef Test",
            notes="Test notes here",
        )
        recipe.add_item("cream_35", 305.0)
        recipe.add_item("dark_choc_65", 420.0)

        path = str(tmp_path / "test_recipe.json")
        FileManager.save_recipe(recipe, path)

        loaded = FileManager.load_recipe(path)
        assert loaded.name == recipe.name
        assert loaded.category_id == recipe.category_id
        assert loaded.status == recipe.status
        assert loaded.author == recipe.author
        assert loaded.notes == recipe.notes
        assert len(loaded.items) == 2
        assert loaded.items[0].ingredient_id == "cream_35"
        assert abs(loaded.items[0].quantity_g - 305.0) < 0.01

    def test_save_creates_directory(self, tmp_path):
        """Save should create intermediate directories."""
        recipe = Recipe(name="Nested")
        path = str(tmp_path / "subdir" / "nested" / "recipe.json")
        FileManager.save_recipe(recipe, path)
        assert os.path.exists(path)

    def test_saved_file_is_valid_json(self, tmp_path):
        """Saved file should be valid JSON."""
        recipe = Recipe(name="JSON Test")
        recipe.add_item("sugar", 100.0)
        path = str(tmp_path / "json_test.json")
        FileManager.save_recipe(recipe, path)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)  # Should not raise
        assert data["name"] == "JSON Test"
        assert len(data["items"]) == 1


class TestFileManagerIngredients:
    """Tests for ingredient database loading."""

    def test_load_builtin_ingredients(self):
        """Built-in ingredients should load successfully."""
        ingredients = FileManager.load_ingredients()
        assert len(ingredients) >= 40
        assert "cream_35" in ingredients
        assert "dark_choc_65" in ingredients

    def test_load_builtin_categories(self):
        """Built-in categories should load successfully."""
        categories = FileManager.load_categories()
        assert len(categories) >= 8
        assert "ganache_molded" in categories
        assert "ice_cream" in categories


class TestCSVExporter:
    """Tests for CSV export."""

    def test_export_to_string(self):
        """Export should produce a non-empty CSV string."""
        sugar = IngredientProfile(
            id="sugar", name="Sugar", sugar_pct=100.0,
            pod=100, pac=100, kcal_per_100g=400,
        )
        db = {"sugar": sugar}
        calc = RecipeCalculator(db)
        r = Recipe()
        r.add_item("sugar", 500.0)
        analysis = calc.calculate(r)

        csv_str = CSVExporter.to_string(analysis)
        assert "Sugar" in csv_str
        assert "TOTALES" in csv_str
        assert "RESUMEN" in csv_str

    def test_export_to_file(self, tmp_path):
        """Export to file should create a readable CSV."""
        sugar = IngredientProfile(
            id="sugar", name="Sugar", sugar_pct=100.0,
            pod=100, pac=100, kcal_per_100g=400,
        )
        db = {"sugar": sugar}
        calc = RecipeCalculator(db)
        r = Recipe()
        r.add_item("sugar", 200.0)
        analysis = calc.calculate(r)

        path = str(tmp_path / "export.csv")
        CSVExporter.export(analysis, path)
        assert os.path.exists(path)

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Sugar" in content
        assert "200.0" in content

    def test_export_empty_analysis(self):
        """Exporting empty analysis should still produce valid CSV."""
        analysis = RecipeAnalysis()
        csv_str = CSVExporter.to_string(analysis)
        assert "TOTALES" in csv_str
