#!/usr/bin/env python3
"""Reproduce the survey's displayed historical data and explicit calculations."""
from pathlib import Path
from datetime import datetime
import csv
import json
from bs4 import BeautifulSoup
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ARCHIVE = ROOT / 'references/token-cost/2026-09-07'

def main():
    (HERE / 'data').mkdir(exist_ok=True)
    (HERE / 'figures').mkdir(exist_ok=True)
    soup = BeautifulSoup((ARCHIVE / 'epoch-prices.html').read_text(), 'html.parser')
    # The responsive page repeats the same table; extract exactly its first copy.
    table = next(t for t in soup.find_all('table') if 'Benchmark score' in t.get_text())
    fields = [h.get_text(' ', strip=True) for h in table.find_all('th')]
    rows = []
    for tr in table.find_all('tr'):
        values = [td.get_text(' ', strip=True) for td in tr.find_all('td')]
        if values:
            assert len(values) == len(fields)
            rows.append(dict(zip(fields, values)))
    with (HERE / 'data/epoch-frontiers.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    selections = [('MMLU', 'GPT-3.5', 'MMLU >= 64.8 (GPT-3.5)'),
                  ('MMLU', 'GPT-3.5 Turbo', 'MMLU >= 68 (GPT-3.5 Turbo)'),
                  ('MMLU', 'GPT-4-0314', 'MMLU >= 86 (GPT-4)'),
                  ('GPQA Diamond', 'GPT-4-0314', 'GPQA Diamond >= 33 (GPT-4)'),
                  ('HumanEval', 'GPT-4-0314', 'HumanEval >= 67 (GPT-4)')]
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    colors = ['#5876ac', '#289a9a', '#bf7b22', '#9a5f9e', '#46734e']
    history = []
    for (benchmark, threshold, label), color in zip(selections, colors):
        chosen = [r for r in rows if r['Benchmark'] == benchmark and r['Threshold model'] == threshold]
        dates = [datetime.fromisoformat(r['Release Date']) for r in chosen]
        prices = [float(r['USD per 1M Tokens'].replace('$', '').replace(',', '')) for r in chosen]
        ax.step(dates, prices, where='post', lw=1.7, color=color, label=label)
        ax.scatter(dates, prices, s=20, color=color, zorder=3)
        history.append(dict(benchmark=benchmark, threshold=threshold,
                            start=chosen[0], end=chosen[-1], endpoint_ratio=prices[0]/prices[-1]))
    ax.set_yscale('log')
    ax.set_ylim(.05, 65)
    ax.set_xlim(datetime(2022, 11, 1), datetime(2025, 4, 1))
    ax.set_ylabel('USD / 1M blended tokens (3:1 input:output, log scale)')
    ax.set_title('Historical prices at fixed benchmark thresholds', loc='left', fontsize=15, pad=15)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.grid(axis='y', which='both', alpha=.17)
    ax.spines[['top','right']].set_visible(False)
    ax.legend(loc='upper right', fontsize=9, frameon=False)
    fig.text(.1, .035, 'Source: Epoch AI, 2025-03-12 analysis; values rounded as displayed.\n'
             'Lines end at observed points. No extrapolation to 2026; no production-cost inference.', fontsize=9, color='#555555')
    fig.subplots_adjust(left=.1, right=.97, top=.9, bottom=.17)
    fig.savefig(HERE / 'figures/price-frontiers.svg')
    fig.savefig(HERE / 'figures/price-frontiers.png', dpi=180)
    plt.close(fig)

    out = {
        'scope': 'Published rounded-price endpoint ratios plus explicitly hypothetical resource/task examples. Not a 2023-2026 industry cost attribution.',
        'historical_endpoints': history,
        'gemini_launch_blend': {'2026-03-03': (3*.25+1.5)/4, '2026-07-21': (3*.3+2.5)/4,
                                'later_over_earlier': ((3*.3+2.5)/4)/((3*.25+1.5)/4)},
        'parameter_ratio_70_to_8': 70/8,
        'kv_example_gib': {'mha': 2*32*8192*32*128*2/2**30, 'gqa': 2*32*8192*8*128*2/2**30},
        'deepseek_v2_kv_ratio': 1/(1-.933),
        'bandwidth_ratios': {'h100_over_a100': 3.35/2.039, 'h200_over_h100': 4.8/3.35},
        'illustrative_two_year_doubling_over_three_years': 2**(3/2),
        'inferencex_displayed_numbers': {'throughput_ratio': 6182/2189, 'cost_ratio': (6182/2189)/(2.65/2.21),
                                        'published_cost_ratio': 2.31,
                                        'note': 'Published interpolated claim is not exactly reproducible from these displayed inputs; report retains discrepancy.'},
        'weight_read_lower_bounds_ms': [70/3350*1000, 8/3350*1000, 4/3350*1000, 4/4800*1000],
        'weight_read_lower_bound_ratio': (70/3350)/(4/4800),
        'speculation_hypothetical': [dict(k=4, p=p, expected_tokens=sum(p**i for i in range(5)),
                                         round_cost_in_normal_steps=1.8, speedup=sum(p**i for i in range(5))/1.8) for p in [.8,.3]],
        'successful_task_cost_hypothetical_ratio': (20/10)*.5/.8,
        'lifecycle_hypothetical_break_even_requests': 1_000_000/.002,
    }
    (HERE / 'calculations.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n')
    print(f'Extracted {len(rows)} observations; generated 5 historical series and calculation record.')

if __name__ == '__main__':
    main()
