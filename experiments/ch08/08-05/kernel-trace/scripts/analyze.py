import json,pathlib,collections,bisect,hashlib
P=pathlib.Path(__file__).resolve().parents[1]; R=P/'results';R.mkdir(exist_ok=True)
def read(p):return [json.loads(s) for s in p.read_text().splitlines()]
summary={};requests=[];steps=[];checks=[];kernelrows=[];forwardrows=[];proposals=[]
for mode in ['ar','dflash-7','dflash-15']:
 e=read(P/'raw'/mode/'events.jsonl');ref=read(P.parent/'raw'/mode/'events.jsonl')
 results=[x for x in e if x['kind']=='result' and x['phase']=='observed']
 assert len(results)==4
 for x in results:
  rr=[y for y in ref if y['kind']=='result' and y['phase']=='measured' and y['task_id']==x['task_id']]
  eq=all(y['token_ids']==x['token_ids'] and y['text']==x['text'] and y['finish_reason']==x['finish_reason'] for y in rr)
  checks.append({'check':mode+'/'+x['task_id']+'/reference_tokens','pass':bool(rr) and eq});requests.append({'mode':mode,**x,'reference_equal':eq})
 b=[x for x in e if x['kind']=='boundary']
 forward={x['step']:x for x in b if x['boundary']=='GPUModelRunner._model_forward'}
 for x in b:
  if x['boundary']=='SpecDecodeBaseProposer.propose':proposals.append({'mode':mode,**x})
  if x['boundary']=='GPUModelRunner._model_forward':
   offset=0
   for rid in x['request_ids']:
    n=x['scheduled'][rid]
    forwardrows.append({'mode':mode,'step':x['step'],'request_id':rid,'external_request_id':rid[:-9],'actual_rows':n,'positions':x['positions'][offset:offset+n],'batch_input_shape':x['input_shape']});offset+=n
   checks.append({'check':mode+'/step'+str(x['step'])+'/forward_rows','pass':offset==x['input_shape'][0]})
 rej={x['step']:x for x in b if x['boundary'].endswith('.rejection_sample')}
 prep={x['step']:x for x in b if x['boundary']=='SpecDecodeBaseProposer.prepare_inputs_padded'}
 effective={x['step']:x for x in b if x['boundary']=='DFlashProposer.set_inputs_first_pass'}
 for x in b:
  if x['boundary']!='RejectionSampler.forward':continue
  m=x['metadata'];offset=0;j=rej[x['step']]; f=forward[x['step']]
  for i,(rid,n) in enumerate(zip(x['request_ids'],m['num_draft_tokens'])):
   draft=m['draft_token_ids'][offset:offset+n]; target=j['target_argmax'][offset:offset+n]; offset+=n
   mismatch=next((k for k in range(n) if draft[k]!=target[k]),None)
   accepted=n if mismatch is None else mismatch
   valid=[v for v in x['sampled_token_ids'][i] if v>=0]
   good=len(valid)==accepted+1 and valid[:accepted]==draft[:accepted] and (mismatch is None or valid[-1]==target[mismatch])
   checks.append({'check':f'{mode}/step{x["step"]}/{rid}/greedy_chain','pass':good})
   p=prep.get(x['step']); eff=effective.get(x['step']); mapped=p is not None and p['request_ids']==x['request_ids']
   if mapped:
    checks.append({'check':f'{mode}/step{x["step"]}/{rid}/rejected_count','pass':p['num_rejected'][i]==n-accepted})
    checks.append({'check':f'{mode}/step{x["step"]}/{rid}/effective_context','pass':eff['seq_lens_after'][i]-(int(mode.split('-')[1])+1)==eff['seq_lens_before'][i]-p['num_rejected'][i]})
   row={'mode':mode,'step':x['step'],'request_id':rid,'external_request_id':rid[:-9],'actual_draft_tokens':draft,'target_argmax':target,'verify_rows':n+1,'verify_logits_shape_batch':x['logits_shape'],'target_forward_shape_batch':f['input_shape'],'target_scheduled_rows':f['scheduled'][rid],'accepted_draft_length':accepted,'first_reject_index_0based':mismatch,'fallback_token':None if mismatch is None else valid[-1],'sampled_before_stop_filter':valid,'rejected_count':p['num_rejected'][i] if mapped else 'unknown','context_seq_before':eff['seq_lens_before'][i] if mapped else 'unknown','effective_context_seq':eff['seq_lens_after'][i]-(int(mode.split('-')[1])+1) if mapped else 'unknown'}
   steps.append(row)
 t=json.loads((P/'raw'/mode/'trace.json').read_text())['traceEvents']
 ranges=[x for x in t if x.get('ph')=='X' and (x.get('name','').startswith('stage/') or x.get('name','').startswith('obs.readback'))]
 runtimes={x.get('args',{}).get('correlation'):x for x in t if x.get('cat') in ['cuda_runtime','cuda_driver'] and 'correlation' in x.get('args',{})}
 counts=collections.Counter();duration=collections.Counter();names=collections.Counter();unmatched=0
 for x in t:
  if x.get('cat') not in ['kernel','gpu_memcpy','gpu_memset']:continue
  rt=runtimes.get(x.get('args',{}).get('correlation'));candidates=[]
  if rt:
   candidates=[r for r in ranges if r['tid']==rt['tid'] and r['ts']<=rt['ts']<=r['ts']+r['dur']]
  obs=[r for r in candidates if r['name'].startswith('obs.')]
  selected=min(obs or candidates,key=lambda r:r['dur']) if candidates else None
  stage=selected['name'].split('/step=')[0] if selected else 'unattributed'
  if stage.startswith('obs.'):stage='observation_readback'
  key=stage+'|'+x['cat']; counts[key]+=1;duration[key]+=x.get('dur',0);names[x['name']]+=1
  kernelrows.append({'mode':mode,'stage':stage,'category':x['cat'],'name':x['name'],'gpu_duration_us':x.get('dur',0),'correlation':x.get('args',{}).get('correlation'),'ts_us':x['ts']})
  if not selected:unmatched+=1
 cpu=collections.defaultdict(list)
 for x in ranges:
  if x['name'].startswith('stage/'):cpu[x['name'].split('/step=')[0]].append(x['dur'])
 peak=max([int(line.split(',')[1]) for x in e if x['kind']=='gpu_memory' for line in x['processes'].splitlines() if int(line.split(',')[0])==next(z['pid'] for z in e if z['kind']=='preflight')],default=0)
 summary[mode]={'results':len(results),'quality_pass':sum(x['quality_pass'] for x in results),'gpu_activity_counts':dict(counts),'gpu_duration_us_sum':dict(duration),'unattributed_activities':unmatched,'cpu_stage_inclusive_us_sum':{k:sum(v) for k,v in cpu.items()},'peak_sampled_MiB':peak,'torch_peak_reserved':max(x['torch_peak_reserved'] for x in e if x['kind']=='batch_complete'),'kernel_names':dict(names)}
 checks += [{'check':mode+'/success','pass':any(x['kind']=='success' for x in e) and (P/'raw'/f'{mode}.exit').read_text().strip()=='0'}, {'check':mode+'/gpu_kernels','pass':any('|kernel' in k for k in counts)},{'check':mode+'/memory_sample','pass':peak<=24576}]
for name,obj in [('summary',summary),('requests',requests),('steps',steps),('checks',checks),('gpu-activities',kernelrows),('forward-rows',forwardrows),('proposals',proposals)]:
 (R/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
print(json.dumps({'checks':len(checks),'passed':sum(x['pass'] for x in checks),'steps':len(steps),'requests':len(requests)}))
assert all(x['pass'] for x in checks)
