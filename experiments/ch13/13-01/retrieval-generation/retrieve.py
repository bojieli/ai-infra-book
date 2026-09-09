"""Actual CPU encoder, Faiss indexes and frozen search sweep. No generation."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['TOKENIZERS_PARALLELISM']='false'
import argparse,hashlib,json,random,time,resource
from pathlib import Path
import numpy as np
import torch,faiss
from transformers import AutoModel,AutoTokenizer
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
P=json.loads((B/'protocol.json').read_text());docs=json.loads((B/'corpus.json').read_text());queries=json.loads((B/'queries.json').read_text())
def save(n,x):(a.out/n).write_text(json.dumps(x,indent=2)+'\n')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
save('preregistration.json',dict(time=time.time(),files={n:sha(B/n) for n in ['protocol.json','corpus.json','queries.json','retrieve.py']},protocol=P))
for r in json.loads((B/'encoder/manifest.json').read_text())['files']:assert sha(B/'encoder'/r['file'])==r['sha256']
assert faiss.__version__==P['faiss_version']
torch.set_num_threads(4);torch.set_num_interop_threads(1);faiss.omp_set_num_threads(4)
t=time.monotonic();tok=AutoTokenizer.from_pretrained(B/'encoder',local_files_only=True);model=AutoModel.from_pretrained(B/'encoder',local_files_only=True).eval().cpu();load_s=time.monotonic()-t
assert not any(p.is_cuda for p in model.parameters())
def encode(texts,name):
 out=[];raw=[];t=time.monotonic()
 with torch.inference_mode():
  for start in range(0,len(texts),32):
   text=texts[start:start+32];lengths=[len(tok(s,add_special_tokens=True)['input_ids']) for s in text];assert max(lengths)<=256,'No silent truncation'
   batch=tok(text,padding=True,truncation=False,return_tensors='pt');h=model(**batch).last_hidden_state
   mask=batch['attention_mask'].unsqueeze(-1);pooled=(h*mask).sum(1)/mask.sum(1).clamp(min=1)
   norm=torch.nn.functional.normalize(pooled,p=2,dim=1);out.append(norm.numpy().copy());raw.extend(lengths)
 arr=np.ascontiguousarray(np.concatenate(out),dtype=np.float32);assert arr.shape[1]==384 and np.allclose(np.linalg.norm(arr,axis=1),1,atol=2e-6)
 np.save(a.out/f'{name}.npy',arr);return arr,dict(seconds=time.monotonic()-t,token_lengths=raw,dtype=str(arr.dtype),shape=list(arr.shape))
X,corpus_time=encode([d['text'] for d in docs],'corpus-vectors');Q,query_time=encode([q['question'] for q in queries],'query-vectors')
indexes={};build=[]
for name in ['flat','hnsw']:
 t=time.monotonic()
 if name=='flat':idx=faiss.IndexFlatIP(384)
 else:
  idx=faiss.IndexHNSWFlat(384,P['hnsw_M'],faiss.METRIC_INNER_PRODUCT);idx.hnsw.efConstruction=P['efConstruction']
 idx.add(X);elapsed=time.monotonic()-t;f=a.out/f'{name}.faiss';faiss.write_index(idx,str(f));indexes[name]=idx
 build.append(dict(index=name,build_s=elapsed,serialized_bytes=f.stat().st_size,sha256=sha(f),ntotal=idx.ntotal,dimension=idx.d,metric='IP',vector_dtype='float32'))
configs=[dict(index='flat',efSearch=None,k=k) for k in P['k']]+[dict(index='hnsw',efSearch=ef,k=k) for ef in P['efSearch'] for k in P['k']]
schedule=[(c,q,rep) for c in range(len(configs)) for q in range(len(queries)) for rep in range(P['query_repetitions'])];random.Random(P['search_order_seed']).shuffle(schedule)
# Explicit one-call warmup per config, excluded from formal search times.
for c in configs:
 idx=indexes[c['index']]
 if c['efSearch'] is not None:idx.hnsw.efSearch=c['efSearch']
 idx.search(Q[:1],c['k'])
rows=[]
for ci,qi,rep in schedule:
 c=configs[ci];idx=indexes[c['index']]
 if c['efSearch'] is not None:idx.hnsw.efSearch=c['efSearch']
 t=time.perf_counter_ns();scores,ids=idx.search(Q[qi:qi+1],c['k']);ns=time.perf_counter_ns()-t
 rows.append(dict(config_id=ci,query_id=queries[qi]['id'],repeat=rep,search_ns=ns,ids=ids[0].tolist(),scores=scores[0].tolist()))
save('searches.json',rows)
# Independent exact dense-vector reference for Flat. Ties explicitly allowed.
reference=Q.astype(np.float64)@X.astype(np.float64).T
for r in rows:
 if configs[r['config_id']]['index']!='flat':continue
 qi=next(i for i,q in enumerate(queries) if q['id']==r['query_id']);ids=r['ids'];assert all(0<=i<len(docs) for i in ids)
 threshold=np.partition(reference[qi],-len(ids))[-len(ids)];assert min(reference[qi,ids])>=threshold-2e-6
 assert np.allclose(reference[qi,ids],r['scores'],rtol=0,atol=2e-6)
# Request evidence uses repeat zero; all repeat route stability checked.
requests=[]
for ci,c in enumerate(configs):
 for q in queries:
  rr=[r for r in rows if r['config_id']==ci and r['query_id']==q['id']];chosen=next(r for r in rr if r['repeat']==0)
  assert all(r['ids']==chosen['ids'] for r in rr)
  selected=[docs[i] for i in chosen['ids']]
  context='\n\n'.join(f'Document {j+1}: {d["text"]}' for j,d in enumerate(selected))
  system='Answer the question using only the supplied station register. Return only the complete two-word handover phrase. If the relevant station record is absent, return exactly UNKNOWN.'
  user=f'{context}\n\nQuestion: {q["question"]}'
  requests.append(dict(id=f'c{ci:02d}-{q["id"]}',config_id=ci,query_id=q['id'],split=q['split'],retrieved_doc_ids=[d['id'] for d in selected],evidence_present=q['doc_id'] in [d['id'] for d in selected],messages=[dict(role='system',content=system),dict(role='user',content=user)],search_ns=chosen['search_ns']))
save('generation-plan.json',dict(configs=configs,requests=requests,order='calibration before evaluation; config/query schedule randomized within split by fixed seed'))
save('preparation.json',dict(status='actual_CPU_retrieval_complete_generation_unrun',torch=torch.__version__,faiss=faiss.__version__,numpy=np.__version__,encoder_load_s=load_s,corpus_encoding=corpus_time,query_encoding=query_time,indexes=build,formal_searches=len(rows),ru_maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,strict_flat_fp64_control=True))
print(json.dumps(dict(searches=len(rows),requests=len(requests),evidence_hits=sum(r['evidence_present'] for r in requests))))
