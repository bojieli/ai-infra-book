from pathlib import Path
import tempfile
import unittest
from prepare import prepare,P

class PrepareTests(unittest.TestCase):
    def test_tasks_sources_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'job';m=prepare(out)
            self.assertEqual(m['status'],'prepared, not executed')
            self.assertEqual(m['distinct_tasks'],8)
            for name in ('run.py','probe.py'):
                self.assertEqual((out/name).read_bytes(),(P/'sources/kv-quality'/name).read_bytes())
            self.assertNotIn('prompt_token_ids',(out/'expected-tasks.json').read_text())
            with self.assertRaises(ValueError):prepare(out)

if __name__=='__main__':unittest.main()
