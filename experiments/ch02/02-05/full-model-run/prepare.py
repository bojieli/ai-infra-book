"""CPU tokenizer + argument resolution only. No Engine, no weight tensor reads."""
import argparse,dataclasses,importlib.util,importlib.metadata,os,shutil,sys
from pathlib import Path
from common import *
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 os.environ.update(PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',CUDA_HOME=str(TOOLS/'flashinfer-cuda130/nvidia/cu13'))
 save(a.out/'resource-before.json',snapshot())
 cfg=json.loads((MODEL/'config.json').read_text());index=json.loads((MODEL/'model.safetensors.index.json').read_text())
 assert cfg['num_hidden_layers']==43
 shards=[]
 for n in sorted(set(index['weight_map'].values())):
  f=MODEL/n;s=f.stat();shards.append(dict(name=n,target=str(f.resolve()),bytes=s.st_size,allocated_bytes=s.st_blocks*512,mtime_ns=s.st_mtime_ns))
 assert len(shards)==48 and all(x['bytes']>0 for x in shards)
 files=['config.json','generation_config.json','tokenizer_config.json','model.safetensors.index.json','encoding/encoding_dsv4.py','encoding/README.md']
 records=[]
 for n in files:
  dst=a.out/'metadata'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(MODEL/n,dst);records.append(dict(file=n,sha256=sha(dst)))
 save(a.out/'model-metadata.json',dict(status='metadata_and_stat_only_not_payload_integrity_check',revision=MODEL.name,model_path=str(MODEL),layers=43,compress_ratios=cfg['compress_ratios'],shards=shards,shard_count=len(shards),disk_payload_bytes=sum(x['bytes'] for x in shards),disk_allocated_bytes=sum(x['allocated_bytes'] for x in shards),index_metadata=index['metadata'],small_file_hashes=records,weight_payload_read=False))
 from transformers import AutoTokenizer
 spec=importlib.util.spec_from_file_location('encoding_dsv4',MODEL/'encoding/encoding_dsv4.py');encoding=importlib.util.module_from_spec(spec);spec.loader.exec_module(encoding)
 tok=AutoTokenizer.from_pretrained(str(MODEL),local_files_only=True,trust_remote_code=False)
 def encode(messages):
  prompt=encoding.encode_messages(messages,thinking_mode='chat');assert prompt.endswith('<｜Assistant｜></think>')
  ids=tok.encode(prompt,add_special_tokens=False);assert ids[0]==cfg['bos_token_id']
  return prompt,ids
 filler=[]
 subjects=['reading room','west garden','archive desk','workshop','riverside path','visitor hall','storage room','courtyard']
 actions=['The volunteers checked the shelves and returned the books before lunch.','The caretaker opened the windows while the staff arranged the chairs.','The team recorded the weather and discussed the schedule for the following week.','The coordinator reviewed the supply list and placed a paper copy near the entrance.']
 for i in range(180):filler.append(f'In note {i+1}, the {subjects[i%len(subjects)]} was quiet. {actions[(i//len(subjects))%len(actions)]}')
 cases=[]
 for target in (512,2048):
  for variant,project,answer in [('A','Cedar','violet lantern'),('B','Harbor','copper meadow')]:
   hidden=f'The sealed record for Project {project} states that its retrieval phrase is "{answer}". This is the only retrieval phrase recorded for that project.'
   def build(n,pos):
    paragraphs=filler[:n].copy();j=round(n*pos);paragraphs.insert(j,hidden)
    user='Read the following archive notes and find the requested fact.\n\n'+'\n\n'.join(paragraphs)+f'\n\nQuestion: What is the retrieval phrase for Project {project}? Reply with the phrase only, without quotes, explanation, or punctuation.'
    messages=[dict(role='system',content='Answer the question using only the supplied notes.'),dict(role='user',content=user)]
    prompt,ids=encode(messages);offset=prompt.index(hidden)
    return dict(messages=messages,prompt=prompt,input_ids=ids,prompt_tokens=len(ids),hidden_char_offset=offset,hidden_token_offset=len(tok.encode(prompt[:offset],add_special_tokens=False)),hidden_text=hidden,paragraph_count=n)
   # Select paragraph count once by content/token length, before model outputs.
   n=min(range(1,150),key=lambda n:abs(build(n,.15)['prompt_tokens']-target))
   for position,pos in [('early',.15),('late',.85)]:
    row=build(n,pos);assert abs(row['prompt_tokens']-target)<48;assert row['prompt_tokens']+32<4096
    cases.append(dict(id=f'retrieval-{target}-{variant}-{position}',quality_scope='natural_text_retrieval',variant=variant,target_tokens=target,position=position,answer=answer,**row))
 save(a.out/'cases.json',dict(status='frozen_before_any_model_execution',sampling=SAMPLING,cases=cases))
 save(a.out/'tokenizer-evidence.json',dict(tokenizer_class=type(tok).__name__,chat_template=tok.chat_template,encoder='original cached encoding/encoding_dsv4.py:encode_messages(thinking_mode="chat")',add_special_tokens=False,bos_id=tok.bos_token_id,eos_id=tok.eos_token_id,tokenizer_json_sha256=sha(MODEL/'tokenizer.json'),cases_sha256=sha(a.out/'cases.json'),lengths=[dict(id=c['id'],tokens=c['prompt_tokens'],hidden_token_offset=c['hidden_token_offset']) for c in cases]))
 import torch
 from sglang.srt.server_args import ServerArgs
 args=ServerArgs(**CONFIG)
 assert args.json_model_override_args=='{}' and args.context_length==4096 and args.swa_full_tokens_ratio==1.0
 save(a.out/'resolved-serverargs.json',dict(status='ServerArgs_resolution_only_NO_engine_NO_model_NO_requests',requested=CONFIG,resolved=vars(args),torch=torch.__version__,versions={d.metadata['Name']:d.version for d in importlib.metadata.distributions() if any(x in d.metadata['Name'].lower() for x in ['sglang','torch','transformers','tilelang','tvm','triton','flashinfer','cuda','nvidia'])},CUDA_HOME=os.environ['CUDA_HOME']))
 dist=importlib.metadata.distribution('sglang');sources=[]
 for rel in ['sglang/srt/server_args.py','sglang/srt/arg_groups/deepseek_v4_hook.py','sglang/srt/utils/offloader.py','sglang/srt/models/deepseek_v4.py','sglang/srt/model_executor/pool_configurator.py','sglang/srt/entrypoints/engine.py']:
  f=Path(dist.locate_file(rel))
  if not f.exists():
   matches=list(Path(dist.locate_file('sglang/srt')).rglob(Path(rel).name));assert len(matches)==1;f=matches[0]
  dst=a.out/'sources'/f.relative_to(Path(dist.locate_file('')));dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dst)
  sources.append(dict(path=str(f),saved=str(dst.relative_to(a.out)),sha256=sha(f)))
 save(a.out/'sources.json',sources)
 save(a.out/'resource-after.json',snapshot())
 save(a.out/'completion.json',dict(status='PREPARED_ONLY_PENDING_ROOT_EXECUTION',model_started=False,requests_executed=0,case_sha256=sha(a.out/'cases.json'),candidate=CONFIG,limits=LIMITS))
if __name__=='__main__':main()
