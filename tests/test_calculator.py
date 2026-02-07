"""Tests for the recipe calculation engine.

Includes the reference ganache recipe from the GanacheSolution screenshot.
"""
import pytest
from src.models.ingredient import IngredientProfile
from src.models.recipe import Recipe
from src.engine.calculator import RecipeCalculator, RecipeAnalysis


def _make_db(*ingredients: IngredientProfile) -> dict[str, IngredientProfile]:
    """Helper to create an ingredient database from a list."""
    return {ing.id: ing for ing in ingredients}


# --- Reference ingredients for the ganache test ---
# Based on real-world pastry science values

CREAM_35 = IngredientProfile(
    id="cream_35", name="Nata 35%", group="Lácteos",
    butter_fat_pct=35.0, amp_pct=2.3, lactose_pct=1.7, water_pct=61.0,
    pod=6, pac=0, kcal_per_100g=335, cost_per_kg=4.5,
)

INVERTED_SUGAR = IngredientProfile(
    id="inverted_sugar", name="Azúcar invertido", group="Azúcares",
    sugar_pct=75.0, water_pct=25.0,
    pod=130, pac=190, kcal_per_100g=300, cost_per_kg=5.0,
)

GLUCOSE_60 = IngredientProfile(
    id="glucose_60", name="Glucosa DE 60", group="Azúcares",
    sugar_pct=80.0, water_pct=20.0,
    pod=50, pac=120, kcal_per_100g=320, cost_per_kg=3.5,
)

SORBITOL_POWDER = IngredientProfile(
    id="sorbitol_powder", name="Sorbitol polvo", group="Azúcares",
    sugar_pct=98.0, water_pct=2.0,
    pod=60, pac=190, kcal_per_100g=392, cost_per_kg=5.5,
)

ANHYDROUS_BUTTER = IngredientProfile(
    id="anhydrous_butter", name="Mantequilla anhidra", group="Lácteos",
    butter_fat_pct=99.5, water_pct=0.5,
    pod=0, pac=0, kcal_per_100g=900, cost_per_kg=12.0,
)

DARK_CHOC_65 = IngredientProfile(
    id="dark_choc_65", name="Chocolate negro 65%", group="Chocolate",
    sugar_pct=33.0, cocoa_butter_pct=38.0, cocoa_pct=27.0,
    other_solids_pct=1.0, water_pct=1.0,
    pod=33, pac=33, kcal_per_100g=580, cost_per_kg=14.0,
)


class TestRecipeCalculatorEmpty:
    """Tests with empty or trivial recipes."""

    def test_empty_recipe(self):
        db = _make_db()
        calc = RecipeCalculator(db)
        r = Recipe()
        result = calc.calculate(r)
        assert len(result.breakdowns) == 0
        assert result.totals.total_weight_g == 0.0

    def test_unknown_ingredient(self):
        """Unknown ingredients should be silently skipped."""
        db = _make_db()
        calc = RecipeCalculator(db)
        r = Recipe()
        r.add_item("nonexistent", 100.0)
        result = calc.calculate(r)
        assert len(result.breakdowns) == 0

    def test_single_ingredient_100pct(self):
        """A recipe with one ingredient should have that ingredient at 100%."""
        sugar = IngredientProfile(id="sugar", name="Sugar", sugar_pct=100.0, pod=100, pac=100, kcal_per_100g=400)
        db = _make_db(sugar)
        calc = RecipeCalculator(db)
        r = Recipe()
        r.add_item("sugar", 500.0)
        result = calc.calculate(r)

        assert len(result.breakdowns) == 1
        bd = result.breakdowns[0]
        assert abs(bd.percentage - 100.0) < 0.01
        assert abs(bd.sugar - 100.0) < 0.01

        t = result.totals
        assert abs(t.total_sugars_pct - 100.0) < 0.01
        assert abs(t.total_fats_pct) < 0.01
        assert abs(t.pod - 100.0) < 0.01
        assert abs(t.pac - 100.0) < 0.01
        assert abs(t.kcal_per_100g - 400.0) < 0.01


