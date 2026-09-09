"""Structural evidence verification only; no subprocess, GPU or mock execution."""
import ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
B=ROOT/'experiments/ch02/02-05/full-model-run'
if not B.is_dir():B=ROOT/'ch02/02-05/full-model-run'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
parsed=[]
for p in sorted(B.glob('*.py')):ast.parse(p.read_text(),filename=str(p));parsed.append(p.name)
frozen=json.loads((B/'prepared/cases.json').read_text());cases=frozen['cases'];t=json.loads((B/'prepared/tokenizer-evidence.json').read_text());m=json.loads((B/'prepared/model-metadata.json').read_text());r=json.loads((B/'prepared/resolved-serverargs.json').read_text())
assert len(cases)==8 and len({c['id'] for c in cases})==8
assert t['cases_sha256']==sha(B/'prepared/cases.json')
for c in cases:
 assert len(c['input_ids'])==c['prompt_tokens']
 assert c['prompt'].count(c['answer'])==1
 assert c['prompt'].endswith('<｜Assistant｜></think>')
 assert c['prompt_tokens']+frozen['sampling']['max_new_tokens']<4096
for target in (512,2048):
 for variant in ('A','B'):
  pair=[c for c in cases if c['target_tokens']==target and c['variant']==variant]
  assert {c['position'] for c in pair}=={'early','late'} and len({c['answer'] for c in pair})==1
  assert pair[0]['prompt'].replace(pair[0]['hidden_text']+'\n\n','')==pair[1]['prompt'].replace(pair[1]['hidden_text']+'\n\n','')
assert m['layers']==43 and m['shard_count']==48
assert m['disk_payload_bytes']==sum(s['bytes'] for s in m['shards'])
assert 'json_model_override_args' not in r['requested'] and r['resolved']['json_model_override_args']=='{}'
assert len(m['compress_ratios'])==46
assert all(x['matches_distribution_record'] for x in json.loads((B/'prepared/toolchain-audit.json').read_text())['source_records'])
assert not (B/'runs').exists()
result=dict(status='preparation_artifact_checks_passed_NOT_GPU_EXPERIMENT',parsed_scripts=parsed,cases=8,lengths=sorted({c['prompt_tokens'] for c in cases}),model_layers=43,weight_shards=48,source_record_matches=6,model_started=False,requests_executed=0)
(Path(__file__).parent/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
