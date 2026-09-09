"""Finite-grid nonnegative least-squares diagnostics, including zero faces.

This does not replace the positive-law compute-optimum API. Exponents are
selected only on fit observations; holdout losses never affect selection.
"""
import itertools
import json
import math


class NumericalRangeError(ValueError):
    """An intermediate or reported result is not representable as a finite float."""


class RankDeficientError(ValueError):
    """Active columns are dependent under the declared QR tolerance."""


def finite(value):
    if not math.isfinite(value):
        raise NumericalRangeError('nonfinite numeric result')
    return value


def root_mean_square(values):
    scale = max(abs(value) for value in values)
    if scale == 0:
        return 0.0
    return finite(scale * math.sqrt(math.fsum((value/scale)**2 for value in values)/len(values)))


def power_term(coefficient, value, reference, exponent):
    if coefficient == 0:
        return 0.0
    try:
        result = coefficient * (value/reference)**(-exponent)
        if math.isfinite(result) and result > 0:
            return result
    except (OverflowError, ZeroDivisionError):
        pass
    try:
        result = math.exp(math.log(coefficient)-exponent*(math.log(value)-math.log(reference)))
    except OverflowError as error:
        raise NumericalRangeError('power term exceeds finite range') from error
    if not math.isfinite(result) or result == 0:
        raise NumericalRangeError('nonzero power term outside representable range')
    return result


def least_squares(columns, targets):
    """Column/target-scaled QR distinguishes rank loss from numeric range loss."""
    if not targets or any(len(column) != len(targets) for column in columns):
        raise ValueError('Nonempty targets and matching column lengths required')
    try:
        if any(type(x) not in (int, float) or not math.isfinite(x) for x in targets) or any(type(x) not in (int, float) or not math.isfinite(x) for column in columns for x in column):
            raise NumericalRangeError('Inputs must be finite numeric values')
    except OverflowError as error:
        raise NumericalRangeError('Inputs exceed finite float range') from error
    scales = [max(abs(x) for x in column) for column in columns]
    if any(scale == 0 for scale in scales):
        raise RankDeficientError('zero active column')
    target_scale = max(abs(x) for x in targets) or 1.0
    scaled_targets = [x/target_scale for x in targets]
    q, upper = [], [[0.0] * len(columns) for _ in columns]
    for j, column in enumerate(columns):
        vector = [x/scales[j] for x in column]
        original = math.hypot(*vector)
        for i, basis in enumerate(q):
            upper[i][j] = math.fsum(x*y for x, y in zip(basis, vector))
            vector = [x-upper[i][j]*y for x, y in zip(vector, basis)]
        norm = math.hypot(*vector)
        if norm <= 1e-10 * original:
            raise RankDeficientError('dependent or ill-conditioned active columns')
        upper[j][j] = norm
        q.append([x/norm for x in vector])
    rhs = [math.fsum(x*y for x, y in zip(column, scaled_targets)) for column in q]
    coefficients = [0.0] * len(columns)
    for i in reversed(range(len(columns))):
        coefficients[i] = (rhs[i]-math.fsum(upper[i][j]*coefficients[j] for j in range(i+1, len(columns))))/upper[i][i]
    restored = []
    for value, scale in zip(coefficients, scales):
        result = value * target_scale / scale
        if not math.isfinite(result) or (result == 0 and value != 0):
            try:
                result = math.copysign(math.exp(math.log(abs(value))+math.log(target_scale)-math.log(scale)), value)
            except OverflowError as error:
                raise NumericalRangeError('coefficient exceeds finite range') from error
        if result == 0 and value != 0:
            raise NumericalRangeError("nonzero coefficient underflows")
        restored.append(finite(result))
    return restored


def nonnegative_fit(rows, targets):
    """Enumerate all eight E/A/B faces; each accepted face is a feasible fit."""
    if not rows or len(rows) != len(targets) or any(len(row) != 3 for row in rows):
        raise ValueError('Three-column rows matching nonempty targets required')
    for value in [*targets, *(x for row in rows for x in row)]:
        try:
            valid = type(value) in (int, float) and math.isfinite(value)
        except OverflowError:
            valid = False
        if not valid:
            raise NumericalRangeError('Finite numeric design and targets required')
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
            try:
                residuals = [finite(math.fsum(x*y for x, y in zip(row, values))-target) for row, target in zip(rows, targets)]
                sse = finite(math.fsum(x*x for x in residuals))
            except (NumericalRangeError, OverflowError):
                continue
            candidates.append(dict(coefficients=values, active_columns=list(active), sse=sse))
    if not candidates:
        raise NumericalRangeError('no face has finite coefficients and representable SSE')
    return min(candidates, key=lambda row: row['sse'])


def fit(records, exponent_grid, N0=1e9, D0=1e10):
    """Rows require id/N/D/loss/split/control_id; one declared control only."""
    if not records or not exponent_grid:
        raise ValueError('Records and exponent grid required')
    def positive(value):
        try:
            return type(value) in (int, float) and math.isfinite(value) and value > 0
        except OverflowError:
            return False
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
    candidates, rejected = [], []
    for alpha, beta in exponent_grid:
        if not positive(alpha) or not positive(beta):
            raise ValueError('Positive finite exponents required')
        try:
            design = [[1.0, power_term(1, row['N'], N0, alpha), power_term(1, row['D'], D0, beta)] for row in train]
            targets = [row['loss'] for row in train]
            try:
                least_squares(list(zip(*design)), [0.0] * len(targets))
                dependent = False
            except RankDeficientError:
                dependent = True
            result = nonnegative_fit(design, targets)
        except (NumericalRangeError, OverflowError) as error:
            rejected.append(dict(alpha=alpha, beta=beta, category='numeric_range', reason=str(error)))
            continue
        candidates.append(dict(result, alpha=alpha, beta=beta, full_design_rank_deficient=dependent))
    if not candidates:
        raise NumericalRangeError('no finite representable grid candidate')
    best = min(candidates, key=lambda row: row['sse'])
    E, A, B = best['coefficients']
    predictions = []
    for row in records:
        prediction = finite(E + power_term(A,row['N'],N0,best['alpha']) + power_term(B,row['D'],D0,best['beta']))
        predictions.append(dict(row, prediction=prediction, residual=prediction-row['loss']))
    result = dict(law=dict(E=E, A=A, B=B, alpha=best['alpha'], beta=best['beta'], N0=N0, D0=D0),
                fit_sse=best['sse'], predictions=predictions, candidates=candidates,
                holdout_rmse=root_mean_square([row['residual'] for row in predictions if row['split']=='holdout']),
                rejected_candidates=rejected,
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

    json.dumps(result, allow_nan=False)
    return result
