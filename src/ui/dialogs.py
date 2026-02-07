"""Dialog windows for adding/editing ingredients."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Optional
from collections import defaultdict

import customtkinter as ctk

from src.ui import theme

if TYPE_CHECKING:
    from src.ui.app import PastryCalcApp


# Group display order and icons
_GROUP_ORDER = [
    "Azúcares",
    "Lácteos",
    "Chocolate y Cacao",
    "Grasas",
    "Huevos",
    "Frutas y Purés",
    "Alcoholes",
    "Estabilizantes y Otros",
]


def _build_detail_panel(parent, ing) -> ctk.CTkFrame:
    """Build a structured detail panel for an ingredient (GanacheSolution style).

    Shows composition in grouped sections: Azúcares, Grasas, Materia seca,
    Líquidos, Otro (POD/PAC/Kcal/KJ).
    """
    frame = ctk.CTkFrame(parent, fg_color="transparent")

    # --- Azúcares ---
    _section(frame, "Azúcares", [
        ("Sacarosa (%)", f"{ing.sugar_pct:.1f}"),
    ])

    # --- Grasas ---
    _section(frame, "Grasas", [
        ("Aceite (%)", f"{ing.oil_pct:.1f}"),
        ("Mantequilla (%)", f"{ing.butter_fat_pct:.1f}"),
        ("Manteca de cacao (%)", f"{ing.cocoa_butter_pct:.1f}"),
    ])

    # --- Materia seca ---
    _section(frame, "Materia seca", [
        ("Sólidos de cacao (%)", f"{ing.cocoa_pct:.1f}"),
        ("L.M.P.D (%)", f"{ing.amp_pct:.1f}"),
        ("Lactosa (%)", f"{ing.lactose_pct:.1f}"),
        ("Otros sólidos (%)", f"{ing.other_solids_pct:.1f}"),
    ])

    # --- Líquidos ---
    _section(frame, "Líquidos", [
        ("Agua (%)", f"{ing.water_pct:.1f}"),
        ("Alcohol (%)", f"{ing.alcohol_pct:.1f}"),
    ])

    # --- Otro (POD, PAC, Kcal, KJ) ---
    kj = ing.kcal_per_100g * 4.184
    _section(frame, "Otro", [
        ("POD (poder endulzante)", f"{ing.pod:.0f}"),
        ("PAC (poder anticongelante)", f"{ing.pac:.0f}"),
        ("Kcal", f"{ing.kcal_per_100g:.0f}"),
        ("KJ", f"{kj:.0f}"),
    ])

    # Total + Cost
    total_frame = ctk.CTkFrame(frame, fg_color=theme.TOTALS_BG, corner_radius=6)
    total_frame.pack(fill="x", padx=5, pady=(8, 2))
    row = ctk.CTkFrame(total_frame, fg_color="transparent")
    row.pack(fill="x", padx=8, pady=4)
    ctk.CTkLabel(row, text="Total composición:", font=("Segoe UI", 11, "bold"),
                 text_color=theme.TOTALS_FG).pack(side="left")
    ctk.CTkLabel(row, text=f"{ing.component_sum:.1f} %", font=("Segoe UI", 11, "bold"),
                 text_color=theme.TOTALS_FG).pack(side="right")
    row2 = ctk.CTkFrame(total_frame, fg_color="transparent")
    row2.pack(fill="x", padx=8, pady=(0, 4))
    ctk.CTkLabel(row2, text="Coste:", font=("Segoe UI", 11),
                 text_color=theme.TOTALS_FG).pack(side="left")
    ctk.CTkLabel(row2, text=f"{ing.cost_per_kg:.2f} €/kg", font=("Segoe UI", 11),
                 text_color=theme.TOTALS_FG).pack(side="right")

    return frame


def _section(parent, title: str, fields: list[tuple[str, str]]):
    """Build a section header + field grid (like GanacheSolution's Calculadora de datos)."""
    sec = ctk.CTkFrame(parent)
    sec.pack(fill="x", padx=5, pady=(6, 0))

    header = ctk.CTkFrame(sec, fg_color=theme.ACCENT, corner_radius=4, height=24)
    header.pack(fill="x")
    header.pack_propagate(False)
    ctk.CTkLabel(header, text=f"  {title}", font=("Segoe UI", 11, "bold"),
                 text_color="white").pack(side="left", padx=4)

    grid = ctk.CTkFrame(sec, fg_color="transparent")
    grid.pack(fill="x", padx=4, pady=2)

    for col, (label, value) in enumerate(fields):
        cell = ctk.CTkFrame(grid, fg_color="transparent")
        cell.pack(side="left", padx=6, pady=1, expand=True)
        ctk.CTkLabel(cell, text=label, font=("Segoe UI", 9),
                     text_color="gray").pack(anchor="w")
        val_frame = ctk.CTkFrame(cell, fg_color="#E8E8E8", corner_radius=4, height=26)
        val_frame.pack(fill="x")
        val_frame.pack_propagate(False)
        ctk.CTkLabel(val_frame, text=value, font=("Segoe UI", 11)).pack(
            padx=6, expand=True)


class AddIngredientDialog(ctk.CTkToplevel):
    """Dialog for adding an ingredient to the recipe.

    Shows ingredients grouped by category (Azúcares, Lácteos, etc.)
    with a detail panel showing composition on selection.
    """

    def __init__(self, parent, app: PastryCalcApp):
        super().__init__(parent)
        self.app = app
        self.result: Optional[tuple[str, float]] = None
        self.title("Añadir ingrediente")
        self.geometry("900x600")
        self.resizable(True, True)
        self.minsize(750, 500)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._populate_tree()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 900) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 600) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _build_ui(self):
        # Top bar: search
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(top, text="Seleccionar ingrediente", font=("Segoe UI", 16, "bold")).pack(
            side="left"
        )

        search_box = ctk.CTkFrame(top, fg_color="transparent")
        search_box.pack(side="right")
        ctk.CTkLabel(search_box, text="Buscar:").pack(side="left", padx=(0, 5))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        ctk.CTkEntry(search_box, textvariable=self.search_var, width=220).pack(side="left")

        # Main area: tree on left, detail on right
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=10, pady=5)

        # --- LEFT: Grouped tree ---
        left = ctk.CTkFrame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))

        tree_container = ctk.CTkFrame(left, fg_color="transparent")
        tree_container.pack(fill="both", expand=True, padx=5, pady=5)

        self.ing_tree = ttk.Treeview(
            tree_container, columns=("fat", "sugar", "water"),
            show="tree headings", height=18,
        )
        self.ing_tree.heading("#0", text="Ingrediente / Grupo")
        self.ing_tree.heading("fat", text="Grasa %")
        self.ing_tree.heading("sugar", text="Azúcar %")
        self.ing_tree.heading("water", text="Agua %")
        self.ing_tree.column("#0", width=250, anchor="w")
        self.ing_tree.column("fat", width=65, anchor="e")
        self.ing_tree.column("sugar", width=65, anchor="e")
        self.ing_tree.column("water", width=65, anchor="e")

        scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.ing_tree.yview)
        self.ing_tree.configure(yscrollcommand=scroll.set)
        self.ing_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.ing_tree.bind("<<TreeviewSelect>>", self._on_select)

        # --- RIGHT: Detail panel ---
        self.detail_frame = ctk.CTkScrollableFrame(main, width=350, label_text="Calculadora de datos")
        self.detail_frame.pack(side="right", fill="both", padx=(5, 0))

        self._detail_placeholder = ctk.CTkLabel(
            self.detail_frame, text="Selecciona un ingrediente\npara ver su composición",
            font=("Segoe UI", 12), text_color="gray",
        )
        self._detail_placeholder.pack(pady=40)

        # Bottom: Quantity + buttons
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=15, pady=(5, 12))

        ctk.CTkLabel(bottom, text="Cantidad (g):").pack(side="left", padx=(0, 5))
        self.qty_var = ctk.StringVar(value="100")
        qty_entry = ctk.CTkEntry(bottom, textvariable=self.qty_var, width=100)
        qty_entry.pack(side="left")

        ctk.CTkButton(
            bottom, text="Añadir", width=100, command=self._on_add,
            fg_color="#E8712B", hover_color="#D4621F",
        ).pack(side="right", padx=5)
        ctk.CTkButton(
            bottom, text="Cancelar", width=100, command=self.destroy,
            fg_color="#5B5B5B", hover_color="#4A4A4A",
        ).pack(side="right", padx=5)

    def _populate_tree(self, filter_text: str = ""):
        """Populate tree with ingredients grouped by category."""
        for item in self.ing_tree.get_children():
            self.ing_tree.delete(item)

        ft = filter_text.lower()

        # Group ingredients
        groups: dict[str, list] = defaultdict(list)
        for ing_id, ing in self.app.ingredients.items():
            if ft and ft not in ing.name.lower() and ft not in ing.group.lower():
                continue
            groups[ing.group].append((ing_id, ing))

        # Insert in display order
        ordered_groups = []
        for g in _GROUP_ORDER:
            if g in groups:
                ordered_groups.append((g, groups.pop(g)))
        # Any remaining groups not in the predefined order
        for g, items in sorted(groups.items()):
            ordered_groups.append((g, items))

        for group_name, items in ordered_groups:
            # Create group node (use a safe iid)
            group_iid = f"__group__{group_name}"
            self.ing_tree.insert(
                "", "end", iid=group_iid, text=f"  {group_name}  ({len(items)})",
                values=("", "", ""), open=True,
                tags=("group",),
            )
            # Insert ingredients under group
            for ing_id, ing in sorted(items, key=lambda x: x[1].name):
                self.ing_tree.insert(
                    group_iid, "end", iid=ing_id, text=ing.name,
                    values=(
                        f"{ing.total_fat_pct:.1f}",
                        f"{ing.sugar_pct:.1f}",
                        f"{ing.water_pct:.1f}",
                    ),
                )

        # Style group rows
        self.ing_tree.tag_configure("group", font=("Segoe UI", 11, "bold"))

    def _on_search(self, *args):
        self._populate_tree(self.search_var.get())

    def _on_select(self, event):
        sel = self.ing_tree.selection()
        if not sel:
            return
        ing_id = sel[0]

        # Ignore group node selection
        if ing_id.startswith("__group__"):
            return

        ing = self.app.ingredients.get(ing_id)
        if not ing:
            return

        # Clear detail panel
        for w in self.detail_frame.winfo_children():
            w.destroy()

        # Header
        ctk.CTkLabel(
            self.detail_frame, text=ing.name,
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(5, 2), padx=5, anchor="w")
        ctk.CTkLabel(
            self.detail_frame, text=f"Grupo: {ing.group}",
            font=("Segoe UI", 10), text_color="gray",
        ).pack(padx=5, anchor="w")

        # Build structured detail
        panel = _build_detail_panel(self.detail_frame, ing)
        panel.pack(fill="x", pady=(5, 5))

    def _on_add(self):
        sel = self.ing_tree.selection()
        if not sel or sel[0].startswith("__group__"):
            return
        try:
            qty = float(self.qty_var.get())
            if qty <= 0:
                return
        except ValueError:
            return

        self.result = (sel[0], qty)
        self.app.recipe.add_item(sel[0], qty)
        self.app.recalculate()
        self.destroy()


