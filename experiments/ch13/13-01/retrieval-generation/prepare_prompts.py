"""CPU-only fixed Qwen tokenizer and schedule; starts no inference engine."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import argparse,hashlib,json,random
from pathlib import Path
from transformers import AutoTokenizer
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--retrieval',type=Path,required=True);p.add_argument('--model',type=Path,required=True);a=p.parse_args()
P=json.loads((B/'protocol.json').read_text());assert a.model.name==P['generation_revision']
plan=json.loads((a.retrieval/'generation-plan.json').read_text());tok=AutoTokenizer.from_pretrained(a.model,local_files_only=True)
rows=[]
for r in plan['requests']:
 ids=tok.apply_chat_template(r['messages'],tokenize=True,add_generation_prompt=True,enable_thinking=False,return_dict=False)
 assert isinstance(ids,list) and all(type(i)is int for i in ids)
 row={k:v for k,v in r.items() if k!='messages'}
 row.update(prompt_token_ids=ids,input_tokens=len(ids),prompt_sha256=hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest())
 rows.append(row)
rng=random.Random(P['search_order_seed']);ordered=[]
for split in ['calibration','evaluation']:
 part=[r for r in rows if r['split']==split];rng.shuffle(part);ordered.extend(part)
d=dict(protocol_sha256=hashlib.sha256((B/'protocol.json').read_bytes()).hexdigest(),generation_model_revision=P['generation_revision'],thinking=False,sampling=dict(temperature=0,top_p=1,max_tokens=32,seed=130113),configs=plan['configs'],tokenizer_hashes={n:hashlib.sha256((a.model/n).read_bytes()).hexdigest() for n in ['tokenizer.json','tokenizer_config.json','config.json']},requests=ordered)
(a.retrieval/'prepared-prompts.json').write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps(dict(requests=len(ordered),min_tokens=min(r['input_tokens'] for r in rows),max_tokens=max(r['input_tokens'] for r in rows))))
