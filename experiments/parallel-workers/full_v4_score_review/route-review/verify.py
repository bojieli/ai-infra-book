"""Read-only actual route evidence checks; no model or GPU imports."""
import collections,hashlib,json,pathlib,shutil,subprocess,sys,tempfile
O=pathlib.Path(__file__).resolve().parent;B=O.parents[3]/'experiments/ch06/06-03';R=B/'runs/routes-001'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bindings=read(B/'reference/source-bindings.json');scheduler_sha=sha(B/'reference/scheduler.py');assert scheduler_sha==bindings['installed-source:sglang/srt/managers/scheduler.py']
requests={r['case_id']:r for r in read(R/'requests.json')};frozen={r['id']:r for r in read(R/'cases.json')['cases']};reference={r['case_id']:r for r in read(B/'reference/requests.json')}
assert len(requests)==len(frozen)==4
batches=[]
for p in (R/'routes').glob('*-batches.jsonl'):
 batches.extend(json.loads(x) for x in p.read_text().splitlines())
counts=collections.Counter();report_cases=[];valid_total=0;assignment_total=0;layerrows=0;duplicate_rows=0
for b in batches:
 case=b['request_phase']['case_id'];r=requests[case];valid=b['num_token_non_padded_cpu'];assert b['host_start']>=r['sent_monotonic'];assert b['host_start']<=b['model_host_return']<=b['observer_sync_end']<=b['observer_copy_end']<=r['sent_monotonic']+r['request_wall_s'];assert [x['layer_id'] for x in b['routes']]==list(range(43));assert valid==len(b['input_ids'])==len(b['positions']);valid_total+=valid
 for layer in b['routes']:
  assert layer['router_class']==('HashTopK' if layer['layer_id']<3 else 'TopK')
  assert len(layer['ids'])==valid;layerrows+=valid
  for ids in layer['ids']:
   assert len(ids)==6 and all(type(i)is int and 0<=i<256 for i in ids);duplicate_rows+=len(set(ids))!=6;assignment_total+=len(ids)
   counts[(case,b['mode'],layer['layer_id'])]+=len(ids)
for case,r in requests.items():
 bs=sorted([b for b in batches if b['request_phase']['case_id']==case],key=lambda b:b['sequence']);pre=[b for b in bs if b['is_extend']];dec=[b for b in bs if b['is_decode']]
 assert [i for b in pre for i in b['input_ids']]==frozen[case]['input_ids']==r['input_ids']
 assert [i for b in dec for i in b['input_ids']]==r['response']['output_ids'];assert dec[-1]['input_ids']==[1]
 assert [i for b in bs for i in b['positions']]==list(range(len(r['input_ids'])+len(r['response']['output_ids'])))
 assert r['response']['meta_info']['finish_reason']=={'type':'stop','matched':1}
 for k in ('output_ids','text'):assert r['response'][k]==reference[case]['response'][k]
 assert r['response']['text'].strip()==frozen[case]['answer']
 for layer in range(43):
  assert counts[(case,'EXTEND',layer)]==len(r['input_ids'])*6
  assert counts[(case,'DECODE',layer)]==len(r['response']['output_ids'])*6
 report_cases.append(dict(case_id=case,prompt_tokens=len(r['input_ids']),prefill_batches=len(pre),decode_batches=len(dec),output_ids=r['response']['output_ids'],extra_terminal_eos_forward=True,last_position=dec[-1]['positions'][0],first_forward_after_request_s=bs[0]['host_start']-r['sent_monotonic'],last_copy_before_response_s=r['sent_monotonic']+r['request_wall_s']-bs[-1]['observer_copy_end']))
assert (len(batches),valid_total,layerrows,assignment_total,duplicate_rows)==(36,5090,218870,1313220,0)
with tempfile.TemporaryDirectory(prefix='offline-route-replay-',dir=O) as temp:
 p=pathlib.Path(temp);shutil.copyfile(B/'analyze.py',p/'analyze.py');shutil.copytree(B/'reference',p/'reference');shutil.copytree(R,p/'run',symlinks=True)
 proc=subprocess.run([sys.executable,'-B',str(p/'analyze.py'),'--out',str(p/'run')],text=True,capture_output=True);(O/'replay.log').write_text(proc.stdout+proc.stderr);assert proc.returncode==0,proc.stderr
 exact=(p/'run/route-analysis.json').read_bytes()==(R/'route-analysis.json').read_bytes();assert exact,'Derived analysis differs; check concurrent analyzer refresh'
report=dict(status='passed',base_analyzer_sha256=sha(B/'analyze.py'),scheduler_sha256=scheduler_sha,scheduler_matches_source_binding=True,replay_exit0=True,replay_byte_identical=True,batches=len(batches),layer_records=len(batches)*43,consumed_tokens=valid_total,valid_token_layer_rows=layerrows,assignments=assignment_total,rows_with_duplicate_experts=duplicate_rows,cases=report_cases,raw_route_sha256={p.name:sha(p) for p in (R/'routes').glob('*-batches.jsonl')},scope='Independent read-only checks and CPU-only temporary analyzer replay; no generation or GPU imports')
(O/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['cases','raw_route_sha256']}))
