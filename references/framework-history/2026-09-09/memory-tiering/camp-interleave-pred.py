import argparse
import math
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from update_data import load_events


BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, "csv", "all_data.csv")
MIN_CSV_PATH = os.path.join(BASE, "csv", "min_slowdown.csv")
PLOTS_DIR = os.path.join(BASE, "plots")

# Event list (kept in sync with cpu2017/perf_events.txt via update_data).
ALL_EVENTS = load_events()

# Reference latencies (ns).
L10 = 190.0
L20 = 296.0

BASELINE_RATIO = 0.0  # L100 — all-DRAM
ENDPOINT_RATIO = 1.0  # L0   — all-CXL
RATIO_ROUND = 4       # decimal places for ratio comparison


# ---------- loading ----------

def load_df(path=CSV_PATH):
  if not os.path.isfile(path):
    raise FileNotFoundError(f"{path} not found. Run update_data.py first.")
  df = pd.read_csv(path)
  if df.empty:
    raise ValueError(f"{path} is empty")
  return df


def iter_workloads(df):
  return df.groupby(["suite", "workload"], sort=True)


def get_group(df, suite, workload):
  g = df[(df["suite"] == suite) & (df["workload"] == workload)]
  if g.empty:
    raise KeyError(f"No rows for {suite}/{workload}")
  return g


def get_ratios(group):
  vals = group["remote_ratio"].dropna().tolist()
  return sorted({round(float(r), RATIO_ROUND) for r in vals})


# ---------- core data access ----------

def get_vals(group, event, ratios=None):
  """Return a 1-D np.ndarray of `event` values for `group`, aligned to `ratios`.
  If ratios is None, uses the group's own sorted remote_ratio values."""
  assert event in ALL_EVENTS, f"unknown event {event!r} (not in perf_events.txt)"
  assert event in group.columns, f"event {event!r} missing from CSV columns"
  by_ratio = {round(float(r["remote_ratio"]), RATIO_ROUND): r[event]
              for _, r in group.iterrows()}
  if ratios is None:
    ratios = sorted(by_ratio.keys())
  return np.asarray(
    [by_ratio.get(round(float(r), RATIO_ROUND), np.nan) for r in ratios],
    dtype=float,
  )


def get_many(group, events, ratios=None):
  """Bulk get_vals — returns {event: np.ndarray}."""
  if ratios is None:
    ratios = get_ratios(group)
  return {e: get_vals(group, e, ratios) for e in events}


def baseline_val(group, event):
  """Scalar value of `event` at the L100 (remote_ratio=0.0) row."""
  return float(get_vals(group, event, [BASELINE_RATIO])[0])


def endpoint_val(group, event):
  """Scalar value of `event` at the L0 (remote_ratio=1.0) row."""
  return float(get_vals(group, event, [ENDPOINT_RATIO])[0])


def eval_metric(group, metric, ratios=None):
  """Evaluate a composite metric ({'events': [...], 'function': fn}) across ratios."""
  if ratios is None:
    ratios = get_ratios(group)
  arrs = [get_vals(group, e, ratios) for e in metric["events"]]
  return metric["function"](arrs)


# ---------- composite metrics ----------

L2_ALL_RD_LATENCY = {
  "events": ["OFFCORE_REQUESTS_OUTSTANDING.ALL_DATA_RD",
             "OFFCORE_REQUESTS.ALL_DATA_RD"],
  "function": lambda a: a[0] / a[1],
}

L2_DEMAND_RD_LATENCY = {
  "events": ["OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD",
             "OFFCORE_REQUESTS.DEMAND_DATA_RD"],
  "function": lambda a: a[0] / a[1],
}

L2_DEMAND_RFO_LATENCY = {
  "events": ["OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO",
             "OFFCORE_REQUESTS.DEMAND_RFO"],
  "function": lambda a: a[0] / a[1],
}

L2_PREF_LATENCY = {
  "events": ["OFFCORE_REQUESTS_OUTSTANDING.ALL_DATA_RD",
             "OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD",
             "OFFCORE_REQUESTS.ALL_DATA_RD",
             "OFFCORE_REQUESTS.DEMAND_DATA_RD"],
  "function": lambda a: (a[0] - a[1]) / (a[2] - a[3]),
}

