"""PastryCalc - Professional Pastry Recipe Calculator.

Entry point for the application.
"""
import sys
import os

# Ensure the project root is in the path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)


def main():
    """Launch the PastryCalc application."""
    from src.ui.app import PastryCalcApp

    app = PastryCalcApp()
    app.mainloop()


if __name__ == "__main__":
    main()
