import argparse,json
from pathlib import Path
from transformers import AutoTokenizer
p=argparse.ArgumentParser();p.add_argument('--model',required=True);args=p.parse_args();root=Path(__file__).absolute().parent
t=AutoTokenizer.from_pretrained(args.model,local_files_only=True);n=0
for f in (root/'runs/preserved-001').glob('r*/requests.jsonl'):
 for x in map(json.loads,f.read_text().splitlines()):
  assert x['output_ids'][-1]==t.eos_token_id
  assert t.decode(x['output_ids'],skip_special_tokens=True)==x['text'];n+=1
(root/'tokenizer-check.json').write_text(json.dumps(dict(requests=n,decode_exact=n,eos_exact=n),indent=2)+'\n');print(n)