# Composite C-counter used by predict_cache (STALLS_MEM_ANY - STALLS_L3_MISS).
CACHE_STALL = {
  "events": ["CYCLE_ACTIVITY.STALLS_MEM_ANY",
             "CYCLE_ACTIVITY.STALLS_L3_MISS"],
  "function": lambda a: a[0] - a[1],
}


# ---------- measured slowdowns ----------

def measured_slowdowns(group, ratios=None):
  """Decompose measured Δcycles vs L100 baseline into dram / cache / store / other."""
  if ratios is None:
    ratios = get_ratios(group)
  bi = ratios.index(BASELINE_RATIO)
  cyc = get_vals(group, "cycles", ratios)
  llc = get_vals(group, "CYCLE_ACTIVITY.STALLS_L3_MISS", ratios)
  mem = get_vals(group, "CYCLE_ACTIVITY.STALLS_MEM_ANY", ratios)
  sto = get_vals(group, "EXE_ACTIVITY.BOUND_ON_STORES", ratios)
  c0 = cyc[bi]
  dram_sd = (llc - llc[bi]) / c0
  cache_sd = ((mem - llc) - (mem[bi] - llc[bi])) / c0
  store_sd = (sto - sto[bi]) / c0
  total = (cyc - c0) / c0
  other = total - dram_sd - cache_sd - store_sd
  return {"total": total, "dram_sd": dram_sd, "cache_sd": cache_sd,
          "store_sd": store_sd, "other": other}


# ---------- prediction ----------

def pred(x, cyc1, C1, C2, L1, L2, L10=L10, L20=L20):
  """x in [0,1] (remote share). Returns (Δstall_cycles)/cyc1."""
  x = np.asarray(x, dtype=float)
  r1 = L1 / L10
  r2 = L2 / L20
  t1 = C1 * (((r1 - 1) * (1 - x) ** 3) + (1 - x)) / r1
  t2 = C2 * (((r2 - 1) * x ** 3) + x) / r2
  return (t1 + t2 - C1) / cyc1


def _scalar_at(group, c_metric, ratio):
  """Return scalar value of `c_metric` (event name or metric dict) at `ratio`."""
  if isinstance(c_metric, str):
    return baseline_val(group, c_metric) if ratio == BASELINE_RATIO \
      else endpoint_val(group, c_metric) if ratio == ENDPOINT_RATIO \
      else float(get_vals(group, c_metric, [ratio])[0])
  return float(eval_metric(group, c_metric, [ratio])[0])


def predict_component(group, ratios, c_metric, l_metric, c2_override=None):
  """Generic component-slowdown prediction.
  c_metric: event-name string or {'events','function'} dict for the stall counter.
  l_metric: {'events','function'} dict for the latency.
  c2_override: if given, use as C2 and force L2 = L20 (so r2 = 1, no L2 lookup)."""
  cyc0 = baseline_val(group, "cycles")
  C1 = _scalar_at(group, c_metric, BASELINE_RATIO)
  L1 = _scalar_at(group, l_metric, BASELINE_RATIO)
  if c2_override is not None:
    C2 = float(c2_override)
    L2 = L20
  else:
    C2 = _scalar_at(group, c_metric, ENDPOINT_RATIO)
    L2 = _scalar_at(group, l_metric, ENDPOINT_RATIO)
  return pred(ratios, cyc0, C1, C2, L1, L2)


def _c2_for(c2_map, name):
  return c2_map.get(name) if c2_map else None


def predict_dram(group, ratios, c2_map=None):
  return predict_component(group, ratios,
                           "CYCLE_ACTIVITY.STALLS_L3_MISS", L2_ALL_RD_LATENCY,
                           c2_override=_c2_for(c2_map, "dram"))


def predict_cache(group, ratios, c2_map=None):
  return predict_component(group, ratios, CACHE_STALL, L2_PREF_LATENCY,
                           c2_override=_c2_for(c2_map, "cache"))


def predict_store(group, ratios, c2_map=None):
  return predict_component(group, ratios,
                           "EXE_ACTIVITY.BOUND_ON_STORES", L2_DEMAND_RFO_LATENCY,
                           c2_override=_c2_for(c2_map, "store"))


