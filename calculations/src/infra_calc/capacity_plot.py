"""Exact necessary-capacity staircases from frozen per-rank storage results."""
import hashlib
import json
from pathlib import Path

from infra_calc.paths import PROJECT

MODELS = [
    ('qwen3-8b', 'Qwen3-8B', 'TP8'),
    ('qwen3-32b', 'Qwen3-32B', 'TP8'),
    ('deepseek-r1-distill-llama-70b', 'R1-Distill-Llama-70B', 'TP8'),
    ('qwen3-235b-a22b', 'Qwen3-235B', 'TP2 / EP4'),
]


def source_path(model, capacity):
    if model == 'qwen3-235b-a22b':
        stem = f'qwen235-placement-tp2-ep4-pp1-{capacity}gb-8192'
    else:
        stem = f'dense-quant-{model}-tp8-pp1-{capacity}gb-8192'
    return PROJECT / 'results' / (stem + '.json')


def threshold(ranks, bits, workspace, requests):
    """Smallest integer per-device budget fitting the same cohort on every rank."""
    values = []
    for rank in ranks:
        row = next(f for f in rank['formats'] if f['bits'] == bits)
        values.append(row['weight_bytes'] + workspace + requests * row['kv_bytes_per_request'])
    return max(values)


def calculate():
    panels, inputs = [], []
    low, high = 24 * 10**9, 80 * 10**9
    for model, title, topology in MODELS:
        snapshots = []
        for capacity in (24, 48, 80):
            path = source_path(model, capacity)
            raw = path.read_bytes()
            snapshots.append(json.loads(raw))
            inputs.append({'file': str(path.relative_to(PROJECT)), 'sha256': hashlib.sha256(raw).hexdigest()})
        base = snapshots[0]
        workspace = base['scenario']['workspace_bytes']
        if workspace != 2 * 2**30 or base['scenario']['length'] != 8192 or len(base['ranks']) != 8:
            raise ValueError('Plot contract requires eight ranks, 8K retained positions and 2 GiB workspace')
        curves = []
        for bits in (16, 8, 4):
            limits = []
            for snap in snapshots:
                budget = snap['scenario']['capacity_bytes']
                count = min(max(0, (budget - f['weight_bytes'] - workspace) // f['kv_bytes_per_request'])
                            for rank in snap['ranks'] for f in rank['formats'] if f['bits'] == bits)
                saved = snap.get('summary', snap.get('cohort'))
                saved_row = next(r for r in saved if r['bits'] == bits)
                assert count == saved_row.get('maximum_global_requests', saved_row.get('maximum_requests'))
                # Geometry/storage is fixed across budgets, not inferred by interpolating counts.
                for rank, other in zip(base['ranks'], snap['ranks']):
                    a = next(f for f in rank['formats'] if f['bits'] == bits)
                    b = next(f for f in other['formats'] if f['bits'] == bits)
                    assert (a['weight_bytes'], a['kv_bytes_per_request']) == (b['weight_bytes'], b['kv_bytes_per_request'])
                limits.append({'capacity_bytes': budget, 'maximum_requests': count})
            nmax = limits[-1]['maximum_requests']
            jumps = [{'capacity_bytes': threshold(base['ranks'], bits, workspace, n), 'maximum_requests': n}
                     for n in range(1, nmax + 1)]
            initial = limits[0]['maximum_requests']
            points = [{'capacity_bytes': low, 'maximum_requests': initial}]
            points += [p for p in jumps if low < p['capacity_bytes'] <= high]
            if points[-1]['capacity_bytes'] != high:
                points.append({'capacity_bytes': high, 'maximum_requests': nmax})
            curves.append({'bits': bits, 'points': points, 'samples': limits,
                           'weights_workspace_minimum_bytes': threshold(base['ranks'], bits, workspace, 0),
                           'first_request_minimum_bytes': threshold(base['ranks'], bits, workspace, 1)})
        panels.append({'model': model, 'title': title, 'topology': topology, 'curves': curves})
    return {'panels': panels, 'inputs': inputs,
            'scope': 'Necessary capacity only. Declared local packed 8/4-bit format, group128/2-byte scales; embedding/head/router/norm as in frozen ledgers. BF16 KV; 8192 retained positions; 2 GiB fixed workspace per rank. One common cohort, no DP multiplication. Zero requests includes weights-not-fitting. No actual allocator, throughput or quality claim.'}


DIRECTORY = PROJECT / 'figures/capacity-curves'


def verify():
    path = DIRECTORY / 'manifest.json'
    if not path.exists():
        return {'verified_figures': 0}
    manifest = json.loads(path.read_text())
    expected_inputs = {str(source_path(model, capacity).relative_to(PROJECT))
                       for model, _, _ in MODELS for capacity in (24, 48, 80)}
    expected_inputs.add(str(Path(__file__).relative_to(PROJECT)))
    expected_artifacts = {str((DIRECTORY / name).relative_to(PROJECT))
                          for name in ('figure.png', 'figure.svg', 'figure.pdf', 'data.json')}
    for key, expected in (('inputs', expected_inputs), ('artifacts', expected_artifacts)):
        rows = manifest.get(key)
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError('Invalid capacity figure manifest list: ' + key)
        names = [row.get('file') for row in rows]
        if any(not isinstance(name, str) for name in names) or len(names) != len(expected) or set(names) != expected:
            raise ValueError('Incomplete or duplicate capacity figure manifest: ' + key)
    for row in manifest['inputs'] + manifest['artifacts']:
        if hashlib.sha256((PROJECT / row['file']).read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Capacity figure stale: ' + row['file'] + '; run plot-capacity-curves')
    return {'verified_figures': 3}


def render():
    from .reproduce import verify_results
    verify_results(include_figures=False)
    directory = DIRECTORY
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    data = calculate()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'svg.hashsalt': 'infra-capacity-curves'})
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), layout='constrained')
    for ax, panel in zip(axes.flat, data['panels']):
        for curve, color in zip(panel['curves'], ['#245BB0', '#D75A20', '#208568']):
            p = curve['points']
            ax.step([r['capacity_bytes']/1e9 for r in p], [r['maximum_requests'] for r in p], where='post', color=color,
                    label='BF16' if curve['bits']==16 else f"Declared {curve['bits']}-bit")
            ax.scatter([r['capacity_bytes']/1e9 for r in curve['samples']], [r['maximum_requests'] for r in curve['samples']], color=color, s=22)
        ax.set(title=panel['title']+' | '+panel['topology'], xlabel='Per-device budget (decimal GB)', ylabel='Maximum common-cohort requests', xlim=(24,80), ylim=(0,None))
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
    fig.suptitle('Eight devices: necessary capacity boundaries\n8K retained positions; BF16 KV; 2 GiB workspace/device; local group128 quantization', fontsize=12)
    fig.supxlabel('Zero includes weights not fitting. Capacity is not throughput or a quality comparison.', fontsize=9)
    for ext in ('png','svg','pdf'):
        metadata = {'Date': None} if ext=='svg' else {'CreationDate': None,'ModDate':None} if ext=='pdf' else {'Software':'infra-calc'}
        fig.savefig(directory/('figure.'+ext), dpi=160, metadata=metadata)
    plt.close(fig)
    (directory/'data.json').write_text(json.dumps(data,indent=2)+'\n')
    files = [directory / ('figure.' + ext) for ext in ('png', 'svg', 'pdf')] + [directory / 'data.json']
    inputs = data['inputs'] + [{'file': str(Path(__file__).relative_to(PROJECT)), 'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}]
    manifest = {'matplotlib_version': matplotlib.__version__, 'inputs': inputs,
                'artifacts': [{'file': str(f.relative_to(PROJECT)), 'sha256': hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]}
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return {'directory': str(directory), **verify()}
