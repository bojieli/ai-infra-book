"""Reader discovery must include component models and tolerate non-model sources."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.cli import model_list, parser


class ModelCatalogTests(unittest.TestCase):
    def test_component_models_and_audio_roots_are_discoverable(self):
        rows = {row['model']: row for row in model_list()}
        for name in ('minimax-h3', 'qwen-image-2512', 'flux2-klein-4b'):
            self.assertEqual(rows[name]['config_layout'], 'components')
            self.assertTrue(rows[name]['stage_calculations'])
            self.assertGreater(len(rows[name]['component_configs']), 1)
        for name in ('qwen3-omni-30b-a3b-instruct', 'fish-audio-s2-pro'):
            self.assertEqual(rows[name]['config_layout'], 'root')
            self.assertTrue(rows[name]['stage_calculations'])
        for row in rows.values():
            for command in row['stage_calculations']:
                self.assertEqual(parser().parse_args([command]).command, command)
        self.assertEqual(rows['llama3.1-70b']['config'], 'unavailable')
        self.assertEqual(rows['llama3.1-70b']['forward'], 'pending')
        self.assertNotIn('hardware', rows)
        self.assertEqual(rows['deepseek-v3']['base_forward_ledger'], 'v3-forward')
