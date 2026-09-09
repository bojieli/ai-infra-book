"""Installed-runtime config experiment; never instantiate an engine or load weights."""
import dataclasses, hashlib, importlib.metadata, inspect, json, os, time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
from vllm.engine.arg_utils import EngineArgs
B=Path(__file__).absolute().parent
MODEL=Path('/home/ubuntu/.cache/huggingface/hub/models--Qwen--Qwen3-VL-30B-A3B-Instruct-FP8/snapshots/d9748a51ae66354c4dad665aab2c71f26cf2c8cd')
sources=B/'sources';sources.mkdir(exist_ok=True)
source_index=[]
for name in ['vllm.engine.arg_utils','vllm.config.parallel','vllm.config.vllm']:
    module=__import__(name,fromlist=['x']);p=Path(inspect.getfile(module));data=p.read_bytes()
    dst=sources/(name+'.py');dst.write_bytes(data)
    source_index.append(dict(module=name,installed_path=str(p),sha256=hashlib.sha256(data).hexdigest()))
raw=(MODEL/'config.json').read_bytes();(B/'model-config.json').write_bytes(raw)
files=[]
for p in sorted(MODEL.glob('*.safetensors')):
    st=p.stat();files.append(dict(name=p.name,path=str(p.resolve()),bytes=st.st_size,mtime_ns=st.st_mtime_ns))
fields={f.name for f in dataclasses.fields(EngineArgs)}
base=dict(model=str(MODEL),dtype='auto',tensor_parallel_size=1,pipeline_parallel_size=1,
          max_model_len=4096,max_num_seqs=1,enforce_eager=True,enable_prefix_caching=False,
          limit_mm_per_prompt={'image':0,'video':0},seed=906)
variants=[('baseline',{}),('eplb',{'enable_expert_parallel':True,'enable_eplb':True}),
          ('dbo',{'enable_expert_parallel':True,'enable_dbo':True}),
          ('eplb_dbo',{'enable_expert_parallel':True,'enable_eplb':True,'enable_dbo':True})]
rows=[]
for name,extra in variants:
    config=base|extra
    missing=sorted(set(config)-fields)
    row=dict(name=name,requested=config,unsupported_argument_names=missing,engine_created=False,model_requests=0)
    if missing:row.update(status='argument_not_available')
    else:
        try:
            resolved=EngineArgs(**config).create_engine_config()
            row.update(status='config_created_not_execution_validated',parallel_config=dataclasses.asdict(resolved.parallel_config),
                       model_architectures=resolved.model_config.architectures,
                       quantization=resolved.model_config.quantization)
        except Exception as exc:
            row.update(status='config_rejected',exception_type=type(exc).__name__,reason=str(exc))
    rows.append(row)
report=dict(captured_unix=time.time(),driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            versions={n:importlib.metadata.version(n) for n in ['vllm','torch','transformers']},sources=source_index,
            model_revision=MODEL.name,model_config_sha256=hashlib.sha256(raw).hexdigest(),weight_file_metadata=files,
            variants=rows,scope='No engine, weight tensor read, CUDA kernel, routing or timing measurement; config acceptance is not runtime support proof')
(B/'readiness.json').write_text(json.dumps(report,indent=2,default=str)+'\n')
print(json.dumps([dict(name=r['name'],status=r['status'],reason=r.get('reason')) for r in rows]))
