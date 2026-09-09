import unittest
from posterior_semantic import extract

class ExtractTests(unittest.TestCase):
 def test_terminal_supported_forms(self):
  for text in ['{"count":8}', 'Explanation\n{"count":8}', 'Explanation\n```json\n{"count":8}\n```', 'Explanation\n```\n{"count":8}\n```']:
   with self.subTest(text=text):self.assertEqual(extract(text)[0],8)
 def test_ambiguity_and_wrong_schema_rejected(self):
  for text in ['{"count":8}\n{"count":5}', '{"count":8,"count":5}', '{"count":true}', '{"count":8,"other":1}', '{"count":{"count":8}}', '{"count":8}\nConclusion', '<think>still reasoning {"count":8}', '```python\n{"count":8}\n```']:
   with self.subTest(text=text):self.assertIsNone(extract(text)[0])
if __name__=='__main__':unittest.main()
