import html
import re
import unittest
from outline_text import rendered_inline


class VisibleTextTests(unittest.TestCase):
    def test_checkpoint_formula_preserves_multiplication(self):
        source = '`E=(exp(lambda*(tau+c))-1)*(1/lambda+r)`'
        actual_html = '<code>E=(exp(lambda*(tau+c))-1)*(1/lambda+r)</code>'
        actual_visible = html.unescape(re.sub(r'<[^>]+>', '', actual_html))
        self.assertEqual(rendered_inline(source), actual_visible)
        self.assertNotEqual(rendered_inline(source), actual_visible.replace('*', ''))

    def test_formatting_and_link_labels(self):
        self.assertEqual(rendered_inline('**记录**：[结果](../results.md)，`a*b` &amp; c*d'),
                         '记录：结果，a*b & c*d')

    def test_literal_asterisks_are_not_unconditionally_removed(self):
        self.assertEqual(rendered_inline('f(*args, **kwargs)'), 'f(*args, **kwargs)')


if __name__ == '__main__':
    unittest.main()