class EditQuantityDialog(ctk.CTkToplevel):
    """Dialog for editing the quantity of an ingredient."""

    def __init__(self, parent, app: PastryCalcApp, ingredient_id: str):
        super().__init__(parent)
        self.app = app
        self.ingredient_id = ingredient_id
        self.title("Editar cantidad")
        self.geometry("350x180")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        ing = app.ingredients.get(ingredient_id)
        name = ing.name if ing else ingredient_id

        # Find current quantity
        current_qty = 0.0
        for item in app.recipe.items:
            if item.ingredient_id == ingredient_id:
                current_qty = item.quantity_g
                break

        self._build_ui(name, current_qty)

        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 350) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 180) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _build_ui(self, name: str, current_qty: float):
        ctk.CTkLabel(self, text=f"Ingrediente: {name}", font=("Segoe UI", 13, "bold")).pack(
            pady=(15, 5), padx=15, anchor="w"
        )

        qty_frame = ctk.CTkFrame(self, fg_color="transparent")
        qty_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(qty_frame, text="Cantidad (g):").pack(side="left", padx=(0, 10))
        self.qty_var = ctk.StringVar(value=f"{current_qty:.1f}")
        entry = ctk.CTkEntry(qty_frame, textvariable=self.qty_var, width=120)
        entry.pack(side="left")
        entry.select_range(0, "end")
        entry.focus()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(5, 15))

        ctk.CTkButton(
            btn_frame, text="Guardar", width=100, command=self._on_save,
            fg_color="#E8712B", hover_color="#D4621F",
        ).pack(side="right", padx=5)
        ctk.CTkButton(
            btn_frame, text="Cancelar", width=100, command=self.destroy,
            fg_color="#5B5B5B", hover_color="#4A4A4A",
        ).pack(side="right", padx=5)

    def _on_save(self):
        try:
            qty = float(self.qty_var.get())
            if qty <= 0:
                return
        except ValueError:
            return

        self.app.recipe.update_quantity(self.ingredient_id, qty)
        self.app.recalculate()
        self.destroy()


