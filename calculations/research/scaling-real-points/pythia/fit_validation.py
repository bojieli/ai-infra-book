"""Real Pythia validation observations; a bounded nonnegative scaling fit."""
from pathlib import Path
import hashlib
import itertools
import json
import math
import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = {'32t0zbcs': '70m', '3mvtbwii': '160m', '12j05401': '410m',
        'vd5ogsc6': '1.4b', '2l7ymzlr': '2.8b', '4x2lfblu': '2.8b', '2j0vfxrj': '2.8b'}


def records():
    nodes = {e['node']['name']: e['node'] for e in json.loads((HERE / 'v2-loss-runs.json').read_text())['data']['project']['runs']['edges']}
    out = []
    for run, model in RUNS.items():
        config = {k: v.get('value') for k, v in json.loads(nodes[run]['config']).items()}
        h, layers = config['hidden_size'], config['num_layers']
        n = 12 * layers * h * h + 13 * layers * h + 2 * h + 2 * 50304 * h
        assert config['train_batch_size'] == 1024 and config['seq_length'] == 2048
        assert config['git_hash'] == 'd36f623' and config['precision'] == 'fp16'
        path = HERE / f'v2-{run}-history.json'
        for row in json.loads(path.read_text())['data']['project']['run']['sampledHistory'][0]:
            observed = row['validation/lm_loss']
            assert math.isclose(math.exp(observed), row['validation/lm_loss_ppl'], rel_tol=1e-12)
            out.append(dict(id=f'{model}-step{row["_step"]}', model=model, run=run,
                            N=n, D=row['_step'] * 2097152, loss=observed,
                            C_flops=6*n*row['_step']*2097152,
                            split='holdout' if n >= 2_000_000_000 else 'fit',
                            control_id='pythia-standard-d36f623-logged-validation-training-document-pool',
                            source_file=path.name, source_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    assert len({r['id'] for r in out}) == len(out)
    return out


def fit(rows, grid, weighting='point'):
    """Enumerate all active coefficient sets; held-out rows never enter selection."""
    train = [r for r in rows if r['split'] == 'fit']
    counts = {r['model']: sum(x['model'] == r['model'] for x in train) for r in train}
    weights = np.array([1 / counts[r['model']] if weighting == 'model' else 1 for r in train])
    target = np.array([r['loss'] for r in train])
    best = None
    for alpha, beta in itertools.product(grid, repeat=2):
        design = np.array([[1, (r['N']/1e9)**(-alpha), (r['D']/1e10)**(-beta)] for r in train])
        for mask in range(1, 8):
            columns = [i for i in range(3) if mask & (1 << i)]
            active = design[:, columns] * np.sqrt(weights[:, None])
            solution, _, rank, _ = np.linalg.lstsq(active, target*np.sqrt(weights), rcond=1e-12)
            if rank != len(columns) or any(solution < 0):
                continue
            coefficients = np.zeros(3)
            coefficients[columns] = solution
            error = design @ coefficients - target
            sse = float(sum(weights*error*error))
            if best is None or sse < best['weighted_fit_sse'] - 1e-14:
                best = dict(coefficients=coefficients.tolist(), alpha=alpha, beta=beta,
                            weighted_fit_sse=sse, active_columns=columns)
    if best is None:
        raise ValueError('No admissible nonnegative fit')
    e, a, b = best['coefficients']
    predictions = []
    for row in rows:
        prediction = e + a*(row['N']/1e9)**(-best['alpha']) + b*(row['D']/1e10)**(-best['beta'])
        predictions.append(dict(**row, predicted_loss=prediction, residual=prediction-row['loss']))
    held = [r['residual'] for r in predictions if r['split'] == 'holdout']
    best.update(weighting=weighting, predictions=predictions,
                holdout_rmse=math.sqrt(sum(x*x for x in held)/len(held)) if held else None,
                beta_identifiable=b != 0, compute_optimum_identified=False)
    return best


def calculate():
    rows = records()
    grid = [i/100 for i in range(10,61,5)]
    return dict(generalization_evidence_gate=False, status='exploratory_training_document_pool_only',
                exclusion_reason='Configured train/valid paths share full documents in build_weighted_datasets; split is not applied on this code path',
                records=rows, primary=fit(rows,grid),
                equal_model_weight=fit(rows,grid,'model'),
                wider_grid=fit(rows,[i/100 for i in range(5,81,5)]),
                leave_one_fit_size_out={m: fit([r for r in rows if r['model'] != m],grid)
                                       for m in sorted({r['model'] for r in rows if r['split']=='fit'})},
                scope='Author-logged validation loss evaluates the training document pool, not an established held-out population. Different iterator positions, correlated checkpoints and unknown sampling variance; this diagnostic does not satisfy the generalization-loss task.')


if __name__ == '__main__':
    (HERE/'validation-fit.json').write_text(json.dumps(calculate(), indent=2)+'\n')
