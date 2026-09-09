"""Persistent CPU-only real retrieval stage for root's generator pipeline.

stdin JSONL {id}; stdout one ready object then one response per request.
Logs/warnings go to stderr. No server or GPU is created.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['TOKENIZERS_PARALLELISM']='false'
import argparse,hashlib,json,time,sys
from pathlib import Path
import faiss,numpy as np,torch
from transformers import AutoModel,AutoTokenizer
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--retrieval',type=Path,required=True);p.add_argument('--model',type=Path,required=True);a=p.parse_args()
start=time.monotonic();P=json.loads((B/'protocol.json').read_text());plan=json.loads((a.retrieval/'prepared-prompts.json').read_text());requests={r['id']:r for r in plan['requests']};docs=json.loads((B/'corpus.json').read_text());queries={r['id']:r for r in json.loads((B/'queries.json').read_text())}
torch.set_num_threads(4);torch.set_num_interop_threads(1);faiss.omp_set_num_threads(4)
et=AutoTokenizer.from_pretrained(B/'encoder',local_files_only=True);encoder=AutoModel.from_pretrained(B/'encoder',local_files_only=True).eval().cpu();qt=AutoTokenizer.from_pretrained(a.model,local_files_only=True)
indexes={n:faiss.read_index(str(a.retrieval/f'{n}.faiss')) for n in ['flat','hnsw']}
print(json.dumps(dict(status='ready',load_s=time.monotonic()-start,pid=os.getpid(),torch=torch.__version__,faiss=faiss.__version__,cpu_only=True)),flush=True)
for line in sys.stdin:
 command=json.loads(line)
 if command.get('stop'):break
 req=requests[command['id']];config=plan['configs'][req['config_id']];query=queries[req['query_id']];t=time.monotonic()
 with torch.inference_mode():
  b=et(query['question'],return_tensors='pt',truncation=False);h=encoder(**b).last_hidden_state;mask=b['attention_mask'].unsqueeze(-1);v=torch.nn.functional.normalize((h*mask).sum(1)/mask.sum(1),p=2,dim=1).numpy()
 enc_end=time.monotonic();idx=indexes[config['index']]
 if config['efSearch'] is not None:idx.hnsw.efSearch=config['efSearch']
 s=time.perf_counter_ns();dist,indices=idx.search(np.ascontiguousarray(v,dtype=np.float32),config['k']);search_ns=time.perf_counter_ns()-s
 selected=[docs[i] for i in indices[0]];doc_ids=[d['id'] for d in selected]
 assert doc_ids==req['retrieved_doc_ids'], 'Online query encoding/search changed frozen selected documents'
 context='\n\n'.join(f'Document {j+1}: {d["text"]}' for j,d in enumerate(selected))
 messages=[dict(role='system',content='Answer the question using only the supplied station register. Return only the complete two-word handover phrase. If the relevant station record is absent, return exactly UNKNOWN.'),dict(role='user',content=f'{context}\n\nQuestion: {query["question"]}')]
 assembled=time.monotonic();ids=qt.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,enable_thinking=False,return_dict=False);end=time.monotonic()
 assert ids==req['prompt_token_ids'], 'Online assembled prompt differs from frozen prompt'
 print(json.dumps(dict(id=req['id'],prompt_token_ids=ids,input_tokens=len(ids),retrieved_doc_ids=doc_ids,retrieval_scores=dist[0].tolist(),query_encoding_s=enc_end-t,search_ns=search_ns,assembly_after_encoding_s=assembled-enc_end,tokenization_s=end-assembled,cpu_pipeline_s=end-t,start_monotonic=t,end_monotonic=end,observed=True)),flush=True)
