"""Tests for the recipe validation engine."""
import pytest
from src.models.category import RecipeCategory, RangeSpec
from src.engine.calculator import RecipeTotals
from src.engine.validator import RecipeValidator, ValidationLevel


@pytest.fixture
def validator():
    return RecipeValidator()


def _make_totals(**kwargs) -> RecipeTotals:
    """Helper to create RecipeTotals with specified values."""
    t = RecipeTotals()
    for k, v in kwargs.items():
        setattr(t, k, v)
    return t


GANACHE_MOLDED = RecipeCategory(
    id="ganache_molded", name="Ganache moldeada",
    sugar_range=RangeSpec(22, 32),
    fat_range=RangeSpec(28, 35),
    dry_matter_range=RangeSpec(5, 18),
    liquid_range=RangeSpec(18, 25),
)

ICE_CREAM = RecipeCategory(
    id="ice_cream", name="Helado",
    sugar_range=RangeSpec(18, 22),
    fat_range=RangeSpec(6, 12),
    dry_matter_range=RangeSpec(10, 20),
    liquid_range=RangeSpec(58, 66),
    pod_range=RangeSpec(16, 20),
    pac_range=RangeSpec(24, 28),
)


class TestValidatorNoCategory:
    """Tests when no category is provided."""

    def test_no_category_returns_empty(self, validator):
        totals = _make_totals()
        result = validator.validate(totals, None)
        assert len(result.metrics) == 0
        assert result.category_name == "(sin categoría)"


class TestValidatorGanache:
    """Tests for ganache moldeada validation."""

    def test_perfect_ganache(self, validator):
        """A ganache within all ranges should be all green."""
        totals = _make_totals(
            total_sugars_pct=27.0,
            total_fats_pct=31.0,
            total_dry_matter_pct=12.0,
            total_liquids_pct=21.0,
        )
        result = validator.validate(totals, GANACHE_MOLDED)
        assert result.is_valid
        assert not result.has_errors
        assert result.category_name == "Ganache moldeada"

    def test_too_much_fat(self, validator):
        """Excess fat should trigger red or orange."""
        totals = _make_totals(
            total_sugars_pct=27.0,
            total_fats_pct=50.0,  # Way over 35%
            total_dry_matter_pct=12.0,
            total_liquids_pct=11.0,
        )
        result = validator.validate(totals, GANACHE_MOLDED)
        fat_metric = next(m for m in result.metrics if m.metric_name == "fat")
        assert fat_metric.level == ValidationLevel.RED
        assert not result.is_valid

    def test_too_little_sugar(self, validator):
        """Very low sugar should trigger red."""
        totals = _make_totals(
            total_sugars_pct=5.0,  # Way under 22%
            total_fats_pct=31.0,
            total_dry_matter_pct=12.0,
            total_liquids_pct=21.0,
        )
        result = validator.validate(totals, GANACHE_MOLDED)
        sugar_metric = next(m for m in result.metrics if m.metric_name == "sugar")
        assert sugar_metric.level == ValidationLevel.RED

    def test_borderline_sugar(self, validator):
        """Sugar just outside range should trigger orange."""
        totals = _make_totals(
            total_sugars_pct=21.0,  # Just below 22%
            total_fats_pct=31.0,
            total_dry_matter_pct=12.0,
            total_liquids_pct=21.0,
        )
        result = validator.validate(totals, GANACHE_MOLDED)
        sugar_metric = next(m for m in result.metrics if m.metric_name == "sugar")
        assert sugar_metric.level == ValidationLevel.ORANGE

    def test_recommendations_generated(self, validator):
        """Out-of-range metrics should generate recommendations."""
        totals = _make_totals(
            total_sugars_pct=5.0,
            total_fats_pct=50.0,
            total_dry_matter_pct=12.0,
            total_liquids_pct=5.0,
        )
        result = validator.validate(totals, GANACHE_MOLDED)
        assert len(result.recommendations) > 0
        assert result.has_errors


class TestValidatorIceCream:
    """Tests for ice cream validation including POD/PAC."""

    def test_perfect_ice_cream(self, validator):
        """Ice cream within all ranges including POD/PAC."""
        totals = _make_totals(
            total_sugars_pct=20.0,
            total_fats_pct=9.0,
            total_dry_matter_pct=15.0,
            total_liquids_pct=62.0,
            pod=18.0,
            pac=26.0,
        )
        result = validator.validate(totals, ICE_CREAM)
        assert result.is_valid

    def test_pod_too_high(self, validator):
        """POD over range should flag."""
        totals = _make_totals(
            total_sugars_pct=20.0,
            total_fats_pct=9.0,
            total_dry_matter_pct=15.0,
            total_liquids_pct=62.0,
            pod=30.0,  # Way over 20
            pac=26.0,
        )
        result = validator.validate(totals, ICE_CREAM)
        pod_metric = next(m for m in result.metrics if m.metric_name == "pod")
        assert pod_metric.level in (ValidationLevel.ORANGE, ValidationLevel.RED)

    def test_pac_too_low(self, validator):
        """PAC under range should flag."""
        totals = _make_totals(
            total_sugars_pct=20.0,
            total_fats_pct=9.0,
            total_dry_matter_pct=15.0,
            total_liquids_pct=62.0,
            pod=18.0,
            pac=10.0,  # Way under 24
        )
        result = validator.validate(totals, ICE_CREAM)
        pac_metric = next(m for m in result.metrics if m.metric_name == "pac")
        assert pac_metric.level == ValidationLevel.RED


class TestRangeSpec:
    """Tests for the RangeSpec model."""

    def test_contains(self):
        r = RangeSpec(10, 20)
        assert r.contains(10)
        assert r.contains(15)
        assert r.contains(20)
        assert not r.contains(9.9)
        assert not r.contains(20.1)

    def test_is_near(self):
        r = RangeSpec(10, 20)
        # 10% of span (10) = 1.0 margin
        assert r.is_near(9.0, tolerance_pct=10)
        assert r.is_near(21.0, tolerance_pct=10)
        assert not r.is_near(5.0, tolerance_pct=10)

    def test_roundtrip(self):
        r = RangeSpec(22, 32)
        d = r.to_dict()
        restored = RangeSpec.from_dict(d)
        assert restored.min_val == 22
        assert restored.max_val == 32
