"""Recipe metadata tab - name, category, status, author, notes."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    from src.ui.app import PastryCalcApp


class RecipeTab(ctk.CTkFrame):
    """Tab for editing recipe metadata."""

    def __init__(self, parent, app: PastryCalcApp):
        super().__init__(parent)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # Title
        title = ctk.CTkLabel(self, text="Editar receta", font=("Segoe UI", 18, "bold"))
        title.pack(pady=(15, 10), padx=20, anchor="w")

        # Form frame
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=20, pady=5)

        # Row 1: Name, Category, Status
        row1 = ctk.CTkFrame(form, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=5)
        row1.columnconfigure(1, weight=2)
        row1.columnconfigure(3, weight=1)
        row1.columnconfigure(5, weight=1)

        ctk.CTkLabel(row1, text="Nombre:").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.name_var = ctk.StringVar(value="Nueva receta")
        self.name_entry = ctk.CTkEntry(row1, textvariable=self.name_var, width=300)
        self.name_entry.grid(row=0, column=1, padx=5, sticky="ew")

        ctk.CTkLabel(row1, text="Categoría:").grid(row=0, column=2, padx=(15, 5), sticky="w")
        self.category_var = ctk.StringVar(value="")
        self.category_combo = ctk.CTkComboBox(
            row1,
            variable=self.category_var,
            values=[],
            width=200,
            command=self._on_category_changed,
        )
        self.category_combo.grid(row=0, column=3, padx=5, sticky="ew")

        ctk.CTkLabel(row1, text="Estatus:").grid(row=0, column=4, padx=(15, 5), sticky="w")
        self.status_var = ctk.StringVar(value="Borrador")
        self.status_combo = ctk.CTkComboBox(
            row1,
            variable=self.status_var,
            values=["Borrador", "Confirmada", "Prueba"],
            width=140,
        )
        self.status_combo.grid(row=0, column=5, padx=5, sticky="ew")

        # Row 2: Author, Origin
        row2 = ctk.CTkFrame(form, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=5)
        row2.columnconfigure(1, weight=1)
        row2.columnconfigure(3, weight=1)

        ctk.CTkLabel(row2, text="Autor:").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.author_var = ctk.StringVar(value="")
        ctk.CTkEntry(row2, textvariable=self.author_var, width=200).grid(
            row=0, column=1, padx=5, sticky="ew"
        )

        ctk.CTkLabel(row2, text="Origen:").grid(row=0, column=2, padx=(15, 5), sticky="w")
        self.origin_var = ctk.StringVar(value="")
        ctk.CTkEntry(row2, textvariable=self.origin_var, width=200).grid(
            row=0, column=3, padx=5, sticky="ew"
        )

        # Row 3: Scale
        row3 = ctk.CTkFrame(form, fg_color="transparent")
        row3.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(row3, text="Ajustar receta a (g):").pack(side="left", padx=(0, 5))
        self.scale_var = ctk.StringVar(value="")
        ctk.CTkEntry(row3, textvariable=self.scale_var, width=100).pack(side="left", padx=5)
        ctk.CTkButton(
            row3, text="Ajustar", width=80, command=self._on_scale,
            fg_color="#E8712B", hover_color="#D4621F"
        ).pack(side="left", padx=5)

        # Notes
        notes_frame = ctk.CTkFrame(self)
        notes_frame.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(notes_frame, text="Notas:", font=("Segoe UI", 14, "bold")).pack(
            pady=(10, 5), padx=10, anchor="w"
        )
        self.notes_text = ctk.CTkTextbox(notes_frame, height=200)
        self.notes_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def set_categories(self, category_names: list[tuple[str, str]]):
        """Set available categories. Each item is (id, display_name)."""
        self._category_map = {name: cid for cid, name in category_names}
        self.category_combo.configure(values=[""] + [name for _, name in category_names])

    def _on_category_changed(self, value):
        """Handle category selection change."""
        cat_id = self._category_map.get(value, "")
        self.app.recipe.category_id = cat_id
        self.app.recalculate()

    def _on_scale(self):
        """Scale recipe to target weight."""
        try:
            target = float(self.scale_var.get())
            if target > 0:
                self.app.recipe.scale_to_weight(target)
                self.app.refresh_all()
        except ValueError:
            pass

    def load_recipe(self, recipe):
        """Populate fields from a Recipe object."""
        self.name_var.set(recipe.name)
        self.status_var.set(recipe.status)
        self.author_var.set(recipe.author)
        self.origin_var.set(recipe.origin)

        # Find category display name
        for cat_id, cat in self.app.categories.items():
            if cat_id == recipe.category_id:
                self.category_var.set(cat.name)
                break
        else:
            self.category_var.set("")

        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", recipe.notes)

    def save_to_recipe(self, recipe):
        """Update a Recipe object from the form fields."""
        recipe.name = self.name_var.get()
        recipe.category_id = self._category_map.get(self.category_var.get(), "")
        recipe.status = self.status_var.get()
        recipe.author = self.author_var.get()
        recipe.origin = self.origin_var.get()
        recipe.notes = self.notes_text.get("1.0", "end").strip()
