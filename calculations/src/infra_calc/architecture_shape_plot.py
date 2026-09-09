"""Data-bound architecture shapes; diagram dimensions are symbolic, not runtime."""
import hashlib
import json
from pathlib import Path

from infra_calc.paths import PROJECT


def calculate():
    source = PROJECT / 'results/architecture-decode.json'
    dense = json.loads(source.read_text())
    sources = [source]
    panels = []
    for name in ('baseline', 'deeper_same_width', 'shallower_wider'):
        row = next(r for r in dense['variants'] if r['name'] == name)
        c = row['config']
        h, f, layers = c['hidden_size'], c['intermediate_size'], c['num_hidden_layers']
        panels.append({'family': 'Dense', 'name': name, 'layers': layers,
                       'hidden': h, 'intermediate': f,
                       'weights_per_ffn': [[f, h], [f, h], [h, f]],
                       'ffn_parameters_all_layers': 3 * layers * h * f,
                       'total_parameters': row['actual_parameters'],
                       'parameter_delta': row['parameter_delta'],
                       'released_baseline': name == 'baseline'})
    for name in ('baseline', 'coarse64', 'fine256-k16'):
        source = PROJECT / 'results' / ('qwen235-granularity-' + name + '.json')
        sources.append(source)
        row = json.loads(source.read_text())
        g, p = row['geometry'], row['parameters']
        h, f, layers, experts = g['hidden'], g['intermediate'], g['layers'], g['experts']
        expert_parameters = 3 * layers * experts * h * f
        if expert_parameters != p['expert_total']:
            raise ValueError('Expert shape/parameter disagreement')
        selected = row['route_table'][0]['experts']
        if len(set(selected)) != g['top_k'] or any(e < 0 or e >= experts for e in selected):
            raise ValueError('Invalid first recorded expert set')
        panels.append({'family': 'MoE', 'name': name, 'layers': layers,
                       'hidden': h, 'intermediate': f, 'experts': experts, 'top_k': g['top_k'],
                       'weights_per_expert': [[f, h], [f, h], [h, f]],
                       'expert_parameters_all_layers': expert_parameters,
                       'router_parameters_all_layers': layers * h * experts,
                       'active_expert_parameters_all_layers': 3 * layers * g['top_k'] * h * f,
                       'first_recorded_expert_set': selected,
                       'first_recorded_route': row['route_table'][0],
                       'total_parameters': p['variant_total'], 'parameter_delta': p['total_delta'],
                       'released_baseline': name == 'baseline'})
    return {'panels': panels, 'inputs': [{'file': str(p.relative_to(PROJECT)),
                                         'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources],
            'scope': 'Only baselines are released model configurations. Variants are untrained. Dense stack: one bar per layer, width proportional to H within Dense column. MoE grid: one bar per expert of one layer, width proportional to F within MoE column; highlighted IDs come from first synthetic route record, not observed runtime. The two columns have different scales. Displayed matrices are FFN/expert weights only, not all model weights. No quality, latency or hardware utilization inference.'}


DIRECTORY = PROJECT / 'figures/architecture-shapes'


def verify():
    path = DIRECTORY / 'manifest.json'
    if not path.exists():
        return {'verified_figures': 0}
    manifest = json.loads(path.read_text())
    expected_inputs = {'results/architecture-decode.json',
                       'results/qwen235-granularity-baseline.json',
                       'results/qwen235-granularity-coarse64.json',
                       'results/qwen235-granularity-fine256-k16.json',
                       str(Path(__file__).relative_to(PROJECT))}
    expected_artifacts = {str((DIRECTORY / name).relative_to(PROJECT))
                          for name in ('figure.png', 'figure.svg', 'figure.pdf', 'data.json')}
    for key, expected in (('inputs', expected_inputs), ('artifacts', expected_artifacts)):
        rows = manifest.get(key)
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError('Invalid architecture figure manifest list: ' + key)
        names = [row.get('file') for row in rows]
        if any(not isinstance(name, str) for name in names) or len(names) != len(expected) or set(names) != expected:
            raise ValueError('Incomplete or duplicate architecture figure manifest: ' + key)
    for row in manifest['inputs'] + manifest['artifacts']:
        if hashlib.sha256((PROJECT / row['file']).read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Architecture figure stale: ' + row['file'])
    return {'verified_figures': 3}


def render():
    from .reproduce import verify_results
    verify_results(include_figures=False)
    directory = DIRECTORY
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    data = calculate()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10, 'svg.hashsalt':'infra-architecture-shapes'})
    fig, axes = plt.subplots(3, 2, figsize=(13, 9), layout='constrained')
    for i, panel in enumerate(data['panels']):
        ax = axes[i if i < 3 else i-3, 0 if i < 3 else 1]
        ax.set(xlim=(0, 1), ylim=(0, 1))
        ax.axis('off')
        baseline = panel['released_baseline']
        title = panel['name'].replace('_', ' ')
        ax.text(0, .98, panel['family'] + ' | ' + title + (' (released baseline)' if baseline else ' (untrained)'), va='top', weight='bold', fontsize=11)
        h, f, layers = panel['hidden'], panel['intermediate'], panel['layers']
        if panel['family'] == 'Dense':
            for layer in range(layers):
                ax.add_patch(Rectangle((.02, .81-layer*.013), .24*h/5120, .007, linewidth=0, color='#346FB1'))
            ax.text(.31, .80, f'L={layers}; H={h:,}; F={f:,}', va='top')
            ax.text(.31, .63, f'gate/up: [{f:,}, {h:,}] each\ndown: [{h:,}, {f:,}]', va='top')
            ax.text(.31, .40, f'Total parameters: {panel["total_parameters"]:,}\nDelta: {panel["parameter_delta"]:+,}', va='top')
            ax.text(.02, .04, 'One bar per layer; bar width proportional to H', fontsize=9)
        else:
            selected = set(panel['first_recorded_expert_set'])
            for expert in range(panel['experts']):
                x, y = expert%16, expert//16
                ax.add_patch(Rectangle((.015+x*.018, .81-y*.032), .015*f/3072, .023,
                                      linewidth=0, color='#D8672A' if expert in selected else '#9ABAAE'))
            ax.text(.34, .80, f'L={layers}; E={panel["experts"]}; top-k={panel["top_k"]}\nH={h:,}; F={f:,}', va='top')
            ax.text(.34, .58, f'per expert gate/up: [{f:,}, {h:,}]\ndown: [{h:,}, {f:,}]', va='top')
            ax.text(.34, .35, f'Total: {panel["total_parameters"]:,}\nDelta: {panel["parameter_delta"]:+,}\nRouter: {panel["router_parameters_all_layers"]:,}', va='top')
            ax.text(.015, .04, 'One layer of experts; orange = first synthetic route top-k', fontsize=9)
    fig.suptitle('Architecture shape and parameter budgets\nQwen3-8B Dense variants | Qwen3-235B expert variants', fontsize=14)
    fig.supxlabel('Symbolic scales differ between columns. FFN weights shown, not all model matrices. No equal-quality or speed claim.', fontsize=10)
    for ext in ('png','svg','pdf'):
        metadata = {'Date':None} if ext=='svg' else {'CreationDate':None,'ModDate':None} if ext=='pdf' else {'Software':'infra-calc'}
        fig.savefig(directory/('figure.'+ext), dpi=160, metadata=metadata)
    plt.close(fig)
    (directory/'data.json').write_text(json.dumps(data,indent=2)+'\n')
    files = [directory / ('figure.' + ext) for ext in ('png', 'svg', 'pdf')] + [directory / 'data.json']
    inputs = data['inputs'] + [{'file': str(Path(__file__).relative_to(PROJECT)), 'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}]
    manifest = {'matplotlib_version': matplotlib.__version__, 'inputs': inputs,
                'artifacts': [{'file': str(f.relative_to(PROJECT)), 'sha256': hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]}
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return {'directory': str(directory), **verify()}
