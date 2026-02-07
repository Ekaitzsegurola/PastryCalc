"""Main PastryCalc application window."""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk

from src.models.ingredient import IngredientProfile
from src.models.recipe import Recipe
from src.models.category import RecipeCategory
from src.engine.calculator import RecipeCalculator, RecipeAnalysis
from src.engine.validator import RecipeValidator, ValidationResult
from src.io.file_manager import FileManager
from src.io.export import CSVExporter
from src.ui.recipe_tab import RecipeTab
from src.ui.ingredients_tab import IngredientsTab
from src.ui.analysis_tab import AnalysisTab
from src.ui import theme


class PastryCalcApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("PastryCalc - Calculadora de Pastelería")
        self.geometry("1200x750")
        self.minsize(900, 600)

        # Configure appearance
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Data
        self.ingredients: dict[str, IngredientProfile] = {}
        self.categories: dict[str, RecipeCategory] = {}
        self.recipe = Recipe()
        self.calculator: Optional[RecipeCalculator] = None
        self.validator = RecipeValidator()
        self._current_analysis: Optional[RecipeAnalysis] = None
        self._current_validation: Optional[ValidationResult] = None
        self._current_file: Optional[str] = None

        # Load data
        self._load_data()

        # Build UI
        self._build_menu()
        self._build_tabs()

        # Initialize
        self._init_recipe_tab()
        self.recalculate()

    def _load_data(self):
        """Load ingredients and categories from JSON files."""
        try:
            self.ingredients = FileManager.load_ingredients()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los ingredientes:\n{e}")
            self.ingredients = {}

        try:
            self.categories = FileManager.load_categories()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las categorías:\n{e}")
            self.categories = {}

        self.calculator = RecipeCalculator(self.ingredients)

    def _build_menu(self):
        """Build the application menu bar."""
        menubar = tk.Menu(self)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Nueva receta", command=self._new_recipe, accelerator="Ctrl+N")
        file_menu.add_command(label="Abrir receta...", command=self._open_recipe, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Guardar", command=self._save_recipe, accelerator="Ctrl+S")
        file_menu.add_command(label="Guardar como...", command=self._save_recipe_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exportar CSV...", command=self._export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        # Ingredients menu
        ing_menu = tk.Menu(menubar, tearoff=0)
        ing_menu.add_command(label="Ver base de datos...", command=self._show_manage_ingredients)
        menubar.add_cascade(label="Ingredientes", menu=ing_menu)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Tema oscuro", command=lambda: ctk.set_appearance_mode("dark"))
        view_menu.add_command(label="Tema claro", command=lambda: ctk.set_appearance_mode("light"))
        menubar.add_cascade(label="Ver", menu=view_menu)

        self.config(menu=menubar)

        # Keyboard shortcuts
        self.bind("<Control-n>", lambda e: self._new_recipe())
        self.bind("<Control-o>", lambda e: self._open_recipe())
        self.bind("<Control-s>", lambda e: self._save_recipe())

    def _build_tabs(self):
        """Build the tabbed interface."""
        self.tabview = ctk.CTkTabview(self, anchor="nw")
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs
        self.tabview.add("Receta")
        self.tabview.add("Ingredientes")
        self.tabview.add("Análisis")

        # Initialize tab contents
        self.recipe_tab = RecipeTab(self.tabview.tab("Receta"), self)
        self.recipe_tab.pack(fill="both", expand=True)

        self.ingredients_tab = IngredientsTab(self.tabview.tab("Ingredientes"), self)
        self.ingredients_tab.pack(fill="both", expand=True)

        self.analysis_tab = AnalysisTab(self.tabview.tab("Análisis"), self)
        self.analysis_tab.pack(fill="both", expand=True)

        # Configure list tree to show names
        self.ingredients_tab._reconfigure_list_tree()

    def _init_recipe_tab(self):
        """Initialize recipe tab with category list."""
        cat_list = [(cid, cat.name) for cid, cat in self.categories.items()]
        self.recipe_tab.set_categories(cat_list)

    def recalculate(self):
        """Recalculate recipe analysis and update all views."""
        if not self.calculator:
            return

        self._current_analysis = self.calculator.calculate(self.recipe)

        # Validate
        category = self.categories.get(self.recipe.category_id)
        self._current_validation = self.validator.validate(
            self._current_analysis.totals, category
        )

        # Update views
        self.ingredients_tab.refresh(self._current_analysis)
        self.analysis_tab.refresh(self._current_validation)

    def refresh_all(self):
        """Refresh all tabs from the current recipe."""
        self.recipe_tab.load_recipe(self.recipe)
        self.recalculate()

    # --- Dialog triggers ---

    def show_add_ingredient_dialog(self):
        from src.ui.dialogs import AddIngredientDialog
        AddIngredientDialog(self, self)

    def show_edit_quantity_dialog(self, ingredient_id: str):
        from src.ui.dialogs import EditQuantityDialog
        EditQuantityDialog(self, self, ingredient_id)

    def _show_manage_ingredients(self):
        from src.ui.dialogs import ManageIngredientsDialog
        ManageIngredientsDialog(self, self)

    # --- File operations ---

    def _new_recipe(self):
        self.recipe = Recipe()
        self._current_file = None
        self.refresh_all()
        self.title("PastryCalc - Nueva receta")

    def _open_recipe(self):
        path = filedialog.askopenfilename(
            title="Abrir receta",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.recipe = FileManager.load_recipe(path)
            self._current_file = path
            self.refresh_all()
            self.title(f"PastryCalc - {self.recipe.name}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la receta:\n{e}")

    def _save_recipe(self):
        if self._current_file:
            self._do_save(self._current_file)
        else:
            self._save_recipe_as()

    def _save_recipe_as(self):
        path = filedialog.asksaveasfilename(
            title="Guardar receta",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        self._do_save(path)

    def _do_save(self, path: str):
        self.recipe_tab.save_to_recipe(self.recipe)
        try:
            FileManager.save_recipe(self.recipe, path)
            self._current_file = path
            self.title(f"PastryCalc - {self.recipe.name}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    def _export_csv(self):
        if not self._current_analysis:
            messagebox.showinfo("Info", "No hay datos para exportar. Añade ingredientes primero.")
            return
        path = filedialog.asksaveasfilename(
            title="Exportar CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            CSVExporter.export(self._current_analysis, path)
            messagebox.showinfo("Exportado", f"CSV exportado correctamente a:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar:\n{e}")
