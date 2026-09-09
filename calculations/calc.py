#!/usr/bin/env python3
"""Run from a checkout without installing packages: python3 calculations/calc.py."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from infra_calc.cli import main

if __name__ == "__main__":
    main()
