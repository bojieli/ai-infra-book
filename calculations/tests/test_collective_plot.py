"""Every plot arrow retains direction, zero load and source-accounted bytes."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.collective_plot import panels
from infra_calc.topics.collective_paths import calculate


class CollectivePlotTests(unittest.TestCase):
    def test_complete_directed_edge_table(self):
        result=calculate();data=panels(result)
        self.assertEqual(len(data),6)
        for panel in data:
            self.assertEqual(len(panel['edges']),32)
            pairs={(e['sender'],e['receiver']) for e in panel['edges']}
            self.assertEqual(len(pairs),32)
            self.assertTrue(all((b,a) in pairs for a,b in pairs))
            self.assertEqual(sum(e['bytes'] for e in panel['edges']),panel['physical_link_bytes'])
            self.assertEqual(max(e['bytes'] for e in panel['edges']),panel['peak_link_bytes'])
        self.assertEqual(sum(e['bytes']==0 for e in data[0]['edges']),16)

    def test_rank_zero_route_matches_original_events(self):
        result=calculate();data=panels(result)
        for panel in data:
            source=next(p for p in result['collective_path_patterns'] if p['pattern']==panel['pattern'])['rounds'][panel['round']]
            route=next(r for r in source['routes'] if r['sender']==0)
            self.assertEqual(panel['rank_zero_path'][0],0)
            self.assertEqual(panel['rank_zero_path'][-1],route['receiver'])
            self.assertEqual(list(zip(panel['rank_zero_path'],panel['rank_zero_path'][1:])),[tuple(e) for e in route['path']])
