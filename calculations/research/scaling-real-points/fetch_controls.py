"""Fetch only official metadata and small training/evaluation scripts, never weights."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen
import json

ROOT=Path(__file__).resolve().parent
REPOS=['lm1-misc','lm1-2b8-55b-c4-repetitions','lm1-4b2-84b-c4-repetitions','lm1-8b7-178b-c4-repetitions']
def fetch(repo):
    p=ROOT/'hub'/repo;p.mkdir(parents=True,exist_ok=True)
    raw=(p/'api.json').read_bytes() if (p/'api.json').exists() else urlopen('https://huggingface.co/api/models/datablations/'+repo).read();(p/'api.json').write_bytes(raw)
    j=json.loads(raw);revision=j['sha']
    paths=[x['rfilename'] for x in j['siblings'] if x['rfilename'].endswith(('.sh','.sbatch')) and any(x['rfilename'].split('/')[0].startswith(row['record_id']) for row in json.loads((ROOT/'candidate-points.json').read_text()))]
    # All matching small scripts, but not arbitrary weight/binary files.
    for f in paths:
        if 'tokenizer' in f or 'vocab' in f:continue
        data=urlopen(f'https://huggingface.co/datablations/{repo}/resolve/{revision}/{f}').read()
        target=p/f;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    return repo,revision,paths
with ThreadPoolExecutor(max_workers=4) as pool:
    for result in pool.map(fetch,REPOS):print(result)
