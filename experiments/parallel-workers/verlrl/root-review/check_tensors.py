from pathlib import Path
import json,torch
B=Path('/Users/boj/book/ai-infra-book/experiments/ch10/10-08');torch.set_num_threads(2);files=0;tensors=0
for mode in ['main','control']:
 d=B/mode;e=json.loads((d/'tensor-export.json').read_text())['tensor_files'];actual={p.name:p for p in (d/'observations').glob('*.pt')};assert set(e)==set(actual)
 for name,p in actual.items():
  x=torch.load(p,map_location='cpu',weights_only=True);assert set(x)==set(e[name])
  for k,t in x.items():
   y=e[name][k];assert str(t.dtype)==y['dtype'] and list(t.shape)==y['shape'] and t.tolist()==y['values'],(mode,name,k);tensors+=1
  files+=1
out=dict(files=files,tensors=tensors,all_raw_tensors_equal_export=True,torch=torch.__version__);Path(__file__).with_name('tensor-checks.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
