"""Prepare actual V4 tokenizer inputs only; never creates an inference engine."""
import argparse,json,hashlib,importlib.util,math,time
from pathlib import Path
from transformers import AutoTokenizer
ROOT=Path(__file__).absolute().parent
p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('encoding_dsv4',a.model/'encoding/encoding_dsv4.py');encoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(encoder)
t=AutoTokenizer.from_pretrained(str(a.model),local_files_only=True,trust_remote_code=False);cases=[]
for task in json.loads((ROOT/'tasks.json').read_text()):
 text=encoder.encode_messages(task['messages'],thinking_mode='chat');ids=t.encode(text,add_special_tokens=False);assert t.decode(ids)==text and ids[0]==t.bos_token_id
 cases.append(dict(id=task['id'],messages=task['messages'],input_ids=ids,prompt=text,prompt_tokens=len(ids),qwen_prompt_tokens=len(task['prompt_token_ids']),expected=task['expected']))
needed=max(len(c['input_ids']) for c in cases)+128;context=math.ceil(needed/1024)*1024
result=dict(status='tokenizer_prepared_only',requests_executed=0,model_revision=a.model.name,task_sha256=hashlib.sha256((ROOT/'tasks.json').read_bytes()).hexdigest(),encoder_sha256=hashlib.sha256((a.model/'encoding/encoding_dsv4.py').read_bytes()).hexdigest(),tokenizer_sha256=hashlib.sha256((a.model/'tokenizer.json').read_bytes()).hexdigest(),sampling=dict(temperature=0,top_p=1,top_k=1,max_new_tokens=128,ignore_eos=False),cases=cases,required_input_plus_output=needed,proposed_context=context,scope='Actual tokenizer lengths; proposed context is not verified KV pool capacity or model execution',prepared_at_unix=time.time())
(a.out/'cases.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(lengths=[c['prompt_tokens'] for c in cases],required=needed,proposed_context=context)))
