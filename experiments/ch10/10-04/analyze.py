"""Read frozen author evidence only. No hardware model, GPU import or invented trace."""
import argparse,hashlib,json,pathlib,re
B=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
sources=json.loads((B/'sources.json').read_text())
for s in sources:
 data=(B/s['path']).read_bytes();assert len(data)==s['bytes'] and hashlib.sha256(data).hexdigest()==s['sha256']
comments=json.loads((B/'sources/pai-issue529-comments.json').read_text());c=next(c for c in comments if c['id']==2753325466)
assert c['author_association']=='COLLABORATOR' and '8*H20' in c['body']
rows=[]
for line in c['body'].splitlines():
 m=re.search(r'iteration\s+(\d+)/\s*(\d+).*elapsed time per iteration \(ms\): ([\d.]+).*global batch size:\s*(\d+).*lm loss: ([\d.E+\-]+)',line)
 if m:
  assert 'number of skipped iterations:   0' in line and 'number of nan iterations:   0' in line
  rows.append(dict(iteration=int(m[1]),planned_iterations=int(m[2]),elapsed_ms=float(m[3]),elapsed_s=float(m[3])/1000,global_batch=int(m[4]),lm_loss=float(m[5]),raw_line=line,source_comment_id=c['id']))
assert len(rows)==1 and rows[0]['iteration']==1 and rows[0]['elapsed_ms']==49449.5
raw=json.loads((B/'sources/swift-qwen235-discussion25.json').read_text())['events'][0]['data']['latest']['raw']
assert '(full-parameter training)' in raw and raw.count('--train_type lora')==2
commands=[s for s in re.findall(r'```shell\s*(.*?)```',raw,re.S) if 'megatron sft' in s]
assert len(commands)==2
parsed=[]
for cmd in commands:
 fields=dict(re.findall(r'--([a-z_]+)\s+([^\s\\]+)',cmd))
 parsed.append({k:fields.get(k) for k in ['train_type','lora_rank','lora_alpha','expert_model_parallel_size','pipeline_model_parallel_size','micro_batch_size','global_batch_size','max_length','optimizer_cpu_offload']})
assert parsed[0]['train_type']=='lora' and parsed[0]['optimizer_cpu_offload'] is None
assert parsed[1]['optimizer_cpu_offload']=='true'
for name in ['braille','a100-sft']:
 tree=json.loads((B/f'sources/{name}-tree.json').read_text());assert not tree.get('truncated')
 candidates=[x['path'] for x in tree['tree'] if x['type']=='blob' and any(w in x['path'].lower() for w in ['trainer_state','trainer_log','events.out.tfevents','.log','.jsonl','.csv'])]
 (a.out/f'{name}-trace-candidates.json').write_text(json.dumps(candidates,indent=2)+'\n')
result=dict(status='PARTIAL_SOURCE_READINESS_NOT_CROSS_HARDWARE_EXPERIMENT',original_target=['Qwen3-8B','Qwen3-235B'],raw_text_training_rows=rows,steady_state_step_estimate_s=None,cross_hardware_speedup=None,deadline_calibration_eligible=False,swift235_actual_commands=parsed,swift235_full_parameter_claim_conflicts_with_commands=True,scope='Only one author-posted first-iteration Moonlight H20 text line; screenshot values remain source images, not raw trace. Published summaries/configurations are separate evidence, not measured locally.')
(a.out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(sources_verified=len(sources),raw_training_rows=len(rows),steady_state=None,cross_hardware_calibration=False)))
