# Public lifecycle integration candidate

Copy src/infra_calc/topics/real_scaling_lifecycle.py and tests/test_real_scaling_lifecycle.py into calculations. Register calculate/markdown and the single book.append.json scenario. The topic directly calls public real_scaling_fit.calculate() each time; it neither reads research result.json nor dynamically imports research code. The parent's existing lifecycle() implements the original unchanged formulas. No new official dataset copies or data locks are needed; output carries real_scaling_fit's source bindings.

The public parameters preserve the frozen main scenario: target loss 2.9; sizes 0.1B/0.5B/1B/2.81B; input512/returned128, hence additional decode127; the same declared 1e-18 abstract cost unit per proxy FLOP; setup0. Invalid token counts/rates/duplicate candidate sizes are rejected. The report shows all five laws separately, every candidate, crossovers, extrapolation factors and requested call counts. These costs omit attention, KV, heads, sampling, communication and actual hardware efficiency and do not establish equal task quality.

Portable replay: PYTHONDONTWRITEBYTECODE=1 python calculations/research/real-scaling-lifecycle/public/replay.py. It verifies the public scenario and complete five-variant ledger exactly equal the original frozen result, then writes example.json/example.md/bindings.json. The topic does not depend on this migration-only replay script. Portable tests: PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s calculations/research/real-scaling-lifecycle/public/tests -v (five tests).

Original plot.py/PNG/SVG remain beside this public directory for the parent's unified figure integration. They are not required to execute the public topic.
