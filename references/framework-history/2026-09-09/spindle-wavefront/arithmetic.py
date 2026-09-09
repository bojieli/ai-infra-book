"""Independent teaching arithmetic; no imports from downloaded framework code."""
from fractions import Fraction
import json
from pathlib import Path

# Explicit invented profiles; they are not Spindle or GPU measurements.
profiles = {'A': {1: 12, 2: 6, 4: 3}, 'B': {1: 6, 2: 4.5, 4: 4}}
shared_tail_ms = 8
serial_ms = profiles['A'][4] + profiles['B'][4] + shared_tail_ms
split_before_handoff_ms = max(profiles['A'][2], profiles['B'][2]) + shared_tail_ms
threshold_ms = serial_ms - split_before_handoff_ms
assert (serial_ms, split_before_handoff_ms, threshold_ms) == (15,14,1)
# A mathematical counterexample to the printed theorem's stated assumptions only.
static = Fraction(1, 1**2)
time_division = 2 * Fraction(1, 2**2)
assert time_division < static
# Complete restart cost, not planning alone; all values below are teaching assumptions.
reconfiguration_s = 3 + 20 + 35 + 2
saving_s_per_step = Fraction(1, 20)
strict_break_even_steps = int(Fraction(reconfiguration_s,1) / saving_s_per_step) + 1
assert reconfiguration_s == 60 and strict_break_even_steps == 1201
result = {
 'scope':'Independent arithmetic on explicit teaching assumptions; no source code, model, simulator or GPU run.',
 'branch_profiles_ms':profiles,'shared_tail_ms':shared_tail_ms,
 'serial_ms':serial_ms,'split_before_incremental_handoff_ms':split_before_handoff_ms,
 'incremental_handoff_break_even_ms':threshold_ms,
 'split_with_0_25_ms_handoff_ms':split_before_handoff_ms+0.25,
 'split_with_3_ms_handoff_ms':split_before_handoff_ms+3,
 'printed_theorem_counterexample':{'tasks':2,'resources':2,'T':'1/n^2, n>0','static_equal_allocation_time':float(static),'serial_full_allocation_time':float(time_division),'claim':'Positive non-increasing T alone does not establish the printed static-equal-finish optimum; no assertion that all paper experiments are invalid.'},
 'restart_teaching_budget':{'planning_s':3,'save_s':20,'load_s':35,'group_and_warmup_s':2,'total_s':reconfiguration_s,'saving_per_step_s':float(saving_s_per_step),'tie_steps':1200,'strictly_profitable_steps':strict_break_even_steps}
}
Path(__file__).with_name('arithmetic.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
