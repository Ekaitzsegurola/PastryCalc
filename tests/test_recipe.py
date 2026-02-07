"""Tests for Recipe model."""
import pytest
from src.models.recipe import Recipe, RecipeItem


class TestRecipeItem:
    """Tests for RecipeItem."""

    def test_create(self):
        item = RecipeItem(ingredient_id="sugar", quantity_g=100.0)
        assert item.ingredient_id == "sugar"
        assert item.quantity_g == 100.0

    def test_to_dict_roundtrip(self):
        item = RecipeItem(ingredient_id="cream_35", quantity_g=305.0)
        d = item.to_dict()
        restored = RecipeItem.from_dict(d)
        assert restored.ingredient_id == item.ingredient_id
        assert restored.quantity_g == item.quantity_g


class TestRecipe:
    """Tests for Recipe model."""

    def test_create_empty(self):
        r = Recipe()
        assert r.total_weight_g == 0.0
        assert len(r.items) == 0

    def test_add_item(self):
        r = Recipe()
        r.add_item("sugar", 100.0)
        assert len(r.items) == 1
        assert r.items[0].ingredient_id == "sugar"
        assert r.items[0].quantity_g == 100.0

    def test_add_item_updates_existing(self):
        """Adding the same ingredient twice should update quantity."""
        r = Recipe()
        r.add_item("sugar", 100.0)
        r.add_item("sugar", 200.0)
        assert len(r.items) == 1
        assert r.items[0].quantity_g == 200.0

    def test_remove_item(self):
        r = Recipe()
        r.add_item("sugar", 100.0)
        r.add_item("cream", 200.0)
        assert r.remove_item("sugar")
        assert len(r.items) == 1
        assert r.items[0].ingredient_id == "cream"

    def test_remove_nonexistent(self):
        r = Recipe()
        assert not r.remove_item("nonexistent")

    def test_total_weight(self):
        r = Recipe()
        r.add_item("sugar", 100.0)
        r.add_item("cream", 200.0)
        assert abs(r.total_weight_g - 300.0) < 0.01

    def test_update_quantity(self):
        r = Recipe()
        r.add_item("sugar", 100.0)
        assert r.update_quantity("sugar", 150.0)
        assert r.items[0].quantity_g == 150.0

    def test_update_quantity_nonexistent(self):
        r = Recipe()
        assert not r.update_quantity("sugar", 150.0)

    def test_scale_to_weight(self):
        """Scaling should preserve proportions."""
        r = Recipe()
        r.add_item("a", 100.0)
        r.add_item("b", 200.0)
        r.scale_to_weight(600.0)
        assert abs(r.total_weight_g - 600.0) < 1.0
        # Proportions preserved: a was 1/3, b was 2/3
        assert abs(r.items[0].quantity_g - 200.0) < 1.0
        assert abs(r.items[1].quantity_g - 400.0) < 1.0

    def test_scale_empty_recipe(self):
        """Scaling an empty recipe should be a no-op."""
        r = Recipe()
        r.scale_to_weight(1000.0)
        assert r.total_weight_g == 0.0

    def test_get_item_percentage(self):
        r = Recipe()
        r.add_item("a", 250.0)
        r.add_item("b", 750.0)
        assert abs(r.get_item_percentage("a") - 25.0) < 0.01
        assert abs(r.get_item_percentage("b") - 75.0) < 0.01

    def test_get_item_percentage_nonexistent(self):
        r = Recipe()
        r.add_item("a", 100.0)
        assert r.get_item_percentage("nonexistent") == 0.0

    def test_duplicate(self):
        r = Recipe(name="Original", category_id="ganache_molded", author="Chef")
        r.add_item("sugar", 100.0)
        copy = r.duplicate()
        assert copy.name == "Original (copia)"
        assert copy.category_id == "ganache_molded"
        assert len(copy.items) == 1
        # Modifying copy should not affect original
        copy.add_item("water", 50.0)
        assert len(r.items) == 1

    def test_to_dict_roundtrip(self):
        r = Recipe(name="Test", category_id="ice_cream", author="Me", notes="Test notes")
        r.add_item("sugar", 100.0)
        r.add_item("cream", 200.0)
        d = r.to_dict()
        restored = Recipe.from_dict(d)
        assert restored.name == r.name
        assert restored.category_id == r.category_id
        assert restored.author == r.author
        assert restored.notes == r.notes
        assert len(restored.items) == 2
        assert restored.items[0].ingredient_id == "sugar"
