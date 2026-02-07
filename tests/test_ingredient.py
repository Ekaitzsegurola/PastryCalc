"""Tests for IngredientProfile model."""
import json
import pytest
from pathlib import Path

from src.models.ingredient import IngredientProfile


class TestIngredientProfile:
    """Tests for the IngredientProfile dataclass."""

    def test_create_basic(self):
        """Create a basic ingredient and verify fields."""
        ing = IngredientProfile(id="test", name="Test Ingredient", group="Test")
        assert ing.id == "test"
        assert ing.name == "Test Ingredient"
        assert ing.group == "Test"
        assert ing.sugar_pct == 0.0

    def test_component_sum_sugar(self):
        """Pure sugar should sum to 100%."""
        ing = IngredientProfile(id="sugar", name="Sugar", sugar_pct=100.0)
        assert abs(ing.component_sum - 100.0) < 0.01

    def test_component_sum_cream(self):
        """Cream 35% components should sum to ~100%."""
        ing = IngredientProfile(
            id="cream", name="Cream 35%",
            butter_fat_pct=35.0, amp_pct=2.3, lactose_pct=1.7, water_pct=61.0,
        )
        assert abs(ing.component_sum - 100.0) < 0.01

    def test_total_fat(self):
        """Total fat should be sum of oil + butter_fat + cocoa_butter."""
        ing = IngredientProfile(
            id="test", name="Test",
            oil_pct=10.0, butter_fat_pct=20.0, cocoa_butter_pct=30.0,
        )
        assert abs(ing.total_fat_pct - 60.0) < 0.01

    def test_total_dry_matter(self):
        """Total dry matter should be cocoa + amp + lactose + other."""
        ing = IngredientProfile(
            id="test", name="Test",
            cocoa_pct=10.0, amp_pct=5.0, lactose_pct=3.0, other_solids_pct=2.0,
        )
        assert abs(ing.total_dry_matter_pct - 20.0) < 0.01

    def test_total_liquid(self):
        """Total liquid should be water + alcohol."""
        ing = IngredientProfile(
            id="test", name="Test",
            water_pct=60.0, alcohol_pct=10.0,
        )
        assert abs(ing.total_liquid_pct - 70.0) < 0.01

    def test_is_valid_true(self):
        """An ingredient summing to 100% should be valid."""
        ing = IngredientProfile(id="s", name="S", sugar_pct=100.0)
        assert ing.is_valid()

    def test_is_valid_false(self):
        """An ingredient summing to 50% should NOT be valid."""
        ing = IngredientProfile(id="s", name="S", sugar_pct=50.0)
        assert not ing.is_valid()

    def test_to_dict_roundtrip(self):
        """Serialize and deserialize should produce the same ingredient."""
        original = IngredientProfile(
            id="choc", name="Choc 65%", group="Chocolate",
            sugar_pct=33.0, cocoa_butter_pct=38.0, cocoa_pct=27.0,
            other_solids_pct=1.0, water_pct=1.0,
            pod=33, pac=33, kcal_per_100g=580, cost_per_kg=14.0,
        )
        d = original.to_dict()
        restored = IngredientProfile.from_dict(d)
        assert restored.id == original.id
        assert restored.name == original.name
        assert abs(restored.sugar_pct - original.sugar_pct) < 0.01
        assert abs(restored.cocoa_butter_pct - original.cocoa_butter_pct) < 0.01
        assert abs(restored.pod - original.pod) < 0.01

    def test_from_dict_extra_keys(self):
        """from_dict should ignore unknown keys gracefully."""
        d = {"id": "x", "name": "X", "unknown_field": 999}
        ing = IngredientProfile.from_dict(d)
        assert ing.id == "x"
        assert ing.name == "X"


class TestIngredientDatabase:
    """Tests that validate the built-in ingredient database."""

    @pytest.fixture
    def ingredients(self):
        """Load the built-in ingredient database."""
        path = Path(__file__).parent.parent / "src" / "data" / "ingredients.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [IngredientProfile.from_dict(item) for item in data]

    def test_database_not_empty(self, ingredients):
        """Database should have at least 40 ingredients."""
        assert len(ingredients) >= 40

    def test_all_have_ids(self, ingredients):
        """Every ingredient must have a non-empty id."""
        for ing in ingredients:
            assert ing.id, f"Ingredient {ing.name} has empty id"

    def test_unique_ids(self, ingredients):
        """All ingredient ids should be unique."""
        ids = [ing.id for ing in ingredients]
        assert len(ids) == len(set(ids)), "Duplicate ingredient ids found"

    def test_all_components_sum_to_100(self, ingredients):
        """Every ingredient's components should sum to approximately 100%."""
        for ing in ingredients:
            assert ing.is_valid(), (
                f"{ing.name} (id={ing.id}): component sum = {ing.component_sum:.1f}%, "
                f"expected ~100%"
            )

    def test_all_have_names(self, ingredients):
        """Every ingredient must have a non-empty name."""
        for ing in ingredients:
            assert ing.name, f"Ingredient {ing.id} has empty name"

    def test_all_have_groups(self, ingredients):
        """Every ingredient must have a group."""
        for ing in ingredients:
            assert ing.group, f"Ingredient {ing.id} ({ing.name}) has empty group"

    def test_no_negative_values(self, ingredients):
        """No component percentage should be negative."""
        for ing in ingredients:
            for field in ["sugar_pct", "oil_pct", "butter_fat_pct", "cocoa_butter_pct",
                          "cocoa_pct", "amp_pct", "lactose_pct", "other_solids_pct",
                          "water_pct", "alcohol_pct", "pod", "pac", "kcal_per_100g"]:
                val = getattr(ing, field)
                assert val >= 0, f"{ing.name}.{field} = {val} (negative)"
