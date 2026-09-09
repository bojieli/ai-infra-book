"""Freeze natural lookup inputs before executing engines."""
import argparse
import hashlib
import json
from pathlib import Path
import time

parser=argparse.ArgumentParser();parser.add_argument('--model',required=True)
parser.add_argument('--out',type=Path,required=True);parser.add_argument('--smoke',action='store_true')
args=parser.parse_args();assert not args.out.exists()
from transformers import AutoTokenizer
tokenizer=AutoTokenizer.from_pretrained(args.model,local_files_only=True)
cases=[]
for rep in range(1 if args.smoke else 3):
    for target in ([2048] if args.smoke else [2048,8192]):
        for index,answer in enumerate(['AMBER'] if args.smoke else ['AMBER','VIOLET']):
            for kind in ['main','miss']:
                case_id=f'r{rep}-n{target}-a{index}-{kind}'
                header=f'Archive identifier {case_id}. The verified access code for station Orion is {answer}.\n'
                filler='Archive note: the weather station records temperature and rainfall every morning. This note does not change the verified access code.\n'
                def encode(count):
                    return tokenizer.apply_chat_template([
                        {'role':'system','content':'Read the archive and answer the lookup question. Reply with only the access code.'},
                        {'role':'user','content':header+filler*count+'\nWhat is the verified access code for station Orion?'}],
                        tokenize=True,add_generation_prompt=True,enable_thinking=False,return_dict=False)
                low,high=0,1000
                while low<high:
                    middle=(low+high+1)//2
                    if len(encode(middle))<=target:low=middle
                    else:high=middle-1
                ids=encode(low)
                cases.append(dict(id=case_id,rep=rep,target_tokens=target,kind=kind,
                                  expected=answer,prompt_token_ids=ids,
                                  input_tokens=len(ids),prompt_sha256=hashlib.sha256(json.dumps(ids).encode()).hexdigest()))
data=dict(created_unix=time.time(),model=args.model,smoke=args.smoke,cases=cases,
          warmup_token_ids=tokenizer.apply_chat_template([
              {'role':'user','content':'Reply with only OK.'}],tokenize=True,
              add_generation_prompt=True,enable_thinking=False,return_dict=False),
          sampling=dict(temperature=0,max_tokens=16),
          quality_gate='normal stop and text.strip() == expected; token IDs compared across main paths',
          order='all baseline cases; then for each main: producer, consumer retrieve, consumer resident, consumer novel miss',
          scope='same-host two independent engines, shared CPU KV; not cross-host network or per-step remote access')
args.out.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({'cases':len(cases),'sha256':hashlib.sha256(args.out.read_bytes()).hexdigest()}))
