"""Synthetic scorer unit checks only. No model calls or experimental observations."""
import copy,importlib.util,json,pathlib,sys,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[3]
BASE=ROOT/'experiments/ch02/02-05/full-model-run'
sys.path.insert(0,str(BASE))
spec=importlib.util.spec_from_file_location('full_v4_score',BASE/'score.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
frozen=json.loads((BASE/'prepared/cases.json').read_text())
rows=[dict(case_id=c['id'],status='returned',input_ids=c['input_ids'],sampling_params=frozen['sampling'],response=dict(text=c['answer'],output_ids=[123,456],meta_info=dict(finish_reason=dict(type='stop',matched=128001)))) for c in frozen['cases']]
checks=[]
def check(name,mutate,expected=7):
 r=copy.deepcopy(rows);mutate(r)
 with tempfile.TemporaryDirectory(prefix='synthetic-',dir=pathlib.Path(__file__).parent) as d:
  p=pathlib.Path(d);(p/'cases.json').write_text(json.dumps(frozen));(p/'requests.json').write_text(json.dumps(r));m.score(p);s=json.loads((p/'scores.json').read_text())
  assert s['strict_success']==expected,(name,s['strict_success'],expected)
  checks.append(dict(name=name,expected_strict_success=expected,passed=True))
check('synthetic_all_normal_stop',lambda r:None,8)
check('not_returned',lambda r:r[0].update(status='in_flight'))
check('schema_error_present',lambda r:r[0].update(schema_error=None))
for kind in ['length','abort','unknown',None]:
 check('finish_'+str(kind),lambda r,k=kind:r[0]['response']['meta_info'].update(finish_reason={'type':k}))
check('finish_string_not_dict',lambda r:r[0]['response']['meta_info'].update(finish_reason='stop'))
check('missing_finish',lambda r:r[0]['response']['meta_info'].clear())
for ids in [[],[True],[1.0],[-1],None,['123']]:
 check('invalid_ids_'+repr(ids),lambda r,ids=ids:r[0]['response'].update(output_ids=ids))
check('missing_ids',lambda r:r[0]['response'].pop('output_ids'))
check('wrong_input',lambda r:r[0].update(input_ids=[123]))
check('bool_input',lambda r:r[0]['input_ids'].__setitem__(0,False))
check('wrong_sampling',lambda r:r[0].update(sampling_params={}))
check('wrong_answer',lambda r:r[0]['response'].update(text='wrong answer'))
check('missing_case',lambda r:r.pop(),0)
check('duplicate_case',lambda r:r.append(copy.deepcopy(r[0])),0)
check('unexpected_case',lambda r:r.append(dict(case_id='unknown')),0)
check('malformed_record',lambda r:r.append(None),0)
check('missing_response',lambda r:r[0].pop('response'))
check('no_records',lambda r:r.clear(),0)
report=dict(scope='SYNTHETIC scorer branch tests; fake output IDs are not model observations',checks=checks,count=len(checks),all_passed=True)
(pathlib.Path(__file__).parent/'synthetic-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(count=len(checks),all_passed=True)))
