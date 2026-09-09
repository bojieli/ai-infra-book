"""Source-backed real scaling fit and declared lifecycle figure."""
import json
from pathlib import Path
from .paths import PROJECT
from .specialization_plot import digest

DIRECTORY = PROJECT / 'figures/real-scaling'


def verify():
    path = DIRECTORY / 'manifest.json'
    if not path.exists():
        return dict(verified_figures=0)
    manifest = json.loads(path.read_text())
    for row in manifest['inputs'] + manifest['artifacts']:
        if digest(PROJECT / row['file']) != row['sha256']:
            raise ValueError('Real scaling figure stale: ' + row['file'] + '; run plot-real-scaling')
    return dict(verified_figures=len(manifest['artifacts']))


def render():
    from .reproduce import verify_results
    verify_results(include_figures=False)
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as error:
        raise ValueError('Install optional calculations[plot] dependencies') from error
    sources = [PROJECT / 'results/datablations-real-c4-eight-point-fit.json', PROJECT / 'results/real-c4-lifecycle-512-128.json']
    fitted, result = [json.loads(path.read_text()) for path in sources]
    fit = fitted['primary']['result']
    if result['variants'][0]['law'] != fit['law']:
        raise ValueError('Lifecycle and observation figure must use the same fitted law')
    scenario = result['scenario']
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'svg.hashsalt': 'infra-calc-real-scaling', 'font.family': 'DejaVu Sans', 'font.size': 10})
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout='constrained')
    for split, color, marker in [('fit','#276FBF','o'),('holdout','#D45A28','s')]:
        rows = [r for r in fit['predictions'] if r['split']==split]
        axes[0].scatter([r['loss'] for r in rows], [r['predicted_loss'] for r in rows], color=color, marker=marker, label=f'{split}: {len(rows)} real points')
    values = [r['loss'] for r in fit['predictions']]+[r['predicted_loss'] for r in fit['predictions']]
    axes[0].plot([min(values),max(values)],[min(values),max(values)], color='gray', linestyle='--', linewidth=1)
    axes[0].set(xlabel='Observed C4 loss (nats/token)', ylabel='Predicted loss (nats/token)', title=f"Finite-grid fit; holdout RMSE {fit['holdout_rmse']:.5f}")
    axes[0].legend()
    calls = np.geomspace(1,1e9,160)
    for row in result['variants'][0]['lifecycle']['rows']:
        if not row['feasible']: continue
        outside = row['outside_fit_box']
        axes[1].plot(calls,row['upfront_cost']+calls*row['cost_per_call'], linestyle='--' if outside else '-',label=f"N={row['N']/1e9:g}B" + ('; outside fit box' if outside else ''))
    axes[1].set(xscale='log',yscale='log',xlabel=f"Lifetime calls ({scenario['input_tokens']} input; {scenario['returned_tokens']} returned tokens)",ylabel='Declared abstract cost units',title=f"Target loss {scenario['target_loss']}; training + inference proxy")
    axes[1].legend(fontsize=8)
    for ax in axes: ax.grid(alpha=.2)
    fig.suptitle('Real-data fit and conditional lifecycle — no hardware price or task-quality claim',fontsize=11)
    for extension in ('png', 'svg', 'pdf'):
        metadata = {'Date': None} if extension == 'svg' else ({'CreationDate': None, 'ModDate': None} if extension == 'pdf' else {'Software': 'infra-calc'})
        fig.savefig(DIRECTORY / ('figure.' + extension), dpi=160, metadata=metadata)
    plt.close(fig)
    inputs = sources + [Path(__file__), PROJECT / 'pyproject.toml', Path(__file__).with_name('specialization_plot.py')]
    artifacts = [DIRECTORY / ('figure.' + extension) for extension in ('png', 'svg', 'pdf')]
    manifest = dict(matplotlib_version=matplotlib.__version__,
                    inputs=[dict(file=str(p.relative_to(PROJECT)), sha256=digest(p)) for p in inputs],
                    artifacts=[dict(file=str(p.relative_to(PROJECT)), sha256=digest(p)) for p in artifacts])
    (DIRECTORY / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return dict(directory=str(DIRECTORY), **verify())
