"""Independent arithmetic only; no imported downloaded predictor implementation."""
import json
from pathlib import Path
from fractions import Fraction
pred=[8,2];actual=[6,4]
per_error=[abs(Fraction(p-a,a)) for p,a in zip(pred,actual)]
assert sum(pred)==sum(actual)==10
assert per_error==[Fraction(1,3),Fraction(1,2)]
util=Fraction(1,10)-Fraction(9,10)/1
assert util==Fraction(-4,5)
result={'scope':'Teaching arithmetic, not paper measurements or predictor execution.','predicted_stage_ms':pred,'actual_stage_ms':actual,'aggregate_absolute_percentage_error':0,'stage_absolute_percentage_errors':[float(x) for x in per_error],'second_stage_predicted_share':0.2,'second_stage_actual_share':0.4,'first_stage_halving_predicted_total_ms':6,'first_stage_halving_actual_total_ms':7,'positive_utilization_counterexample':{'gamma':0.1,'alpha':0.9,'num_wave':1,'utilization':float(util),'limitation':'Shows expression lacks a universal positive lower bound; does not show trained weights produce this output.'}}
Path(__file__).with_name('arithmetic.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('teaching arithmetic passed')
