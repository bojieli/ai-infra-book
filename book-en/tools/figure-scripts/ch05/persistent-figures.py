#!/usr/bin/env python3
"""Re-render the English §5.5.4 timelines from the chapter's current figure data.

The translated full_teaching_revision.py draws every figure in that module; only
the two persistent-kernel timelines changed, so only those are copied.
"""
from pathlib import Path
import json, shutil, sys, tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(HERE.parent), str(ROOT/'manuscripts'), str(ROOT/'book-en/tools')]

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from figure_style.typography import configure_font
import figure_style_fitted
sys.modules['figure_style'] = figure_style_fitted
import types
# The V4.1 case figures in the same module are unchanged and resolve paths from
# their own location; skip them here.
sys.modules['v41_case_figures'] = types.SimpleNamespace(draw=lambda *a, **k: None)
from full_teaching_revision import draw

NAMES = ('figure-5-15-persistent', 'figure-5-persistent-blocks')

if __name__ == '__main__':
    _, family = configure_font()
    plt.rcParams.update({'font.family': [family, 'DejaVu Sans'], 'svg.fonttype': 'path'})
    data = json.loads((ROOT/'manuscripts/ch05/figure-data.json').read_text())
    with tempfile.TemporaryDirectory() as tmp:
        draw(Path(tmp), data)
        for name in NAMES:
            shutil.copy2(Path(tmp)/f'{name}.pdf', ROOT/'book-en/images'/f'{name}.pdf')
            print(f'book-en/images/{name}.pdf')
