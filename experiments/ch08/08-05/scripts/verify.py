import json,pathlib,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1];checks=[]
def check(name,ok,detail=None):checks.append(dict(check=name,passed=bool(ok),detail=detail))
for line in (ROOT/'evidence/transfer-sha256.txt').read_text().splitlines():
 h,n=line.split(maxsplit=1);check('transferred_sha256:'+n,hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h)
for line in (ROOT/'evidence/installed-source-sha256.txt').read_text().splitlines():
 h,n=line.split(maxsplit=1);f=ROOT/'evidence'/('official-vllm_'+n.split('/vllm/')[1].replace('/','_'));check('official_installed_sha256:'+n,hashlib.sha256(f.read_bytes()).hexdigest()==h)
inputs_hash=hashlib.sha256((ROOT/'inputs.json').read_bytes()).hexdigest();rr={}
for mode in ['ar','dflash-7','dflash-15']:
 ev=[json.loads(x) for x in (ROOT/'raw'/mode/'events.jsonl').read_text().splitlines()]
 check(mode+':normal_exit',(ROOT/'raw'/f'{mode}.exit').read_text().strip()=='0' and sum(e['kind']=='success' for e in ev)==1)
 check(mode+':input_hash',all(e['input_sha256']==inputs_hash for e in ev if e['kind']=='configuration'))
 res=[e for e in ev if e['kind']=='result'];rr[mode]={e['request_id']:e for e in res if e['phase']=='measured'}
 check(mode+':counts',len(res)==24 and len(rr[mode])==16 and len(set(e['request_id'] for e in res))==24)
 check(mode+':natural_stop',all(e['finish_reason']=='stop' and len(e['token_ids'])<128 for e in res))
 check(mode+':ttft_wall',all(0<e['ttft_s']<=e['wall_s'] for e in res))
 ss=[e['scheduler']['spec_decoding_stats'] for e in ev if e['kind']=='stats' and e.get('scheduler') and e['scheduler'].get('spec_decoding_stats')]
 check(mode+':acceptance_invariants',all(0<=s['num_accepted_tokens']<=s['num_draft_tokens'] and sum(s['num_accepted_tokens_per_pos'])==s['num_accepted_tokens'] for s in ss))
 if mode!='ar':check(mode+':real_draft_stats',len(ss)>0 and sum(s['num_drafts'] for s in ss)>0)
 peak=json.loads((ROOT/'results/summary.json').read_text())[mode]['sampled_peak_MiB'];check(mode+':sampled_under_24GiB',peak is not None and peak<24576,peak)
 check(mode+':single_gpu_pid',len({e['pid'] for e in ev if e['kind']=='preflight'})==1)
for mode in ['dflash-7','dflash-15']:
 check(mode+':all_measured_token_equal',set(rr[mode])==set(rr['ar']) and all(v['token_ids']==rr['ar'][k]['token_ids'] for k,v in rr[mode].items()))
# Quality failures are scientific outcomes; report separately, never turn them into a successful task claim.
quality={m:{'strict_pass':sum(v['quality_pass'] for v in rs.values()),'n':len(rs),'failures':[{'id':k,'text':v['text'],'expected':v['expected']} for k,v in rs.items() if not v['quality_pass']]} for m,rs in rr.items()}
result={'scope':'仅本worker产物QA，非跨session最终审计','checks':checks,'quality':quality}
(ROOT/'results/validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('Checks:',len(checks),'passed:',sum(c['passed'] for c in checks));assert all(c['passed'] for c in checks)
