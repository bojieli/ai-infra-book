"""Finite-grid nonnegative least-squares diagnostics, including zero faces.

This does not replace the positive-law compute-optimum API. Exponents are
selected only on fit observations; holdout losses never affect selection.
"""
import itertools
import math


def least_squares(columns, targets):
    """Small modified Gram-Schmidt QR; dependent active faces are rejected."""
    q, upper = [], [[0.0] * len(columns) for _ in columns]
    for j, column in enumerate(columns):
        vector = list(column)
        original = math.sqrt(sum(x*x for x in vector))
        for i, basis in enumerate(q):
            upper[i][j] = sum(x*y for x, y in zip(basis, vector))
            vector = [x-upper[i][j]*y for x, y in zip(vector, basis)]
        norm = math.sqrt(sum(x*x for x in vector))
        if norm <= 1e-10 * original:
            raise ValueError('dependent or ill-conditioned active columns')
        upper[j][j] = norm
        q.append([x/norm for x in vector])
    rhs = [sum(x*y for x, y in zip(column, targets)) for column in q]
    coefficients = [0.0] * len(columns)
    for i in reversed(range(len(columns))):
        coefficients[i] = (rhs[i]-sum(upper[i][j]*coefficients[j] for j in range(i+1, len(columns))))/upper[i][i]
    return coefficients


def nonnegative_fit(rows, targets):
    """Enumerate all eight E/A/B faces; each accepted face is a feasible fit."""
    columns = list(zip(*rows))
    candidates = []
    for size in range(4):
        for active in itertools.combinations(range(3), size):
            try:
                local = least_squares([columns[i] for i in active], targets)
            except ValueError:
                continue
            if any(value < 0 for value in local):
                continue
            values = [0.0] * 3
            for index, value in zip(active, local):
                values[index] = value
            residuals = [sum(x*y for x, y in zip(row, values))-target for row, target in zip(rows, targets)]
            candidates.append(dict(coefficients=values, active_columns=list(active), sse=sum(x*x for x in residuals)))
    return min(candidates, key=lambda row: row['sse'])


def fit(records, exponent_grid, N0=1e9, D0=1e10):
    """Rows require id/N/D/loss/split/control_id; one declared control only."""
    if not records or not exponent_grid:
        raise ValueError('Records and exponent grid required')
    def positive(value):
        return type(value) in (int, float) and math.isfinite(value) and value > 0
    if not positive(N0) or not positive(D0):
        raise ValueError('Positive finite reference scales required')
    identities, controls = set(), set()
    for row in records:
        if not isinstance(row['id'], str) or not row['id'] or row['id'] in identities:
            raise ValueError('Unique nonempty record IDs required')
        identities.add(row['id'])
        if not isinstance(row['control_id'], str) or not row['control_id']:
            raise ValueError('Declared control required')
        controls.add(row['control_id'])
        if row['split'] not in ('fit', 'holdout') or not all(positive(row[key]) for key in ('N', 'D', 'loss')):
            raise ValueError('Invalid split or numeric record')
    train = [row for row in records if row['split'] == 'fit']
    held = [row for row in records if row['split'] == 'holdout']
    if len(controls) != 1 or len(train) < 4 or not held:
        raise ValueError('One control, four fit records and a held-out model set required')
    candidates = []
    for alpha, beta in exponent_grid:
        if not positive(alpha) or not positive(beta):
            raise ValueError('Positive finite exponents required')
        design = [[1.0, (row['N']/N0)**(-alpha), (row['D']/D0)**(-beta)] for row in train]
        targets = [row['loss'] for row in train]
        try:
            least_squares(list(zip(*design)), targets)
            dependent = False
        except ValueError:
            dependent = True
        result = nonnegative_fit(design, targets)
        candidates.append(dict(result, alpha=alpha, beta=beta, full_design_rank_deficient=dependent))
    best = min(candidates, key=lambda row: row['sse'])
    E, A, B = best['coefficients']
    predictions = []
    for row in records:
        prediction = E + A*(row['N']/N0)**(-best['alpha']) + B*(row['D']/D0)**(-best['beta'])
        predictions.append(dict(row, prediction=prediction, residual=prediction-row['loss']))
    return dict(law=dict(E=E, A=A, B=B, alpha=best['alpha'], beta=best['beta'], N0=N0, D0=D0),
                fit_sse=best['sse'], predictions=predictions, candidates=candidates,
                holdout_rmse=math.sqrt(sum(row['residual']**2 for row in predictions if row['split']=='holdout')/len(held)),
                zero_coefficients=[name for name, value in zip(('E','A','B'), (E,A,B)) if value == 0],
                compute_optimum_eligible=A > 0 and B > 0,
                full_design_rank_deficient=best["full_design_rank_deficient"],
                exponent_identifiability=dict(alpha=False if A == 0 else None, beta=False if B == 0 else None),
                fit_coordinate_counts=dict(N=len({r["N"] for r in train}), D=len({r["D"] for r in train})),
                scope=['Finite-grid constrained regression diagnostic, not proof of a universal scaling law or generalization.',
                       'Zero A or B removes dependence on its exponent; a grid tie does not identify that exponent.',
                       'Same control is an input assertion; a held-out model split is not evidence that evaluation documents were held out of training.',
                       'compute_optimum_eligible only checks positive A/B formula domain; it does not establish reliable exponents, extrapolation, or fit identifiability.',
                       'No confidence interval, noise weighting, or synthetic observations are inferred. All real residuals remain visible.'])
