"""Visualize validated VL stage work; cache hits do not remove language work."""
import json
from pathlib import Path

from .paths import PROJECT
from .specialization_plot import digest


DIRECTORY = PROJECT / 'figures/vl-stages'


def verify():
    path = DIRECTORY / 'manifest.json'
    if not path.exists():
        return dict(verified_figures=0)
    manifest = json.loads(path.read_text())
    for row in manifest['inputs'] + manifest['artifacts']:
        if digest(PROJECT / row['file']) != row['sha256']:
            raise ValueError('VL stage figure stale: ' + row['file'] + '; run plot-vl-stages')
    return dict(verified_figures=len(manifest['artifacts']))


def chart_data(cold, warm):
    """Compare identical requests; only verified encoder-cache hits may differ."""
    a, b = dict(cold['scenario']), dict(warm['scenario'])
    a.pop('encoder_cache_hits'); b.pop('encoder_cache_hits')
    if a != b:
        raise ValueError('VL stage comparison requires the same request')
    if cold['scenario']['encoder_cache_hits'] != 0 or warm['scenario']['encoder_cache_hits'] != a['images_per_request']:
        raise ValueError('Compare zero versus all image encoder-cache hits')
    rows = []
    for label, result in [('Encode every image', cold), ('All encoder features cached', warm)]:
        stages = result['vl_request_stages']
        if sum(s['matrix_flops'] for s in stages) != result['summary']['total_matrix_flops']:
            raise ValueError('VL stage sum differs from request total')
        rows.append(dict(label=label, stages=stages, total_matrix_flops=result['summary']['total_matrix_flops']))
    if rows[0]['stages'][1:] != rows[1]['stages'][1:]:
        raise ValueError('Encoder cache unexpectedly changed language work')
    return dict(scenario=a, rows=rows,
                prompt_positions=cold['summary']['prompt_positions'],
                final_kv_positions=cold['summary']['final_kv_positions'],
                final_kv_bytes=cold['summary']['final_kv_bytes'],
                complete_encoder_bytes_per_request=cold['summary']['complete_encoder_bytes_per_request'],
                scope='Matrix work only; not latency, quality, physical HBM traffic or a peak-memory estimate')


def render():
    from .reproduce import verify_results
    verify_results(include_figures=False)
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError('Install the optional calculations[plot] dependency') from exc
    sources = [PROJECT / 'results' / (name + '.json') for name in ('vl-request-book', 'vl-request-all-ec-hit')]
    data = chart_data(*(json.loads(path.read_text()) for path in sources))
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    (DIRECTORY / 'data.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    plt.rcParams.update({'svg.hashsalt':'infra-calc-vl-stages','font.family':'DejaVu Sans','font.size':11})
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), gridspec_kw={'height_ratios':[1, 1.3]}, layout='constrained')
    top, bottom = axes
    colors = ['#3978A8', '#D69232', '#408D69']
    labels = ['Image encoder', 'Language prefill', 'Language decode']
    details = ['4 images, each 640 x 640\n400 merged positions per image',
               '2,000 prompt positions\nLast logits produce output token 1',
               '127 single-token calls\nKV grows to 2,127 positions']
    for i, (label, detail, color) in enumerate(zip(labels, details, colors)):
        x = .17 + i * .33
        top.text(x, .60, label, color='white', weight='bold', ha='center', va='center',
                 bbox=dict(boxstyle='round,pad=.7', facecolor=color, edgecolor='none'), transform=top.transAxes)
        top.text(x, .20, detail, ha='center', va='center', fontsize=10, transform=top.transAxes)
        if i < 2:
            top.annotate('', xy=(x+.23,.60), xytext=(x+.11,.60), xycoords='axes fraction',
                         arrowprops=dict(arrowstyle='->', color='#555555', linewidth=1.6))
    top.axis('off')
    for y, row in enumerate(data['rows']):
        left = 0
        for stage, color in zip(row['stages'], colors):
            value = stage['matrix_flops'] / 10**12
            bottom.barh(y, value, left=left, color=color, height=.48)
            if value > 0:
                bottom.text(left + value/2, y, f'{value:.3f}', ha='center', va='center', color='white', fontsize=10)
            left += value
        bottom.text(left + .25, y, f'{left:.3f} TFLOPs', va='center', fontsize=10)
    bottom.set_yticks(range(len(data['rows'])), [row['label'] for row in data['rows']])
    bottom.invert_yaxis()
    maximum = max(r['total_matrix_flops'] for r in data['rows']) / 10**12
    bottom.set_xlim(0, maximum*1.19)
    bottom.set_xlabel('Matrix work per request (10^12 FLOPs); not TFLOP/s or latency')
    bottom.grid(axis='x', alpha=.2)
    bottom.set_axisbelow(True)
    fig.suptitle('Qwen3-VL-4B: image encoding precedes language prefill', fontsize=16)
    fig.supxlabel('Same request: four 640 x 640 images + 400 other prompt positions, 128 output tokens.\n'
                  'Encoder-cache hits remove only encoding work. Feature reads, transfers and CPU preprocessing are outside these bars.', fontsize=10)
    for extension in ('svg','png','pdf'):
        metadata = {'Date':None} if extension == 'svg' else ({'CreationDate':None, 'ModDate':None} if extension == 'pdf' else {'Software':'infra-calc'})
        fig.savefig(DIRECTORY / ('figure.'+extension), dpi=160, metadata=metadata)
    plt.close(fig)
    inputs = sources + [Path(__file__), PROJECT/'pyproject.toml', Path(__file__).with_name('specialization_plot.py')]
    artifacts = [DIRECTORY / name for name in ('figure.svg','figure.png','figure.pdf','data.json')]
    manifest = dict(matplotlib_version=matplotlib.__version__,
                    inputs=[dict(file=str(p.relative_to(PROJECT)), sha256=digest(p)) for p in inputs],
                    artifacts=[dict(file=str(p.relative_to(PROJECT)), sha256=digest(p)) for p in artifacts])
    (DIRECTORY/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return dict(directory=str(DIRECTORY), **verify())
