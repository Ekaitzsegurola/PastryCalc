"""Recipe calculation engine.

Computes per-ingredient breakdown and grouped totals for a recipe.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.models.ingredient import IngredientProfile
from src.models.recipe import Recipe


# Component field names on IngredientProfile
COMPONENT_FIELDS = [
    "sugar_pct", "oil_pct", "butter_fat_pct", "cocoa_butter_pct",
    "cocoa_pct", "amp_pct", "lactose_pct", "other_solids_pct",
    "water_pct", "alcohol_pct",
]


@dataclass
class IngredientBreakdown:
    """Calculated breakdown for a single ingredient in the recipe."""

    ingredient_id: str
    name: str
    quantity_g: float
    percentage: float  # % of total recipe weight

    # Component contributions (as % of total recipe weight)
    sugar: float = 0.0
    oil: float = 0.0
    butter_fat: float = 0.0
    cocoa_butter: float = 0.0
    cocoa: float = 0.0
    amp: float = 0.0
    lactose: float = 0.0
    other_solids: float = 0.0
    water: float = 0.0
    alcohol: float = 0.0

    # Technical values (weighted contribution)
    pod: float = 0.0
    pac: float = 0.0
    kcal: float = 0.0
    cost: float = 0.0


@dataclass
class RecipeTotals:
    """Aggregated totals for the entire recipe."""

    total_weight_g: float = 0.0

    # Component totals (% of total weight)
    sugar_pct: float = 0.0
    oil_pct: float = 0.0
    butter_fat_pct: float = 0.0
    cocoa_butter_pct: float = 0.0
    cocoa_pct: float = 0.0
    amp_pct: float = 0.0
    lactose_pct: float = 0.0
    other_solids_pct: float = 0.0
    water_pct: float = 0.0
    alcohol_pct: float = 0.0

    # Grouped totals
    total_sugars_pct: float = 0.0
    total_fats_pct: float = 0.0
    total_dry_matter_pct: float = 0.0
    total_liquids_pct: float = 0.0

    # Technical totals (weighted averages)
    pod: float = 0.0
    pac: float = 0.0
    kcal_per_100g: float = 0.0
    total_cost: float = 0.0


@dataclass
class RecipeAnalysis:
    """Full analysis result for a recipe."""

    breakdowns: list[IngredientBreakdown] = field(default_factory=list)
    totals: RecipeTotals = field(default_factory=RecipeTotals)


class RecipeCalculator:
    """Calculates recipe composition breakdowns and totals."""

    def __init__(self, ingredient_db: dict[str, IngredientProfile]):
        """Initialize with a dictionary of ingredient profiles keyed by id."""
        self._db = ingredient_db

    def calculate(self, recipe: Recipe) -> RecipeAnalysis:
        """Calculate full analysis for a recipe.

        Returns an analysis with per-ingredient breakdowns and grouped totals.
        """
        analysis = RecipeAnalysis()
        total_g = recipe.total_weight_g

        if total_g <= 0 or not recipe.items:
            return analysis

        analysis.totals.total_weight_g = total_g

        for item in recipe.items:
            profile = self._db.get(item.ingredient_id)
            if profile is None:
                continue

            pct_of_total = (item.quantity_g / total_g) * 100.0

            bd = IngredientBreakdown(
                ingredient_id=item.ingredient_id,
                name=profile.name,
                quantity_g=item.quantity_g,
                percentage=pct_of_total,
                sugar=pct_of_total * profile.sugar_pct / 100.0,
                oil=pct_of_total * profile.oil_pct / 100.0,
                butter_fat=pct_of_total * profile.butter_fat_pct / 100.0,
                cocoa_butter=pct_of_total * profile.cocoa_butter_pct / 100.0,
                cocoa=pct_of_total * profile.cocoa_pct / 100.0,
                amp=pct_of_total * profile.amp_pct / 100.0,
                lactose=pct_of_total * profile.lactose_pct / 100.0,
                other_solids=pct_of_total * profile.other_solids_pct / 100.0,
                water=pct_of_total * profile.water_pct / 100.0,
                alcohol=pct_of_total * profile.alcohol_pct / 100.0,
                pod=item.quantity_g * profile.pod / 100.0,
                pac=item.quantity_g * profile.pac / 100.0,
                kcal=item.quantity_g * profile.kcal_per_100g / 100.0,
                cost=item.quantity_g * profile.cost_per_kg / 1000.0,
            )
            analysis.breakdowns.append(bd)

        # Sum up totals from breakdowns
        totals = analysis.totals
        for bd in analysis.breakdowns:
            totals.sugar_pct += bd.sugar
            totals.oil_pct += bd.oil
            totals.butter_fat_pct += bd.butter_fat
            totals.cocoa_butter_pct += bd.cocoa_butter
            totals.cocoa_pct += bd.cocoa
            totals.amp_pct += bd.amp
            totals.lactose_pct += bd.lactose
            totals.other_solids_pct += bd.other_solids
            totals.water_pct += bd.water
            totals.alcohol_pct += bd.alcohol
            totals.total_cost += bd.cost

        # Grouped totals
        totals.total_sugars_pct = totals.sugar_pct
        totals.total_fats_pct = totals.oil_pct + totals.butter_fat_pct + totals.cocoa_butter_pct
        totals.total_dry_matter_pct = (
            totals.cocoa_pct + totals.amp_pct + totals.lactose_pct + totals.other_solids_pct
        )
        totals.total_liquids_pct = totals.water_pct + totals.alcohol_pct

        # Technical totals (weighted by quantity, divided by total weight)
        total_pod = sum(bd.pod for bd in analysis.breakdowns)
        total_pac = sum(bd.pac for bd in analysis.breakdowns)
        total_kcal = sum(bd.kcal for bd in analysis.breakdowns)

        totals.pod = total_pod / (total_g / 100.0) if total_g > 0 else 0.0
        totals.pac = total_pac / (total_g / 100.0) if total_g > 0 else 0.0
        totals.kcal_per_100g = total_kcal / (total_g / 100.0) if total_g > 0 else 0.0

        return analysis

    def get_ingredient(self, ingredient_id: str) -> Optional[IngredientProfile]:
        """Look up an ingredient by id."""
        return self._db.get(ingredient_id)