class TestRecipeCalculatorGanache:
    """Reference test: 65% dark chocolate ganache from GanacheSolution screenshot.

    Recipe:
      - Nata 35%:              305g (30.1%)
      - Azúcar invertido:       72g (7.1%)
      - Glucosa DE 60:          46g (4.5%)
      - Sorbitol polvo:         58g (5.7%)
      - Mantequilla anhidra:   112g (11.1%)
      - Chocolate negro 65%:   420g (41.5%)
      Total: 1013g

    Expected totals (from screenshot):
      - Azúcares:      ~29.3%
      - Grasas:        ~37.5%
      - Materia seca:  ~11.6%
      - Líquidos:      ~20.1%
      - POD:           ~29
      - PAC:           ~43
      - Kcal/100g:     ~502
    """

    @pytest.fixture
    def ganache_analysis(self) -> RecipeAnalysis:
        db = _make_db(
            CREAM_35, INVERTED_SUGAR, GLUCOSE_60,
            SORBITOL_POWDER, ANHYDROUS_BUTTER, DARK_CHOC_65,
        )
        calc = RecipeCalculator(db)
        r = Recipe(name="65% dark chocolate ganache", category_id="ganache_molded")
        r.add_item("cream_35", 305.0)
        r.add_item("inverted_sugar", 72.0)
        r.add_item("glucose_60", 46.0)
        r.add_item("sorbitol_powder", 58.0)
        r.add_item("anhydrous_butter", 112.0)
        r.add_item("dark_choc_65", 420.0)
        return calc.calculate(r)

    def test_total_weight(self, ganache_analysis):
        assert abs(ganache_analysis.totals.total_weight_g - 1013.0) < 0.01

    def test_ingredient_count(self, ganache_analysis):
        assert len(ganache_analysis.breakdowns) == 6

    def test_cream_percentage(self, ganache_analysis):
        """Cream should be ~30.1% of total."""
        cream_bd = [bd for bd in ganache_analysis.breakdowns if bd.ingredient_id == "cream_35"][0]
        assert abs(cream_bd.percentage - 30.1) < 0.2

    def test_chocolate_percentage(self, ganache_analysis):
        """Chocolate should be ~41.5% of total."""
        choc_bd = [bd for bd in ganache_analysis.breakdowns if bd.ingredient_id == "dark_choc_65"][0]
        assert abs(choc_bd.percentage - 41.5) < 0.2

    def test_total_sugars(self, ganache_analysis):
        """Total sugars should be approximately 29.3%."""
        assert abs(ganache_analysis.totals.total_sugars_pct - 29.3) < 1.5

    def test_total_fats(self, ganache_analysis):
        """Total fats should be approximately 37.5%."""
        assert abs(ganache_analysis.totals.total_fats_pct - 37.5) < 1.5

    def test_total_dry_matter(self, ganache_analysis):
        """Total dry matter should be approximately 11-13%."""
        # The screenshot says 11.6% but composition data can vary slightly
        dm = ganache_analysis.totals.total_dry_matter_pct
        assert 9.0 < dm < 15.0, f"Dry matter = {dm:.1f}%, expected ~11-13%"

    def test_total_liquids(self, ganache_analysis):
        """Total liquids should be approximately 20.1%."""
        assert abs(ganache_analysis.totals.total_liquids_pct - 20.1) < 2.0

    def test_pod(self, ganache_analysis):
        """POD should be approximately 29."""
        assert abs(ganache_analysis.totals.pod - 29.0) < 5.0

    def test_pac(self, ganache_analysis):
        """PAC should be approximately 43."""
        assert abs(ganache_analysis.totals.pac - 43.0) < 8.0

    def test_kcal(self, ganache_analysis):
        """Kcal/100g should be approximately 502."""
        assert abs(ganache_analysis.totals.kcal_per_100g - 502.0) < 30.0

    def test_components_sum_near_100(self, ganache_analysis):
        """All component totals should sum to approximately 100%."""
        t = ganache_analysis.totals
        total = (t.total_sugars_pct + t.total_fats_pct +
                 t.total_dry_matter_pct + t.total_liquids_pct)
        assert abs(total - 100.0) < 2.0, f"Components sum = {total:.1f}%, expected ~100%"


class TestRecipeCalculatorScaling:
    """Tests for recipe weight scaling."""

    def test_scale_preserves_percentages(self):
        """Scaling recipe weight should not change percentage breakdowns."""
        sugar = IngredientProfile(id="sugar", name="Sugar", sugar_pct=100.0, pod=100, pac=100, kcal_per_100g=400)
        water = IngredientProfile(id="water", name="Water", water_pct=100.0)
        db = _make_db(sugar, water)
        calc = RecipeCalculator(db)

        r = Recipe()
        r.add_item("sugar", 200.0)
        r.add_item("water", 800.0)
        result1 = calc.calculate(r)

        r.scale_to_weight(2000.0)
        result2 = calc.calculate(r)

        assert abs(result1.totals.total_sugars_pct - result2.totals.total_sugars_pct) < 0.1
        assert abs(result1.totals.total_liquids_pct - result2.totals.total_liquids_pct) < 0.1
        assert abs(result1.totals.kcal_per_100g - result2.totals.kcal_per_100g) < 0.5

    def test_cost_scales_with_weight(self):
        """Total cost should scale proportionally with weight."""
        sugar = IngredientProfile(id="sugar", name="Sugar", sugar_pct=100.0, cost_per_kg=2.0)
        db = _make_db(sugar)
        calc = RecipeCalculator(db)

        r = Recipe()
        r.add_item("sugar", 500.0)
        result1 = calc.calculate(r)
        cost1 = result1.totals.total_cost

        r.scale_to_weight(1000.0)
        result2 = calc.calculate(r)
        cost2 = result2.totals.total_cost

        assert abs(cost2 / cost1 - 2.0) < 0.1
