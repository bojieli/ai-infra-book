import copy
import random
import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from infra_calc.topics.scaling_boundary_fit import fit, nonnegative_fit, least_squares, NumericalRangeError


class BoundaryTests(unittest.TestCase):
    def test_large_representable_holdout_rmse(self):
        records = [dict(id=str(i), N=(i+1)*1e9, D=(i+1)*1e10,
                        loss=3. if i<4 else 1e308,
                        split='fit' if i<4 else 'holdout', control_id='one') for i in range(8)]
        self.assertEqual(fit(records,[(.2,.3)])['holdout_rmse'], 1e308)

    def test_scaled_qr_large_representable_column(self):
        coefficient = least_squares([[1e200, 2e200, 3e200]], [1., 2., 3.])[0]
        self.assertAlmostEqual(coefficient / 1e-200, 1.)

    def test_unrepresentable_grid_does_not_stop_valid_candidate(self):
        records = [dict(id=str(i), N=n, D=d, loss=2+i*.1,
                        split='fit', control_id='one')
                   for i, (n,d) in enumerate(((1e-100,1), (2e-100,2), (3e-100,1), (4e-100,2)))]
        records.append(dict(records[0], id='held', split='holdout'))
        result = fit(records, [(10., .5), (.1, .5)], 1., 1.)
        self.assertEqual(result['law']['alpha'], .1)
        self.assertEqual(result['rejected_candidates'][0]['category'], 'numeric_range')

    def test_sse_overflow_never_returns_infinity(self):
        records = [dict(id=str(i), N=1., D=1., loss=loss,
                        split='fit', control_id='one')
                   for i, loss in enumerate((1e200,2e200,1e200,2e200))]
        records.append(dict(records[0], id='held', split='holdout'))
        with self.assertRaises(NumericalRangeError):
            fit(records,[(.2,.3)],1.,1.)

    def test_negative_data_slope_reaches_boundary(self):
        rows = [[1., n, d] for n in (1., 2., 3.) for d in (1., 2., 3.)]
        targets = [2 + 3*n - .2*d for _, n, d in rows]
        result = nonnegative_fit(rows, targets)
        self.assertEqual(result['coefficients'][2], 0)
        self.assertAlmostEqual(result['coefficients'][0], 1.6)
        self.assertAlmostEqual(result['coefficients'][1], 3.)

    def test_holdout_cannot_select_grid(self):
        records = [dict(id=str(i), N=n, D=d, loss=1+2/n**.3+3/d**.4,
                        control_id='declared', split='fit')
                   for i, (n, d) in enumerate(( (1,1), (1,4), (4,1), (4,4), (2,3) ))]
        records.append(dict(id='held', N=8, D=8, loss=9, control_id='declared', split='holdout'))
        first = fit(records, [(.2,.2),(.3,.4)], 1, 1)
        changed = copy.deepcopy(records)
        changed[-1]['loss'] = 999
        second = fit(changed, [(.2,.2),(.3,.4)], 1, 1)
        self.assertEqual(first['law'], second['law'])
        self.assertEqual(first['fit_sse'], second['fit_sse'])
        self.assertNotEqual(first['holdout_rmse'], second['holdout_rmse'])
        self.assertAlmostEqual(first['law']['A'], 2)

    def test_dependent_design_reports_feasible_face(self):
        rows = [[1, x, 2] for x in (1,2,3,4)]
        result = nonnegative_fit(rows, [5+2*x for x in (1,2,3,4)])
        self.assertLess(result['sse'], 1e-20)

    def test_against_independent_scipy_nnls(self):
        try:
            import numpy as np
            from scipy.optimize import nnls
        except ImportError:
            self.skipTest("Independent NNLS oracle requires optional SciPy")
        rng = random.Random(309)
        for _ in range(40):
            rows = [[1., rng.uniform(.1,3), rng.uniform(.1,3)] for _ in range(12)]
            targets = [rng.uniform(.1,4) for _ in rows]
            actual = nonnegative_fit(rows, targets)
            expected, norm = nnls(np.asarray(rows), np.asarray(targets))
            self.assertAlmostEqual(actual['sse'], norm*norm, places=10)
            for a, b in zip(actual['coefficients'], expected):
                self.assertAlmostEqual(a, b, places=10)


if __name__ == '__main__':
    unittest.main()
