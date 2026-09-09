"""CPU stdlib independent sealed retrieval QA; never loads model or edits source."""
import hashlib,json,pathlib,statistics,subprocess,sys,tempfile,shutil
B=pathlib.Path(__file__).resolve().parents[3]/'ch13/13-01/retrieval-generation'
O=pathlib.Path(__file__).resolve().parent
J=lambda p:json.loads(p.read_text())
m=J(B/'manifest.json')
for f in m['files']:
 p=B/f['path'];assert p.stat().st_size==f['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256']
assert len(m['files'])==68 and sum(f['bytes'] for f in m['files'])==19591943
run=B/'runs/generation-001';d=run/'data';plan=J(B/'retrieval-001/prepared-prompts.json');refs={r['id']:r for r in plan['requests']};rows=J(d/'records.json');gold={r['id']:r for r in J(B/'queries.json')};quality=J(d/'quality.json');pa=J(d/'pipeline-analysis.json')
assert len(rows)==len(refs)==288
correct={}
for r in rows:
 ref=refs[r['id']];assert all(r[k]==ref[k] for k in ['config_id','query_id','split']);assert r['retrieval']['id']==r['id']
 assert r['retrieval']['prompt_token_ids']==ref['prompt_token_ids'];assert r['retrieval']['retrieved_doc_ids']==ref['retrieved_doc_ids']
 assert r['finish_reason']=='stop' and r['output_ids'][-1]==151645 and all(type(x)is int for x in r['output_ids'])
 correct[r['id']]=r['text'].strip()==gold[r['query_id']]['answer']
 assert r['generation_start_s']<=r['metrics']['queued_ts']
 assert all(r['generation_start_s']<=t<=r['end_s'] for t,n in r['events'])
 assert r['start_s']<=r['retrieval']['start_monotonic']<=r['retrieval']['end_monotonic']<=r['generation_start_s']<=r['end_s']
 assert abs(sum(r['retrieval'][k] for k in ['query_encoding_s','assembly_after_encoding_s','tokenization_s'])-r['retrieval']['cpu_pipeline_s'])<1e-8
 if not correct[r['id']]:assert r['text']=='UNKNOWN' and not ref['evidence_present']
assert sum(correct.values())==281
assert all(rows[i]['end_s']<=rows[i+1]['start_s'] for i in range(287))
assert [r['split'] for r in rows]==['calibration']*96+['evaluation']*192
for c in quality['cells']:
 rr=[r for r in rows if r['config_id']==c['config_id']]
 for split,key in [('calibration','calibration_correct'),('evaluation','evaluation_correct')]:assert sum(correct[r['id']] for r in rr if r['split']==split)==c[key]
for s in quality['calibration_selected']:
 eligible=[c for c in quality['cells'] if c['index']==s['index'] and c['efSearch']==s['efSearch'] and c['calibration_correct']==8]
 assert s['selected_config_id']==(min(eligible,key=lambda x:x['k'])['config_id'] if eligible else None)
 assert not s['heldout_pass']
assert quality['quality_eligible_config_ids']==[1,2,7,8,10,11]
assert sum(r['actual_scheduled_tokens'] for r in pa['records'])==162740
assert (pa['pool_blocks'],pa['reserved_pool_storage_bytes'],pa['bytes_per_pool_block'])==(910,2146959360,2359296)
for name,sha in J(d/'environment.json')['hashes'].items():assert hashlib.sha256((run/'executed-source'/name).read_bytes()).hexdigest()==sha
blocks=[json.loads(l) for l in (d/'blocks.jsonl').read_text().splitlines()]
byid={r['id']:r for r in rows};event_count=0
for b in blocks:
 for r in b['requests']:
  matches=[rid for rid in refs if r['id']==rid or r['id'].startswith(rid+'-')];assert len(matches)==1
  row=byid[matches[0]];assert row['generation_start_s']<=b['time_s']<=row['end_s'];event_count+=1
with tempfile.TemporaryDirectory(prefix='retrieval-review-') as td:
 t=pathlib.Path(td);shutil.copytree(run,t/'run')
 score=subprocess.run([sys.executable,str(B/'score_generation.py'),'--prompts',str(B/'retrieval-001/prepared-prompts.json'),'--records',str(d/'records.json'),'--out',str(t/'quality.json')],capture_output=True,text=True)
 assert score.returncode==0,score.stderr;assert (t/'quality.json').read_bytes()==(d/'quality.json').read_bytes()
 pipeline=subprocess.run([sys.executable,str(B/'analyze_generation.py'),'--run',str(t/'run'),'--prepared',str(B/'retrieval-001/prepared-prompts.json')],capture_output=True,text=True)
 assert pipeline.returncode==0,pipeline.stderr;assert (t/'run/data/pipeline-analysis.json').read_bytes()==(d/'pipeline-analysis.json').read_bytes()
 (O/'replay.log').write_text(score.stdout+pipeline.stdout)
result=dict(status='PASS',manifest_files=68,manifest_bytes=19591943,requests=288,strict_correct=281,unknown_missing_evidence=7,calibration_selected=quality['calibration_selected'],eligible_fixed_cells=quality['quality_eligible_config_ids'],scheduled_tokens=162740,native_request_events=event_count,heldout_eligible_groups=[g for g in pa['groups'] if g['split']=='evaluation' and g['config_id'] in quality['quality_eligible_config_ids']],score_replay_byte_identical=True,pipeline_replay_byte_identical=True,resource_scope='Old guard excludes untagged engine: GPU0 and tagged RSS are not full-task peaks; leftovers assertion has only that limited scope.')
(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