def predict_total(group, ratios, c2_map=None):
  return (predict_dram(group, ratios, c2_map)
          + predict_cache(group, ratios, c2_map)
          + predict_store(group, ratios, c2_map))


# ---------- min-slowdown (closed-form on the cubic) ----------

# y(x) = d1*x + d2*x^2 + d3*x^3   (constant term is zero by construction)
# y'(x) = d1 + 2*d2*x + 3*d3*x^2  -- roots come from a quadratic

def cubic_coeffs(group, c_metric, l_metric, c2_override=None):
  """Return (d1, d2, d3) for the per-component prediction y(x).
  c2_override: if given, use as C2 and force L2 = L20 (r2 = 1)."""
  cyc1 = baseline_val(group, "cycles")
  C1 = _scalar_at(group, c_metric, BASELINE_RATIO)
  L1 = _scalar_at(group, l_metric, BASELINE_RATIO)
  if c2_override is not None:
    C2 = float(c2_override)
    L2 = L20
  else:
    C2 = _scalar_at(group, c_metric, ENDPOINT_RATIO)
    L2 = _scalar_at(group, l_metric, ENDPOINT_RATIO)
  r1 = L1 / L10
  r2 = L2 / L20
  A = C1 * (r1 - 1) / r1
  B = C1 / r1
  P = C2 * (r2 - 1) / r2
  Q = C2 / r2
  d1 = (-3 * A - B + Q) / cyc1
  d2 = 3 * A / cyc1
  d3 = (P - A) / cyc1
  return d1, d2, d3


def dram_coeffs(group, c2_map=None):
  return cubic_coeffs(group, "CYCLE_ACTIVITY.STALLS_L3_MISS", L2_ALL_RD_LATENCY,
                     c2_override=_c2_for(c2_map, "dram"))


def cache_coeffs(group, c2_map=None):
  return cubic_coeffs(group, CACHE_STALL, L2_PREF_LATENCY,
                     c2_override=_c2_for(c2_map, "cache"))


def store_coeffs(group, c2_map=None):
  return cubic_coeffs(group, "EXE_ACTIVITY.BOUND_ON_STORES", L2_DEMAND_RFO_LATENCY,
                     c2_override=_c2_for(c2_map, "store"))


def total_coeffs(group, c2_map=None):
  a = dram_coeffs(group, c2_map)
  b = cache_coeffs(group, c2_map)
  c = store_coeffs(group, c2_map)
  return (a[0] + b[0] + c[0], a[1] + b[1] + c[1], a[2] + b[2] + c[2])


def argmin_cubic_on_unit(d1, d2, d3):
  """Min of f(x) = d1*x + d2*x^2 + d3*x^3 on [0, 1] via closed-form roots of f'.
  Returns (x_min, y_min); NaN-safe."""
  if not (math.isfinite(d1) and math.isfinite(d2) and math.isfinite(d3)):
    return float("nan"), float("nan")
  def f(x):
    return d1 * x + d2 * x * x + d3 * x * x * x
  candidates = [0.0, 1.0]
  a, b, c = 3.0 * d3, 2.0 * d2, d1
  if abs(a) < 1e-300:
    if abs(b) > 1e-300:
      r = -c / b
      if 0.0 < r < 1.0:
        candidates.append(r)
  else:
    disc = b * b - 4.0 * a * c
    if disc >= 0.0:
      sd = math.sqrt(disc)
      for r in ((-b + sd) / (2.0 * a), (-b - sd) / (2.0 * a)):
        if 0.0 < r < 1.0:
          candidates.append(r)
  ys = [f(x) for x in candidates]
  i = int(np.argmin(ys))
  return candidates[i], ys[i]


def pred_min_continuous(coeffs_fn, group, c2_map=None):
  """Closed-form pred-min on x in [0, 1]. Returns (ratio_pct, y_min)."""
  d1, d2, d3 = coeffs_fn(group, c2_map=c2_map)
  x, y = argmin_cubic_on_unit(d1, d2, d3)
  return x * 100.0, y


