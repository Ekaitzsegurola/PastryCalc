"""Recipe validation engine.

Validates recipe totals against category ideal ranges.
Produces a traffic-light result (green/orange/red) per metric.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.models.category import RecipeCategory, RangeSpec
from src.engine.calculator import RecipeTotals


class ValidationLevel(Enum):
    """Traffic light validation levels."""
    GREEN = "green"    # Within range
    ORANGE = "orange"  # Near the edge (within 10% of range span)
    RED = "red"        # Out of range


@dataclass
class MetricValidation:
    """Validation result for a single metric."""

    metric_name: str
    display_name: str
    value: float
    ideal_range: Optional[RangeSpec]
    level: ValidationLevel = ValidationLevel.GREEN
    message: str = ""

    @property
    def is_ok(self) -> bool:
        return self.level == ValidationLevel.GREEN


@dataclass
class ValidationResult:
    """Full validation result for a recipe."""

    category_name: str = ""
    metrics: list[MetricValidation] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """True if all metrics are green."""
        return all(m.is_ok for m in self.metrics)

    @property
    def has_warnings(self) -> bool:
        """True if any metric is orange."""
        return any(m.level == ValidationLevel.ORANGE for m in self.metrics)

    @property
    def has_errors(self) -> bool:
        """True if any metric is red."""
        return any(m.level == ValidationLevel.RED for m in self.metrics)


# Recommendation templates
_RECOMMENDATIONS = {
    "sugar": {
        "high": "Azúcares demasiado altos: reduzca azúcar o aumente otros ingredientes.",
        "low": "Azúcares demasiado bajos: añada más edulcorantes o aumente su proporción.",
    },
    "fat": {
        "high": "Grasas demasiado altas: reduzca mantequilla/nata o aumente líquidos.",
        "low": "Grasas demasiado bajas: añada más grasa (mantequilla, chocolate, nata).",
    },
    "dry_matter": {
        "high": "Materia seca excesiva: reduzca cacao/leche en polvo o añada líquidos.",
        "low": "Materia seca insuficiente: añada leche en polvo, cacao u otros sólidos.",
    },
    "liquid": {
        "high": "Demasiado líquido: reduzca nata/leche o aumente sólidos.",
        "low": "Líquidos insuficientes: añada más nata, leche o agua.",
    },
    "pod": {
        "high": "POD demasiado alto: use edulcorantes con menor poder endulzante (glucosa, dextrosa).",
        "low": "POD demasiado bajo: use edulcorantes con mayor poder endulzante (fructosa, invertido).",
    },
    "pac": {
        "high": "PAC demasiado alto: reduzca alcoholes o edulcorantes con alto PAC.",
        "low": "PAC demasiado bajo: añada dextrosa, sorbitol o alcohol para mejorar textura.",
    },
}


class RecipeValidator:
    """Validates recipe totals against category ideal ranges."""

    def validate(self, totals: RecipeTotals, category: Optional[RecipeCategory]) -> ValidationResult:
        """Validate recipe totals against a category.

        Returns a ValidationResult with per-metric traffic lights and recommendations.
        If category is None, returns an empty result (no validation possible).
        """
        result = ValidationResult()

        if category is None:
            result.category_name = "(sin categoría)"
            return result

        result.category_name = category.name

        # Define metrics to validate
        checks = [
            ("sugar", "Azúcares", totals.total_sugars_pct, category.sugar_range),
            ("fat", "Grasas", totals.total_fats_pct, category.fat_range),
            ("dry_matter", "Materia seca", totals.total_dry_matter_pct, category.dry_matter_range),
            ("liquid", "Líquidos", totals.total_liquids_pct, category.liquid_range),
            ("pod", "POD", totals.pod, category.pod_range),
            ("pac", "PAC", totals.pac, category.pac_range),
        ]

        for metric_key, display_name, value, ideal_range in checks:
            mv = self._validate_metric(metric_key, display_name, value, ideal_range)
            result.metrics.append(mv)
            if not mv.is_ok and mv.message:
                result.recommendations.append(mv.message)

        return result

    def _validate_metric(
        self,
        metric_key: str,
        display_name: str,
        value: float,
        ideal_range: Optional[RangeSpec],
    ) -> MetricValidation:
        """Validate a single metric against its ideal range."""
        mv = MetricValidation(
            metric_name=metric_key,
            display_name=display_name,
            value=value,
            ideal_range=ideal_range,
        )

        if ideal_range is None:
            # No range defined for this metric in this category
            mv.level = ValidationLevel.GREEN
            mv.message = ""
            return mv

        if ideal_range.contains(value):
            mv.level = ValidationLevel.GREEN
            mv.message = ""
        elif ideal_range.is_near(value, tolerance_pct=15.0):
            mv.level = ValidationLevel.ORANGE
            if value < ideal_range.min_val:
                mv.message = _RECOMMENDATIONS.get(metric_key, {}).get(
                    "low", f"{display_name} ligeramente bajo."
                )
            else:
                mv.message = _RECOMMENDATIONS.get(metric_key, {}).get(
                    "high", f"{display_name} ligeramente alto."
                )
        else:
            mv.level = ValidationLevel.RED
            if value < ideal_range.min_val:
                mv.message = _RECOMMENDATIONS.get(metric_key, {}).get(
                    "low", f"{display_name} fuera de rango (bajo)."
                )
            else:
                mv.message = _RECOMMENDATIONS.get(metric_key, {}).get(
                    "high", f"{display_name} fuera de rango (alto)."
                )

        return mv
