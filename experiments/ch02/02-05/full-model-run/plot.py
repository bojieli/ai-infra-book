"""Plot only validated actual run evidence; no synthetic or fallback data."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--analysis', type=Path)
    args = parser.parse_args()
    source = args.out.resolve()
    folder = args.analysis or source / 'offline-analysis'
    report = json.loads((folder / 'analysis.json').read_text())
    assert report['status'] == 'completed_actual_execution' and report['denominator'] == 8
    for name, expected in report['provenance']['source_sha256'].items():
        assert hashlib.sha256((source / name).read_bytes()).hexdigest() == expected, 'Raw evidence changed: ' + name
    scores = json.loads((folder / 'scores-recomputed.json').read_text())['cases']
    samples = [json.loads(line) for line in (source / 'watchdog.jsonl').read_text().splitlines() if line.strip()]
    assert len(scores) == 8 and all(c['returned'] and c['schema_valid'] for c in scores)
    for stem in ('retrieval-results', 'resource-timeline'):
        for ext in ('png', 'svg'):
            assert not (folder / (stem + '.' + ext)).exists(), 'Existing plot; choose a fresh analysis directory'
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
    colors = ['#20866c' if c['strict_success'] else '#be6046' for c in scores]
    bars = ax.bar(range(8), [c['request_wall_s'] for c in scores], color=colors)
    ax.set_xticks(range(8), [f"{c['actual_prompt_tokens']} tokens\n{c['variant']} / {c['position']}" for c in scores])
    ax.set_ylabel('Application request envelope (s)')
    ax.set_title(f"Full V4 retrieval: {report['quality_strict_success']}/8 strict matches (fixed cases)")
    for bar, c in zip(bars, scores):
        ax.annotate(f"{c['request_wall_s']:.2f}s\n{c['finish_reason']['type']}", (bar.get_x() + bar.get_width()/2, bar.get_height()), xytext=(0, 4), textcoords='offset points', ha='center', fontsize=8)
    ax.margins(y=.25)
    ax.legend(handles=[Patch(color='#20866c', label='Correct answer + normal stop'), Patch(color='#be6046', label='Does not satisfy strict success')])
    for ext in ('png', 'svg'):
        fig.savefig(folder / ('retrieval-results.' + ext), dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True, constrained_layout=True)
    t = [s['elapsed_s'] for s in samples]
    for key, scale, label in [('own_rss_bytes', 2**30, 'Process RSS sum (shared pages may repeat)'), ('own_anon_bytes', 2**30, 'Process anonymous RSS sum'), ('available_bytes', 2**30, 'Host MemAvailable')]:
        axes[0].plot(t, [s[key]/scale for s in samples], label=label)
    for key, label in [('own_gpu_mib', 'Experiment GPU allocation'), ('gpu_free_mib', 'Shared-host GPU free')]:
        axes[1].plot(t, [s[key]/1024 for s in samples], label=label)
    for ax in axes:
        ax.set_ylabel('GiB'); ax.legend(loc='best'); ax.grid(alpha=.2)
    axes[1].set_xlabel('Seconds since watchdog launch')
    axes[0].set_title(f"Actual watchdog samples: n={len(samples)}, max interval={report['resources']['interval_s']['max']:.3f}s; no continuous-peak claim")
    for ext in ('png', 'svg'):
        fig.savefig(folder / ('resource-timeline.' + ext), dpi=180)
    plt.close(fig)

if __name__ == '__main__':
    main()