def pred_min_at_measured(predictor_fn, group, ratios, c2_map=None):
  """Pred-min restricted to the measured ratios. Returns (ratio_pct, y_min)."""
  ys = np.asarray(predictor_fn(group, ratios, c2_map=c2_map), dtype=float)
  if np.all(np.isnan(ys)):
    return float("nan"), float("nan")
  i = int(np.nanargmin(ys))
  return float(ratios[i]) * 100.0, float(ys[i])


def meas_min(measured_arr, ratios):
  """Measured-min across the measured ratios. Returns (ratio_pct, y_min)."""
  arr = np.asarray(measured_arr, dtype=float)
  if np.all(np.isnan(arr)):
    return float("nan"), float("nan")
  i = int(np.nanargmin(arr))
  return float(ratios[i]) * 100.0, float(arr[i])


# Per-component metadata: predictor, cubic-coeffs builder, measured-key, plot stem.
Y_STALL_LABEL = "(stall - stall_L100) / cycles_L100"
COMPONENTS = [
  {"name": "dram",  "predictor": predict_dram,  "coeffs": dram_coeffs,
   "meas_key": "dram_sd",  "title": "DRAM slowdown",
   "ylabel": Y_STALL_LABEL, "stem": "sd_dram_pred"},
  {"name": "cache", "predictor": predict_cache, "coeffs": cache_coeffs,
   "meas_key": "cache_sd", "title": "Cache slowdown",
   "ylabel": Y_STALL_LABEL, "stem": "sd_cache_pred"},
  {"name": "store", "predictor": predict_store, "coeffs": store_coeffs,
   "meas_key": "store_sd", "title": "Store slowdown",
   "ylabel": Y_STALL_LABEL, "stem": "sd_store_pred"},
  {"name": "total", "predictor": predict_total, "coeffs": total_coeffs,
   "meas_key": "total",    "title": "Total slowdown",
   "ylabel": "slowdown vs L100", "stem": "sd_pred"},
]


def component_mins(group, ratios, measured_dict, c2_map=None):
  """One row per COMPONENTS entry with all three (y, ratio_pct) pairs."""
  rows = []
  for comp in COMPONENTS:
    cont_x,  cont_y  = pred_min_continuous(comp["coeffs"], group, c2_map=c2_map)
    pmeas_x, pmeas_y = pred_min_at_measured(comp["predictor"], group, ratios, c2_map=c2_map)
    mx, my           = meas_min(measured_dict[comp["meas_key"]], ratios)
    rows.append({
      "component": comp["name"],
      "pred_cont_y": cont_y,
      "pred_cont_ratio_pct": cont_x,
      "pred_meas_y": pmeas_y,
      "pred_meas_ratio_pct": pmeas_x,
      "meas_y": my,
      "meas_ratio_pct": mx,
    })
  return rows


# ---------- plotting ----------

def plot_pred(ratios, measured, predicted, title, ylabel, out_path):
  x = np.asarray(ratios, dtype=float) * 100.0
  fig, ax = plt.subplots(figsize=(7, 4.5))
  ax.plot(x, measured, "o-", label="measured", color="black",
          markersize=5, linewidth=1.0)
  ax.plot(x, predicted, "-", label="predicted", color="red", linewidth=1.5)
  ax.set_xlim(0, 100)
  ax.set_xlabel("Remote share (%)", fontsize=10)
  ax.set_ylabel(ylabel, fontsize=10)
  ax.set_title(title, fontsize=11)
  ax.axhline(0, color="black", linewidth=0.5)
  ax.grid(linestyle=":", linewidth=0.5, alpha=0.6)
  ax.legend(loc="best", prop={"size": 9})
  plt.tight_layout()
  os.makedirs(os.path.dirname(out_path), exist_ok=True)
  plt.savefig(out_path, dpi=130)
  plt.close(fig)


# ---------- external-C2 mode ----------

EXTERNAL_C2_COLS = ["workload", "dram_c2", "cache_c2", "store_c2"]


def load_external_c2(path):
  """Read consolidated CSV (cols: workload, dram_c2, cache_c2, store_c2).
  Returns dict: workload -> {'dram', 'cache', 'store': float}."""
  df = pd.read_csv(path)
  missing = set(EXTERNAL_C2_COLS) - set(df.columns)
  assert not missing, f"{path} missing columns: {sorted(missing)}"
  return {row["workload"]: {"dram":  float(row["dram_c2"]),
                            "cache": float(row["cache_c2"]),
                            "store": float(row["store_c2"])}
          for _, row in df.iterrows()}


