"""Source-verifiable C4 subset; reported-coordinate fit with explicit sensitivity."""
import json
import importlib.util
import hashlib
import re
from pathlib import Path
from adapt import build, GRID, scaling_law

HERE = Path(__file__).resolve().parent


def records():
    strict = build()
    logs = json.loads((HERE/'log-controls.json').read_text())
    out = []
    for row in strict:
        if 'evaluation' not in row or row['record_id'] == '146m14b14b':
            continue
        text = (HERE/row['evaluation']['file']).read_text()
        checks = {
            'tokenizer': r'tokenizer_type\s+\.+\s+GPT2BPETokenizer',
            'vocab': r'vocab_file\s+\.+\s+gpt2/vocab.json',
            'merges': r'merge_file\s+\.+\s+gpt2/merges.txt',
            'validation': r'valid_weighted_split_paths\s+\.+.*c4_validation/gpt2tok_c4validation_rerun_text_document',
            'validation_split': r'valid_weighted_split_splits\s+\.+\s+\[\[\x270:1\x27\]\]',
        }
        for name, pattern in checks.items():
            if not re.search(pattern,text):
                raise ValueError(f'{row["record_id"]}: {name} evidence absent')
        control = next(x for x in logs if x['file'] == row['evaluation']['file'])
        h, layers = control['hidden_size'], control['num_layers']
        out.append(dict(id=row['record_id'],N=row['N'],D=row['D'],loss=row['loss'],
                        split=row['split'],control_id='C4-validation-gpt2-same-population-variable-budget',
                        C_flops=6*row['N']*row['D'],
                        N_shape_estimate=12*layers*h*h+13*layers*h+(50257+2048)*h,
                        D_declared_budget=row.get('training_budget',{}).get('declared_target_tokens'),
                        evaluation=row['evaluation'],coordinate_status='author reported estimates',
                        source_controls=list(checks)))
    return out


def run_fit(rows, grid):
    try:
        return dict(status='fit',result=scaling_law.fit(rows,grid,1e9,1e10))
    except ValueError as error:
        return dict(status='no_admissible_interior_fit',reason=str(error))


def boundary(rows):
    path=HERE.parent/'scaling-boundary-fit'/'boundary_fit.py'
    spec=importlib.util.spec_from_file_location('real_points_boundary',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.fit(rows,GRID,N0=1e9,D0=1e10)


def calculate():
    rows=records()
    sensitivity={}
    for kind in ('shape_N','declared_D','both'):
        changed=[]
        for r in rows:
            q=dict(r)
            if kind in ('shape_N','both'):q['N']=r['N_shape_estimate']
            if kind in ('declared_D','both') and r['D_declared_budget'] is not None:q['D']=r['D_declared_budget']
            q['C_flops']=6*q['N']*q['D']
            changed.append(q)
        sensitivity[kind]=run_fit(changed,GRID)
    sensitivity['wider_grid']=run_fit(rows,[(a/100,b/100) for a in range(5,81,5) for b in range(5,81,5)])
    evidence_files=['README.md','sources.lock.json','adapter-inputs.lock.json',
                    '../scaling-real-points-independent/STATISTICAL-C4-REVIEW.md',
                    '../scaling-real-points-independent/statistical-C4-eight-point-evidence.json',
                    '../scaling-real-points-independent/n-loss-sources.lock.json']
    evidence=[dict(file=f,sha256=hashlib.sha256((HERE/f).read_bytes()).hexdigest()) for f in evidence_files]
    return dict(sources=evidence,records=rows,primary=run_fit(rows,GRID),boundary_diagnostic=boundary(rows),sensitivity=sensitivity,
                estimand='Held-out C4 population token loss, variable finite evaluation samples',
                sampling_variance_known=False,independent_observations=False,
                coordinate_uncertainty='Reported N/D; shape and declared-budget sensitivities are not exact checkpoint/achieved-token proof')


if __name__=='__main__':
    (HERE/'statistical-fit.json').write_text(json.dumps(calculate(),indent=2)+'\n')
