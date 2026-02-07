"""Dialog windows for adding/editing ingredients."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk

if TYPE_CHECKING:
    from src.ui.app import PastryCalcApp


class AddIngredientDialog(ctk.CTkToplevel):
    """Dialog for adding an ingredient to the recipe."""

    def __init__(self, parent, app: PastryCalcApp):
        super().__init__(parent)
        self.app = app
        self.result: Optional[tuple[str, float]] = None
        self.title("Añadir ingrediente")
        self.geometry("500x450")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._populate_list()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 450) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        ctk.CTkLabel(self, text="Seleccionar ingrediente", font=("Segoe UI", 14, "bold")).pack(
            pady=(15, 5), padx=15, anchor="w"
        )

        # Search
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(search_frame, text="Buscar:").pack(side="left", padx=(0, 5))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        ctk.CTkEntry(search_frame, textvariable=self.search_var, width=300).pack(side="left", fill="x", expand=True)

        # Ingredient list
        list_frame = ctk.CTkFrame(self, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.ing_tree = ttk.Treeview(
            list_frame, columns=("group",), show="headings", height=12,
        )
        self.ing_tree.heading("#0", text="Ingrediente")
        self.ing_tree.heading("group", text="Grupo")
        self.ing_tree.column("group", width=120)

        # Show tree column
        self.ing_tree["displaycolumns"] = ("group",)
        self.ing_tree.column("#0", width=280)
        self.ing_tree["show"] = ("tree", "headings")

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.ing_tree.yview)
        self.ing_tree.configure(yscrollcommand=scroll.set)
        self.ing_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Quantity
        qty_frame = ctk.CTkFrame(self, fg_color="transparent")
        qty_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(qty_frame, text="Cantidad (g):").pack(side="left", padx=(0, 5))
        self.qty_var = ctk.StringVar(value="100")
        ctk.CTkEntry(qty_frame, textvariable=self.qty_var, width=100).pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(5, 15))

        ctk.CTkButton(
            btn_frame, text="Añadir", width=100, command=self._on_add,
            fg_color="#E8712B", hover_color="#D4621F",
        ).pack(side="right", padx=5)
        ctk.CTkButton(
            btn_frame, text="Cancelar", width=100, command=self.destroy,
            fg_color="#5B5B5B", hover_color="#4A4A4A",
        ).pack(side="right", padx=5)

    def _populate_list(self, filter_text: str = ""):
        for item in self.ing_tree.get_children():
            self.ing_tree.delete(item)

        ft = filter_text.lower()
        for ing_id, ing in self.app.ingredients.items():
            if ft and ft not in ing.name.lower() and ft not in ing.group.lower():
                continue
            self.ing_tree.insert("", "end", iid=ing_id, text=ing.name, values=(ing.group,))

    def _on_search(self, *args):
        self._populate_list(self.search_var.get())

    def _on_add(self):
        sel = self.ing_tree.selection()
        if not sel:
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
        self.geometry(f"+{x}+{y}")

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
    """Dialog for managing the ingredient database (CRUD)."""

    def __init__(self, parent, app: PastryCalcApp):
        super().__init__(parent)
        self.app = app
        self.title("Gestionar ingredientes")
        self.geometry("800x500")
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._populate()

        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 800) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 500) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        # List
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(
            list_frame, columns=("group", "sum"), show="tree headings", height=18,
        )
        self.tree.heading("#0", text="Nombre")
        self.tree.heading("group", text="Grupo")
        self.tree.heading("sum", text="Sum %")
        self.tree.column("#0", width=250)
        self.tree.column("group", width=120)
        self.tree.column("sum", width=60, anchor="e")

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Info panel
        info_frame = ctk.CTkFrame(self, width=250)
        info_frame.pack(side="right", fill="y", padx=10, pady=10)
        info_frame.pack_propagate(False)

        ctk.CTkLabel(info_frame, text="Info del ingrediente", font=("Segoe UI", 13, "bold")).pack(
            pady=10
        )

        self.info_text = ctk.CTkTextbox(info_frame, height=350, width=230)
        self.info_text.pack(padx=5, fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _populate(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for ing_id, ing in sorted(self.app.ingredients.items(), key=lambda x: (x[1].group, x[1].name)):
            self.tree.insert("", "end", iid=ing_id, text=ing.name, values=(
                ing.group,
                f"{ing.component_sum:.1f}",
            ))

    def _on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        ing = self.app.ingredients.get(sel[0])
        if not ing:
            return

        self.info_text.delete("1.0", "end")
        lines = [
            f"ID: {ing.id}",
            f"Nombre: {ing.name}",
            f"Grupo: {ing.group}",
            "",
            "--- Composición ---",
            f"Azúcar: {ing.sugar_pct:.1f}%",
            f"Aceite: {ing.oil_pct:.1f}%",
            f"Grasa láctea: {ing.butter_fat_pct:.1f}%",
            f"M. cacao: {ing.cocoa_butter_pct:.1f}%",
            f"Cacao: {ing.cocoa_pct:.1f}%",
            f"AMP: {ing.amp_pct:.1f}%",
            f"Lactosa: {ing.lactose_pct:.1f}%",
            f"Otros: {ing.other_solids_pct:.1f}%",
            f"Agua: {ing.water_pct:.1f}%",
            f"Alcohol: {ing.alcohol_pct:.1f}%",
            f"  TOTAL: {ing.component_sum:.1f}%",
            "",
            "--- Técnico ---",
            f"POD: {ing.pod:.0f}",
            f"PAC: {ing.pac:.0f}",
            f"Kcal/100g: {ing.kcal_per_100g:.0f}",
            f"Coste/kg: {ing.cost_per_kg:.2f} €",
        ]
        self.info_text.insert("end", "\n".join(lines))
