# C22 conditional per-stage resource bounds

See CONTRACT.md for precision/provider, unknown, memory-interface and capacity rules. Public code is read only; candidates live under public/. Run focused tests and regenerate only this directory:

```sh
python -m unittest discover -s calculations/research/stage-resource-bounds/public/tests -v
python calculations/research/stage-resource-bounds/build_delivery.py
```

Seven tests cover the strict two-stage counterexample (serial maxima 20 versus global maximum 11), zero-work unknown-rate admission, positive unknown propagation, real model work conservation, source precision/storage distinction, three vendor profiles, refusal to substitute TF32/integer/structured-sparse peaks, supply perturbation monotonicity, capacity failure/unknown and V4 incomplete runtime propagation after explicit byte assumptions. The original Qwen/V4 matrix, scalar and special subtotals are checked on every call.

No official absence is imputed. No semantic operand byte count is presented as measured HBM. Global max, serial stage sum, compute-only known subtotal and complete-accounted availability are separate fields.
