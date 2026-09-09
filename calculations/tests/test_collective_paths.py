"""Book link counts, independent BFS distances and directed-byte conservation."""
from collections import deque,Counter
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.collective_paths import calculate,shortest_path


class CollectivePathTests(unittest.TestCase):
    def test_book_counts(self):
        r=calculate();a,b=r['collective_path_patterns']
        self.assertEqual(r['summary']['enumerated_messages'],96)
        self.assertEqual([x['peak_link_messages'] for x in a['rounds']],[1,2,4])
        self.assertEqual([x['peak_link_messages'] for x in b['rounds']],[1,1,2])
        self.assertEqual([x['physical_link_bytes']//2**20 for x in a['rounds']],[64,64,64])
        self.assertEqual([x['physical_link_bytes']//2**20 for x in b['rounds']],[64,32,48])
        self.assertEqual(a['injected_bytes'],b['injected_bytes'])
        self.assertEqual(a['injected_bytes'],112*2**20)
        self.assertIsNone(r['summary']['full_all_reduce_seconds'])

    def test_bfs_paths_and_byte_conservation(self):
        for pattern in calculate()['collective_path_patterns']:
            for row in pattern['rounds']:
                counts=Counter()
                for route in row['routes']:
                    sender,receiver=route['sender'],route['receiver']
                    queue=deque([(sender,0)]);seen={sender}
                    while queue:
                        node,distance=queue.popleft()
                        if node==receiver:break
                        for nxt in ((node+1)%16,(node-1)%16):
                            if nxt not in seen:seen.add(nxt);queue.append((nxt,distance+1))
                    self.assertEqual(len(route['path']),distance)
                    current=sender
                    for a,b in route['path']:
                        self.assertEqual(a,current);current=b
                        self.assertIn((b-a)%16,(1,15))
                        counts[f'{a}->{b}']+=row['message_bytes']
                    self.assertEqual(current,receiver)
                self.assertEqual(dict(counts),row['directed_link_bytes'])
                self.assertEqual(sum(counts.values()),row['physical_link_bytes'])
                self.assertEqual(max(counts.values()),row['peak_link_bytes'])

    def test_scaling_and_scope_rejection(self):
        base=calculate();small=calculate(tokens=1);slow=calculate(bandwidth_bytes_per_second=25*10**9)
        for key in ('recursive_prefix_lower_seconds','swing_prefix_lower_seconds'):
            self.assertEqual(slow['summary'][key],2*base['summary'][key])
            self.assertEqual(small['summary'][key]*1024,base['summary'][key])
        with self.assertRaises(ValueError):calculate(rounds=4)
        with self.assertRaises(ValueError):shortest_path(0,8)
