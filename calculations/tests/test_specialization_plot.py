"""Stale optional figures must be rejected without importing plotting packages."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc import specialization_plot


class PlotProvenanceTests(unittest.TestCase):
    def test_optional_absence(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(specialization_plot,'PROJECT',Path(directory)):
                self.assertEqual(specialization_plot.verify(),{'verified_figures':0})

    def test_source_and_figure_mutations_are_rejected(self):
        for changed in ('source.json','figure.svg'):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);target=root/'figures/specialization';target.mkdir(parents=True)
                for name in ('source.json','figure.svg'):(root/name).write_text('original')
                def entry(name):
                    return dict(file=name,sha256=hashlib.sha256((root/name).read_bytes()).hexdigest())
                (target/'manifest.json').write_text(json.dumps(dict(inputs=[entry('source.json')],artifacts=[entry('figure.svg')])))
                with patch.object(specialization_plot,'PROJECT',root):
                    self.assertEqual(specialization_plot.verify()['verified_figures'],1)
                    (root/changed).write_text('changed')
                    with self.assertRaises(ValueError):specialization_plot.verify()
