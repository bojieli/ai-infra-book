"""Resolve data relative to the checkout, never to the caller's working directory."""
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
BOOK = PROJECT.parent