class ManageIngredientsDialog(ctk.CTkToplevel):
    """Dialog for managing the ingredient database.

    Shows ingredients grouped by category with a GanacheSolution-style
    detail panel (Calculadora de datos) on the right.
    """

    def __init__(self, parent, app: PastryCalcApp):
        super().__init__(parent)
        self.app = app
        self.title("Gestionar ingredientes")
        self.geometry("950x600")
        self.minsize(800, 500)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._populate()

        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 950) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 600) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _build_ui(self):
        # Left: grouped tree
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(
            list_frame, columns=("fat", "sugar", "sum"),
            show="tree headings", height=20,
        )
        self.tree.heading("#0", text="Ingrediente / Grupo")
        self.tree.heading("fat", text="Grasa %")
        self.tree.heading("sugar", text="Azúcar %")
        self.tree.heading("sum", text="Total %")
        self.tree.column("#0", width=260)
        self.tree.column("fat", width=65, anchor="e")
        self.tree.column("sugar", width=65, anchor="e")
        self.tree.column("sum", width=65, anchor="e")

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Right: detail panel (scrollable)
        self.detail_frame = ctk.CTkScrollableFrame(self, width=370, label_text="Calculadora de datos")
        self.detail_frame.pack(side="right", fill="both", padx=(0, 10), pady=10)

        self._detail_placeholder = ctk.CTkLabel(
            self.detail_frame, text="Selecciona un ingrediente\npara ver su composición",
            font=("Segoe UI", 12), text_color="gray",
        )
        self._detail_placeholder.pack(pady=60)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _populate(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        groups: dict[str, list] = defaultdict(list)
        for ing_id, ing in self.app.ingredients.items():
            groups[ing.group].append((ing_id, ing))

        ordered_groups = []
        for g in _GROUP_ORDER:
            if g in groups:
                ordered_groups.append((g, groups.pop(g)))
        for g, items in sorted(groups.items()):
            ordered_groups.append((g, items))

        for group_name, items in ordered_groups:
            group_iid = f"__group__{group_name}"
            self.tree.insert(
                "", "end", iid=group_iid,
                text=f"  {group_name}  ({len(items)})",
                values=("", "", ""), open=False,
                tags=("group",),
            )
            for ing_id, ing in sorted(items, key=lambda x: x[1].name):
                self.tree.insert(
                    group_iid, "end", iid=ing_id, text=ing.name,
                    values=(
                        f"{ing.total_fat_pct:.1f}",
                        f"{ing.sugar_pct:.1f}",
                        f"{ing.component_sum:.1f}",
                    ),
                )

        self.tree.tag_configure("group", font=("Segoe UI", 11, "bold"))

    def _on_select(self, event):
        sel = self.tree.selection()
        if not sel or sel[0].startswith("__group__"):
            return
        ing = self.app.ingredients.get(sel[0])
        if not ing:
            return

        for w in self.detail_frame.winfo_children():
            w.destroy()

        # Header
        ctk.CTkLabel(
            self.detail_frame, text=ing.name,
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(5, 2), padx=5, anchor="w")
        ctk.CTkLabel(
            self.detail_frame, text=f"Grupo: {ing.group}",
            font=("Segoe UI", 10), text_color="gray",
        ).pack(padx=5, anchor="w")

        panel = _build_detail_panel(self.detail_frame, ing)
        panel.pack(fill="x", pady=(5, 5))
