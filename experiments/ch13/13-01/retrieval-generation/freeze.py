"""Freeze authored synthetic station records, questions and protocol before retrieval."""
import hashlib,json,random
from pathlib import Path
B=Path(__file__).resolve().parent
adj='amber azure bronze coral crimson crystal emerald golden granite indigo ivory jade lavender lemon lilac lunar maple maroon misty mossy olive opal orange pearl ruby russet scarlet silver slate snowy teal violet'.split()
noun='badger beaver bison crane dolphin eagle falcon finch fox gecko heron ibex ibis jaguar kestrel koala lark lynx marten otter owl panda pelican puffin raven robin salmon seal sparrow swan tern wren'.split()
assert len(adj)==len(noun)==32
rng=random.Random(130120260909)
permutation=list(range(1024));rng.shuffle(permutation)
docs=[]
for i in range(1024):
 name=f'{adj[i//32]} {noun[i%32]}'
 secret=permutation[i];answer=f'{adj[secret//32]} {noun[secret%32]}'
 docs.append(dict(id=f'doc-{i:04d}',station=name,answer=answer,text=f'Station register: {name}. The authorized handover phrase for the {name} station is "{answer}". This phrase is the complete two-word answer to handover enquiries. The register describes a fictional station used only in this experiment. Its routine includes checking the logbook, recording the weather and closing the supply cupboard.'))
indices=rng.sample(range(1024),24)
queries=[dict(id=f'q-{j:02d}',split='calibration' if j<8 else 'evaluation',doc_id=docs[i]['id'],question=f'What is the authorized handover phrase for the {docs[i]["station"]} station?',answer=docs[i]['answer']) for j,i in enumerate(indices)]
protocol=dict(seed=130120260909,corpus_kind='authored synthetic fictional facts; not a natural benchmark',encoder='sentence-transformers/all-MiniLM-L6-v2',encoder_revision='1110a243fdf4706b3f48f1d95db1a4f5529b4d41',representation='actual pretrained encoder attention-mask mean pooling, FP32 L2 normalization',metric='inner_product_on_unit_vectors',faiss_version='1.12.0',cpu_threads=4,hnsw_M=8,efConstruction=40,efSearch=[4,16,64],k=[1,4,16],query_repetitions=11,search_order_seed=130113,quality_gate='8/8 calibration exact answer then 16/16 held-out evaluation exact answer; never relax after seeing results',selection='Within each retriever configuration select smallest k passing all calibration questions; ties unchanged k. Report held-out results for every preregistered cell and label only cells passing both gates eligible. No latency winner without matched quality.',generation_model='Qwen/Qwen3-8B',generation_revision='b968826d9c46dd6066d109eabc6255188de91218',temperature=0,max_tokens=32,thinking=False,prefix_cache=False,concurrency=1,query_variants_after_freeze=False,metric_limits='Search wall measured, encoding/build/storage measured. TTFT is application-stream first nonempty output, not prefill kernel. Prefill/KV require actual server observations; missing fields remain null.')
for name,obj in [('corpus.json',docs),('queries.json',queries),('protocol.json',protocol)]:
 p=B/name
 if p.exists():raise FileExistsError(p)
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
