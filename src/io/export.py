"""CSV export for recipes."""
from __future__ import annotations

import csv
import io
from typing import TextIO

from src.engine.calculator import RecipeAnalysis


class CSVExporter:
    """Exports recipe analysis to CSV format."""

    @staticmethod
    def export(analysis: RecipeAnalysis, file_or_path) -> None:
        """Export recipe analysis to a CSV file or file-like object.

        Args:
            analysis: The calculated recipe analysis.
            file_or_path: A file path (str) or writable file-like object.
        """
        if isinstance(file_or_path, str):
            with open(file_or_path, "w", encoding="utf-8", newline="") as f:
                CSVExporter._write(analysis, f)
        else:
            CSVExporter._write(analysis, file_or_path)

    @staticmethod
    def _write(analysis: RecipeAnalysis, f: TextIO) -> None:
        writer = csv.writer(f, delimiter=";")

        # Header
        writer.writerow([
            "Ingrediente", "Cantidad (g)", "% Total",
            "Azúcar %", "Aceite %", "Mantequilla %", "M. Cacao %",
            "Cacao %", "AMP %", "Lactosa %", "Otro %",
            "Agua %", "Alcohol %",
            "POD", "PAC", "Kcal", "Coste (€)",
        ])

        # Rows
        for bd in analysis.breakdowns:
            writer.writerow([
                bd.name,
                f"{bd.quantity_g:.1f}",
                f"{bd.percentage:.1f}",
                f"{bd.sugar:.1f}",
                f"{bd.oil:.1f}",
                f"{bd.butter_fat:.1f}",
                f"{bd.cocoa_butter:.1f}",
                f"{bd.cocoa:.1f}",
                f"{bd.amp:.1f}",
                f"{bd.lactose:.1f}",
                f"{bd.other_solids:.1f}",
                f"{bd.water:.1f}",
                f"{bd.alcohol:.1f}",
                f"{bd.pod:.1f}",
                f"{bd.pac:.1f}",
                f"{bd.kcal:.1f}",
                f"{bd.cost:.2f}",
            ])

        # Separator
        writer.writerow([])

        # Totals
        t = analysis.totals
        writer.writerow([
            "TOTALES",
            f"{t.total_weight_g:.1f}",
            "100.0",
            f"{t.sugar_pct:.1f}",
            f"{t.oil_pct:.1f}",
            f"{t.butter_fat_pct:.1f}",
            f"{t.cocoa_butter_pct:.1f}",
            f"{t.cocoa_pct:.1f}",
            f"{t.amp_pct:.1f}",
            f"{t.lactose_pct:.1f}",
            f"{t.other_solids_pct:.1f}",
            f"{t.water_pct:.1f}",
            f"{t.alcohol_pct:.1f}",
            f"{t.pod:.1f}",
            f"{t.pac:.1f}",
            f"{t.kcal_per_100g:.1f}",
            f"{t.total_cost:.2f}",
        ])

        # Grouped summary
        writer.writerow([])
        writer.writerow(["RESUMEN"])
        writer.writerow(["Azúcares totales", f"{t.total_sugars_pct:.1f}%"])
        writer.writerow(["Grasas totales", f"{t.total_fats_pct:.1f}%"])
        writer.writerow(["Materia seca", f"{t.total_dry_matter_pct:.1f}%"])
        writer.writerow(["Líquidos", f"{t.total_liquids_pct:.1f}%"])
        writer.writerow(["POD", f"{t.pod:.1f}"])
        writer.writerow(["PAC", f"{t.pac:.1f}"])
        writer.writerow(["Kcal/100g", f"{t.kcal_per_100g:.1f}"])
        writer.writerow(["Coste total", f"{t.total_cost:.2f} €"])

    @staticmethod
    def to_string(analysis: RecipeAnalysis) -> str:
        """Export recipe analysis to a CSV string."""
        buf = io.StringIO()
        CSVExporter.export(analysis, buf)
        return buf.getvalue()
