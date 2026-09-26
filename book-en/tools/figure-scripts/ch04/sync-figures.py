#!/usr/bin/env python3
"""Render the English L2, cross-SM handoff and sync-cost figures with the Chinese geometry."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT/'manuscripts'), str(ROOT/'manuscripts/ch04'), str(ROOT/'book-en/tools')]

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from figure_style.typography import configure_font
import figure_style_fitted
sys.modules['figure_style'] = figure_style_fitted  # English labels are wider: fit, never clip
from figure_style_fitted import Exporter
from sync_figures import draw

if __name__ == '__main__':
    _, family = configure_font()
    plt.rcParams.update({'font.family': [family, 'DejaVu Sans'], 'svg.fonttype': 'path', 'svg.hashsalt': 'chapter04-sync-en'})
    out = Exporter(ROOT/'book-en/images')
    draw(out, ROOT, english=True)
    for path in out.outputs:
        print(path.relative_to(ROOT))