# ---------- orchestration ----------

def process_workload(suite, workload, group, c2_map=None):
  ratios = get_ratios(group)
  if BASELINE_RATIO not in ratios:
    print(f"  skip {suite}/{workload}: no L100 baseline")
    return []
  if c2_map is None and ENDPOINT_RATIO not in ratios:
    print(f"  skip {suite}/{workload}: no L0 endpoint")
    return []
  cyc0 = baseline_val(group, "cycles")
  if np.isnan(cyc0) or cyc0 == 0:
    print(f"  skip {suite}/{workload}: bad baseline cycles")
    return []

  m = measured_slowdowns(group, ratios)
  preds = {c["name"]: c["predictor"](group, ratios, c2_map=c2_map) for c in COMPONENTS}

  stem = f"{suite}__{workload}"
  title = f"{suite}/{workload}"
  for comp in COMPONENTS:
    plot_pred(ratios, m[comp["meas_key"]], preds[comp["name"]],
              f"{title} - {comp['title']}", comp["ylabel"],
              os.path.join(PLOTS_DIR, f"{stem}__{comp['stem']}.png"))

  rows = component_mins(group, ratios, m, c2_map=c2_map)
  mode_tag = " [external C2]" if c2_map else ""
  print(f"{suite}/{workload} best ratios (y = slowdown, ratio% = remote share){mode_tag}:")
  print(f"  {'component':<8}  "
        f"{'pred_cont_y':>11}  {'ratio%':>6}    "
        f"{'pred_meas_y':>11}  {'ratio%':>6}    "
        f"{'meas_y':>11}  {'ratio%':>6}")
  for r in rows:
    print(f"  {r['component']:<8}  "
          f"{r['pred_cont_y']:>11.4f}  {r['pred_cont_ratio_pct']:>5.1f}%    "
          f"{r['pred_meas_y']:>11.4f}  {r['pred_meas_ratio_pct']:>5.1f}%    "
          f"{r['meas_y']:>11.4f}  {r['meas_ratio_pct']:>5.1f}%")
    r["suite"] = suite
    r["workload"] = workload
  return rows


def parse_args(argv=None):
  p = argparse.ArgumentParser(description="Cubic-fit prediction + best-ratio report.")
  p.add_argument("--c2-csv", default=None,
                 help="Path to CSV with external predicted C2 values per workload "
                      "(columns: workload, dram_c2, cache_c2, store_c2). If given, "
                      "only workloads listed in the CSV are processed and the L0 row "
                      "is not required; r2 = L2/L20 is forced to 1.")
  return p.parse_args(argv)


def main():
  args = parse_args()
  external_c2 = load_external_c2(args.c2_csv) if args.c2_csv else None
  if external_c2 is not None:
    print(f"Loaded external C2 for {len(external_c2)} workload(s) from {args.c2_csv}")

  try:
    df = load_df()
  except (FileNotFoundError, ValueError) as e:
    print(f"error: {e}")
    return

  os.makedirs(PLOTS_DIR, exist_ok=True)
  all_rows = []
  n_done = 0
  for (suite, workload), group in iter_workloads(df):
    if external_c2 is not None:
      if workload not in external_c2:
        print(f"  skip {suite}/{workload}: no external C2")
        continue
      c2_map = external_c2[workload]
    else:
      c2_map = None
    rows = process_workload(suite, workload, group, c2_map=c2_map)
    if rows:
      all_rows.extend(rows)
      n_done += 1

  if all_rows:
    os.makedirs(os.path.dirname(MIN_CSV_PATH), exist_ok=True)
    cols = ["suite", "workload", "component",
            "pred_cont_y", "pred_cont_ratio_pct",
            "pred_meas_y", "pred_meas_ratio_pct",
            "meas_y", "meas_ratio_pct"]
    pd.DataFrame(all_rows)[cols].to_csv(MIN_CSV_PATH, index=False)
    print(f"Wrote min-slowdown summary -> {MIN_CSV_PATH}")
  print(f"Done. {n_done} workload(s) plotted to {PLOTS_DIR}/")


if __name__ == "__main__":
  main()
