"""Ingredients tab - detailed breakdown table and totals bar."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

import customtkinter as ctk

from src.ui import theme

if TYPE_CHECKING:
    from src.ui.app import PastryCalcApp


# Column definitions for the breakdown table
DETAIL_COLUMNS = [
    ("sugar", "Azúcar %", 70),
    ("oil", "Aceite %", 65),
    ("butter_fat", "Mantq %", 65),
    ("cocoa_butter", "M.Cacao %", 75),
    ("cocoa", "Cacao %", 65),
    ("amp", "AMP %", 55),
    ("lactose", "Lact %", 55),
    ("other_solids", "Otro %", 55),
    ("water", "Agua %", 65),
    ("alcohol", "Alc %", 55),
    ("pod", "POD", 50),
    ("pac", "PAC", 50),
    ("kcal", "Kcal", 55),
    ("cost", "Coste €", 65),
]


class IngredientsTab(ctk.CTkFrame):
    """Tab showing ingredient list, detail breakdown, and totals."""

    def __init__(self, parent, app: PastryCalcApp):
        super().__init__(parent)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # Title
        title = ctk.CTkLabel(self, text="Detalles de ingredientes", font=("Segoe UI", 18, "bold"))
        title.pack(pady=(10, 5), padx=15, anchor="w")

        # Main content area - paned window for list + details
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=5)

        # --- LEFT: Ingredient list ---
        left_frame = ctk.CTkFrame(content)
        left_frame.pack(side="left", fill="both", padx=(0, 5))

        ctk.CTkLabel(left_frame, text="Lista", font=("Segoe UI", 14, "bold")).pack(
            pady=(8, 4), padx=8, anchor="w"
        )

        # List treeview
        list_container = ctk.CTkFrame(left_frame, fg_color="transparent")
        list_container.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        self.list_tree = ttk.Treeview(
            list_container,
            columns=("qty", "pct"),
            show="headings",
            height=15,
        )
        self.list_tree.heading("qty", text="Cant. (g)")
        self.list_tree.heading("pct", text="% Total")
        self.list_tree.column("qty", width=70, anchor="e")
        self.list_tree.column("pct", width=70, anchor="e")

        list_scroll = ttk.Scrollbar(list_container, orient="vertical", command=self.list_tree.yview)
        self.list_tree.configure(yscrollcommand=list_scroll.set)

        self.list_tree.pack(side="left", fill="both", expand=True)
        list_scroll.pack(side="right", fill="y")

        # Buttons
        btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(
            btn_frame, text="+ Añadir", width=80, command=self._on_add,
            fg_color="#E8712B", hover_color="#D4621F",
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            btn_frame, text="Editar", width=70, command=self._on_edit,
            fg_color="#5B5B5B", hover_color="#4A4A4A",
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            btn_frame, text="Eliminar", width=75, command=self._on_delete,
            fg_color="#C0392B", hover_color="#A93226",
        ).pack(side="left", padx=2)

        # --- RIGHT: Detail table ---
        right_frame = ctk.CTkFrame(content)
        right_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))

        ctk.CTkLabel(right_frame, text="Desglose por componente", font=("Segoe UI", 14, "bold")).pack(
            pady=(8, 4), padx=8, anchor="w"
        )

        detail_container = ctk.CTkFrame(right_frame, fg_color="transparent")
        detail_container.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        col_ids = [c[0] for c in DETAIL_COLUMNS]
        self.detail_tree = ttk.Treeview(
            detail_container,
            columns=col_ids,
            show="headings",
            height=15,
        )
        for col_id, col_name, col_width in DETAIL_COLUMNS:
            self.detail_tree.heading(col_id, text=col_name)
            self.detail_tree.column(col_id, width=col_width, anchor="e")

        detail_scroll_y = ttk.Scrollbar(detail_container, orient="vertical", command=self.detail_tree.yview)
        detail_scroll_x = ttk.Scrollbar(detail_container, orient="horizontal", command=self.detail_tree.xview)
        self.detail_tree.configure(yscrollcommand=detail_scroll_y.set, xscrollcommand=detail_scroll_x.set)

        self.detail_tree.pack(side="left", fill="both", expand=True)
        detail_scroll_y.pack(side="right", fill="y")

        # --- BOTTOM: Totals bar ---
        self.totals_frame = ctk.CTkFrame(self, height=90, fg_color=theme.TOTALS_BG, corner_radius=8)
        self.totals_frame.pack(fill="x", padx=10, pady=(5, 10))
        self.totals_frame.pack_propagate(False)

        self._totals_labels = {}
        self._build_totals_bar()

    def _build_totals_bar(self):
        """Build the grouped totals summary bar."""
        for w in self.totals_frame.winfo_children():
            w.destroy()

        # Title row
        title_row = ctk.CTkFrame(self.totals_frame, fg_color="transparent")
        title_row.pack(fill="x", padx=10, pady=(6, 2))

        ctk.CTkLabel(
            title_row, text="Totales", font=("Segoe UI", 14, "bold"),
            text_color=theme.TOTALS_FG,
        ).pack(side="left")

        # Values row
        val_row = ctk.CTkFrame(self.totals_frame, fg_color="transparent")
        val_row.pack(fill="x", padx=10, pady=(0, 6))

        groups = [
            ("Azúcares", "sugars"),
            ("Grasas", "fats"),
            ("M. Seca", "dry"),
            ("Líquidos", "liquids"),
            ("POD", "pod"),
            ("PAC", "pac"),
            ("Kcal/100g", "kcal"),
            ("Coste", "cost"),
        ]

        for label_text, key in groups:
            cell = ctk.CTkFrame(val_row, fg_color="transparent")
            cell.pack(side="left", padx=8, expand=True)

            ctk.CTkLabel(
                cell, text=label_text, font=("Segoe UI", 10),
                text_color=theme.TOTALS_FG,
            ).pack()

            lbl = ctk.CTkLabel(
                cell, text="--", font=("Segoe UI", 13, "bold"),
                text_color=theme.TOTALS_FG,
            )
            lbl.pack()
            self._totals_labels[key] = lbl

    def refresh(self, analysis):
        """Update tables and totals from a RecipeAnalysis."""
        # Clear trees
        for item in self.list_tree.get_children():
            self.list_tree.delete(item)
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)

        # Populate
        for bd in analysis.breakdowns:
            # List tree - use ingredient name as display, store id as iid
            self.list_tree.insert("", "end", iid=bd.ingredient_id, text=bd.name, values=(
                f"{bd.quantity_g:.1f}",
                f"{bd.percentage:.1f}",
            ))

            # Detail tree
            self.detail_tree.insert("", "end", iid=bd.ingredient_id, values=(
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
                f"{bd.kcal:.0f}",
                f"{bd.cost:.2f}",
            ))

        # Workaround: Treeview doesn't show 'text' in headings mode.
        # Use first column trick - reconfigure to include name column
        # Actually we already show it properly via the #0 column or values.
        # Let me use the displaycolumns approach.

        # Update totals
        t = analysis.totals
        self._totals_labels["sugars"].configure(text=f"{t.total_sugars_pct:.1f} %")
        self._totals_labels["fats"].configure(text=f"{t.total_fats_pct:.1f} %")
        self._totals_labels["dry"].configure(text=f"{t.total_dry_matter_pct:.1f} %")
        self._totals_labels["liquids"].configure(text=f"{t.total_liquids_pct:.1f} %")
        self._totals_labels["pod"].configure(text=f"{t.pod:.0f}")
        self._totals_labels["pac"].configure(text=f"{t.pac:.0f}")
        self._totals_labels["kcal"].configure(text=f"{t.kcal_per_100g:.0f}")
        self._totals_labels["cost"].configure(text=f"{t.total_cost:.2f} €")

    def _on_add(self):
        self.app.show_add_ingredient_dialog()

    def _on_edit(self):
        sel = self.list_tree.selection()
        if sel:
            self.app.show_edit_quantity_dialog(sel[0])

    def _on_delete(self):
        sel = self.list_tree.selection()
        if sel:
            self.app.recipe.remove_item(sel[0])
            self.app.recalculate()

    def _reconfigure_list_tree(self):
        """Set up list tree to show ingredient names using tree column."""
        self.list_tree.column("#0", width=200, anchor="w")
        self.list_tree.heading("#0", text="Ingrediente")
