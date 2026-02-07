"""Integration tests - full workflow from recipe creation to validation."""
import json
import pytest
from pathlib import Path

from src.models.recipe import Recipe
from src.models.ingredient import IngredientProfile
from src.models.category import RecipeCategory
from src.engine.calculator import RecipeCalculator
from src.engine.validator import RecipeValidator, ValidationLevel
from src.io.file_manager import FileManager
from src.io.export import CSVExporter


class TestFullWorkflow:
    """End-to-end workflow tests."""

    @pytest.fixture
    def ingredients(self):
        return FileManager.load_ingredients()

    @pytest.fixture
    def categories(self):
        return FileManager.load_categories()

    @pytest.fixture
    def calculator(self, ingredients):
        return RecipeCalculator(ingredients)

    @pytest.fixture
    def validator(self):
        return RecipeValidator()

    def test_create_calculate_validate_save(self, calculator, validator, categories, tmp_path):
        """Full workflow: create recipe -> calculate -> validate -> save -> load -> verify."""
        # 1. Create recipe
        recipe = Recipe(
            name="Test Ganache Workflow",
            category_id="ganache_molded",
            author="Integration Test",
        )
        recipe.add_item("cream_35", 300.0)
        recipe.add_item("inverted_sugar", 70.0)
        recipe.add_item("dark_choc_65", 400.0)

        # 2. Calculate
        analysis = calculator.calculate(recipe)
        assert analysis.totals.total_weight_g == 770.0
        assert len(analysis.breakdowns) == 3
        assert analysis.totals.total_sugars_pct > 0
        assert analysis.totals.total_fats_pct > 0

        # 3. Validate
        category = categories["ganache_molded"]
        validation = validator.validate(analysis.totals, category)
        assert validation.category_name == "Ganache moldeada"
        # With cream+chocolate, this should have reasonable fat/sugar values
        assert len(validation.metrics) == 6

        # 4. Save
        path = str(tmp_path / "workflow_test.json")
        FileManager.save_recipe(recipe, path)

        # 5. Load and verify
        loaded = FileManager.load_recipe(path)
        assert loaded.name == recipe.name
        assert loaded.category_id == recipe.category_id
        assert len(loaded.items) == 3

        # 6. Recalculate from loaded and compare
        analysis2 = calculator.calculate(loaded)
        assert abs(analysis2.totals.total_sugars_pct - analysis.totals.total_sugars_pct) < 0.01
        assert abs(analysis2.totals.total_fats_pct - analysis.totals.total_fats_pct) < 0.01

    def test_scale_and_export(self, calculator, tmp_path):
        """Create recipe, scale it, export to CSV."""
        recipe = Recipe(name="Scale Test")
        recipe.add_item("cream_35", 300.0)
        recipe.add_item("sucrose", 100.0)

        # Scale to 1kg
        recipe.scale_to_weight(1000.0)
        assert abs(recipe.total_weight_g - 1000.0) < 1.0

        # Calculate and export
        analysis = calculator.calculate(recipe)
        path = str(tmp_path / "scaled_export.csv")
        CSVExporter.export(analysis, path)

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "TOTALES" in content
        assert "1000.0" in content

    def test_ganache_reference_with_real_db(self, calculator, validator, categories):
        """Replicate the GanacheSolution screenshot using the real ingredient database."""
        recipe = Recipe(name="65% dark chocolate ganache", category_id="ganache_molded")
        recipe.add_item("cream_35", 305.0)
        recipe.add_item("inverted_sugar", 72.0)
        recipe.add_item("glucose_syrup_de60", 46.0)
        recipe.add_item("sorbitol_powder", 58.0)
        recipe.add_item("anhydrous_butter", 112.0)
        recipe.add_item("dark_choc_65", 420.0)

        analysis = calculator.calculate(recipe)
        t = analysis.totals

        # Verify reasonable ranges (exact match depends on ingredient data precision)
        assert 25.0 < t.total_sugars_pct < 35.0, f"Sugars: {t.total_sugars_pct:.1f}%"
        assert 33.0 < t.total_fats_pct < 42.0, f"Fats: {t.total_fats_pct:.1f}%"
        assert 8.0 < t.total_dry_matter_pct < 18.0, f"Dry matter: {t.total_dry_matter_pct:.1f}%"
        assert 15.0 < t.total_liquids_pct < 25.0, f"Liquids: {t.total_liquids_pct:.1f}%"

        # Technical values
        assert 20 < t.pod < 40, f"POD: {t.pod:.1f}"
        assert 30 < t.pac < 55, f"PAC: {t.pac:.1f}"
        assert 450 < t.kcal_per_100g < 570, f"Kcal: {t.kcal_per_100g:.1f}"

        # Validate against category
        category = categories["ganache_molded"]
        validation = validator.validate(t, category)
        # This recipe should be mostly within range for a molded ganache
        red_count = sum(1 for m in validation.metrics if m.level == ValidationLevel.RED)
        # Allow at most 1-2 red metrics due to data approximation
        assert red_count <= 2, (
            f"Too many out-of-range metrics: "
            + ", ".join(f"{m.display_name}={m.value:.1f}" for m in validation.metrics if m.level == ValidationLevel.RED)
        )

    def test_empty_recipe_no_crash(self, calculator, validator, categories):
        """An empty recipe should calculate and validate without errors."""
        recipe = Recipe()
        analysis = calculator.calculate(recipe)
        assert analysis.totals.total_weight_g == 0.0

        category = categories["ganache_molded"]
        validation = validator.validate(analysis.totals, category)
        assert validation.category_name == "Ganache moldeada"
