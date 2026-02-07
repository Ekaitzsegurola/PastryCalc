"""Analysis tab - composition bars, traffic lights, and recommendations."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

import customtkinter as ctk

from src.ui import theme
from src.engine.validator import ValidationResult, ValidationLevel

if TYPE_CHECKING:
    from src.ui.app import PastryCalcApp


_LEVEL_COLORS = {
    ValidationLevel.GREEN: theme.GREEN,
    ValidationLevel.ORANGE: theme.ORANGE,
    ValidationLevel.RED: theme.RED,
}


class AnalysisTab(ctk.CTkFrame):
    """Tab for recipe analysis - bars, traffic lights, recommendations."""

    def __init__(self, parent, app: PastryCalcApp):
        super().__init__(parent)
        self.app = app
        self._metric_widgets = {}
        self._build_ui()

    def _build_ui(self):
        # Title
        title = ctk.CTkLabel(self, text="Análisis de la receta", font=("Segoe UI", 18, "bold"))
        title.pack(pady=(15, 5), padx=20, anchor="w")

        self.category_label = ctk.CTkLabel(
            self, text="Categoría: --", font=("Segoe UI", 13)
        )
        self.category_label.pack(pady=(0, 10), padx=20, anchor="w")

        # Metrics frame
        self.metrics_frame = ctk.CTkFrame(self)
        self.metrics_frame.pack(fill="x", padx=20, pady=5)

        # Build metric rows (will be populated on refresh)
        metrics = [
            ("Azúcares", "sugar"),
            ("Grasas", "fat"),
            ("Materia seca", "dry_matter"),
            ("Líquidos", "liquid"),
            ("POD", "pod"),
            ("PAC", "pac"),
        ]

        for i, (display_name, key) in enumerate(metrics):
            row = ctk.CTkFrame(self.metrics_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=4)
            row.columnconfigure(2, weight=1)

            # Traffic light circle
            light_label = ctk.CTkLabel(
                row, text=" \u25cf ", font=("Segoe UI", 16),
                text_color=theme.GRAY, width=30,
            )
            light_label.grid(row=0, column=0, padx=(0, 5))

            # Metric name
            name_label = ctk.CTkLabel(
                row, text=display_name, font=("Segoe UI", 12, "bold"), width=120, anchor="w"
            )
            name_label.grid(row=0, column=1, padx=5, sticky="w")

            # Progress bar (shows value vs range)
            bar_frame = ctk.CTkFrame(row, fg_color="transparent", height=22)
            bar_frame.grid(row=0, column=2, padx=5, sticky="ew")
            bar_frame.columnconfigure(0, weight=1)

            bar = ctk.CTkProgressBar(bar_frame, height=16, width=300)
            bar.grid(row=0, column=0, sticky="ew")
            bar.set(0)

            # Value label
            val_label = ctk.CTkLabel(
                row, text="-- %", font=("Segoe UI", 12), width=90, anchor="e"
            )
            val_label.grid(row=0, column=3, padx=5)

            # Range label
            range_label = ctk.CTkLabel(
                row, text="", font=("Segoe UI", 10), width=120, anchor="w",
                text_color=theme.GRAY,
            )
            range_label.grid(row=0, column=4, padx=5)

            self._metric_widgets[key] = {
                "light": light_label,
                "bar": bar,
                "value": val_label,
                "range": range_label,
            }

        # Recommendations section
        rec_label = ctk.CTkLabel(
            self, text="Recomendaciones", font=("Segoe UI", 14, "bold")
        )
        rec_label.pack(pady=(15, 5), padx=20, anchor="w")

        self.rec_text = ctk.CTkTextbox(self, height=150)
        self.rec_text.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def refresh(self, validation: ValidationResult):
        """Update display from a ValidationResult."""
        self.category_label.configure(text=f"Categoría: {validation.category_name}")

        for mv in validation.metrics:
            widgets = self._metric_widgets.get(mv.metric_name)
            if not widgets:
                continue

            color = _LEVEL_COLORS.get(mv.level, theme.GRAY)
            widgets["light"].configure(text_color=color)

            # Value display
            if mv.metric_name in ("pod", "pac"):
                widgets["value"].configure(text=f"{mv.value:.0f}")
            else:
                widgets["value"].configure(text=f"{mv.value:.1f} %")

            # Range display
            if mv.ideal_range:
                if mv.metric_name in ("pod", "pac"):
                    widgets["range"].configure(
                        text=f"({mv.ideal_range.min_val:.0f} - {mv.ideal_range.max_val:.0f})"
                    )
                else:
                    widgets["range"].configure(
                        text=f"({mv.ideal_range.min_val:.0f} - {mv.ideal_range.max_val:.0f} %)"
                    )
            else:
                widgets["range"].configure(text="(sin rango)")

            # Progress bar (normalize to range)
            if mv.ideal_range:
                range_center = (mv.ideal_range.min_val + mv.ideal_range.max_val) / 2.0
                range_span = mv.ideal_range.max_val - mv.ideal_range.min_val
                if range_span > 0:
                    # Normalize: 0.5 = center of ideal range
                    normalized = 0.5 + (mv.value - range_center) / (range_span * 2)
                    normalized = max(0.0, min(1.0, normalized))
                else:
                    normalized = 0.5
                widgets["bar"].set(normalized)
                widgets["bar"].configure(progress_color=color)
            else:
                widgets["bar"].set(0)

        # Recommendations
        self.rec_text.delete("1.0", "end")
        if validation.recommendations:
            for rec in validation.recommendations:
                self.rec_text.insert("end", f"\u2022 {rec}\n")
        elif validation.is_valid:
            self.rec_text.insert("end", "\u2714 La receta está dentro de los rangos ideales para esta categoría.")
        else:
            self.rec_text.insert("end", "Selecciona una categoría en la pestaña Receta para ver el análisis.")
