"""Offline deterministic scoring. Never runs or retries inference."""
import argparse,json,re
from pathlib import Path
from common import save
def score(out):
 frozen=json.loads((out/'cases.json').read_text());rows=json.loads((out/'requests.json').read_text()) if (out/'requests.json').exists() else []
 assert isinstance(rows,list),'requests.json must contain a list'
 frozen_ids=[c['id'] for c in frozen['cases']]
 assert len(frozen_ids)==len(set(frozen_ids)),'Frozen case IDs must be unique'
 by={};unexpected=[];malformed=[];scores=[]
 for index,r in enumerate(rows):
  if not isinstance(r,dict) or not isinstance(r.get('case_id'),str):malformed.append(index);continue
  if r['case_id'] not in frozen_ids:unexpected.append(r['case_id'])
  by.setdefault(r['case_id'],[]).append(r)
 duplicate_ids=sorted(k for k,v in by.items() if len(v)!=1)
 record_set_valid=not (unexpected or malformed or duplicate_ids) and set(by)==set(frozen_ids)
 for case in frozen['cases']:
  matches=by.get(case['id'],[]);r=matches[0] if len(matches)==1 else {};raw=r.get('response');response=raw if isinstance(raw,dict) else {};text=response.get('text');raw_meta=response.get('meta_info');meta=raw_meta if isinstance(raw_meta,dict) else {};finish=meta.get('finish_reason');kind=finish.get('type') if isinstance(finish,dict) else None
  ids=response.get('output_ids');output_ids_valid=isinstance(ids,list) and bool(ids) and all(type(x) is int and x>=0 for x in ids)
  valid=isinstance(text,str) and output_ids_valid and isinstance(finish,dict) and isinstance(kind,str) and 'schema_error' not in r
  input_ids=r.get('input_ids');input_matches=isinstance(input_ids,list) and all(type(x) is int and x>=0 for x in input_ids) and input_ids==case['input_ids']
  sampling_matches=r.get('sampling_params')==frozen['sampling'];returned=r.get('status')=='returned';normal_finish=kind=='stop'
  exact=bool(valid and text.strip()==case['answer']);truncated=kind=='length'
  scores.append(dict(case_id=case['id'],target_tokens=case['target_tokens'],actual_prompt_tokens=case['prompt_tokens'],position=case['position'],variant=case['variant'],answer=case['answer'],record_count=len(matches),returned=returned,schema_valid=valid,schema_error=r.get('schema_error'),output_ids_valid=output_ids_valid,input_matches_frozen=input_matches,sampling_matches_frozen=sampling_matches,finish_reason=finish,normal_finish=normal_finish,truncated=truncated,exact_match=exact,strict_success=bool(record_set_valid and returned and exact and input_matches and sampling_matches and normal_finish),format_error=bool(isinstance(text,str) and not re.fullmatch(r'[a-z]+ [a-z]+',text.strip())),request_wall_s=r.get('request_wall_s')))
 log=(out/'run.log').read_text(errors='replace') if (out/'run.log').exists() else ''
 pool_lines=[l for l in log.splitlines() if 'DSV4 pool sizes:' in l or 'DSV4 memory calculation:' in l or 'Load weight end' in l or 'KV Cache' in l]
 save(out/'pool-log-evidence.json',dict(source='actual_engine_stdout_only',lines=pool_lines,observed=bool(pool_lines)))
 save(out/'scores.json',dict(scope='four_fixed_natural_text_retrieval_cases_not_general_quality_or_numerical_validation',denominator=len(scores),record_set_valid=record_set_valid,duplicate_case_ids=duplicate_ids,unexpected_case_ids=unexpected,malformed_record_indices=malformed,returned_count=sum(x['returned'] for x in scores),schema_valid_count=sum(x['schema_valid'] for x in scores),normal_finish_count=sum(x['normal_finish'] for x in scores),strict_success=sum(x['strict_success'] for x in scores),exact_match=sum(x['exact_match'] for x in scores),cases=scores,calibration=None,strict_numerical_clearance=False,request_wall_scope='Application envelope: includes the requests.json write before engine.generate; not isolated generation or transfer time.',cpu_offload_overhead=dict(candidate_gib=110,isolated_transfer_time_s=None,isolated_overhead_s=None,reason='Uninstrumented official OffloaderV1 transfers are included in initialization/request wall time; no zero-offload matched control or transfer profiler, so overhead cannot be isolated.'),shared_host_state='resource-before/after.json and watchdog.jsonl; sampled shared contention, no exclusive-host performance claim'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);score(p.parse_args().out)
