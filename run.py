#!/usr/bin/env python3
"""Development launcher for PastryCalc."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.main import main

if __name__ == "__main__":
    main()
