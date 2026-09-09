"""Resolve installed SGLang arguments without constructing an engine/model."""
import base64,hashlib,importlib.metadata,json,os
from pathlib import Path
import torch
from sglang.srt.server_args import ServerArgs

root=Path(__file__).parent
model='/home/ubuntu/.cache/huggingface/hub/models--deepseek-ai--DeepSeek-V4-Flash-0731/snapshots/7872f01b1d1fe23eabc4c98b48bffcef5a386062'
args=ServerArgs(model_path=model,dtype='bfloat16',cpu_offload_gb=110,
                context_length=2048,max_total_tokens=4096,max_running_requests=1,
                chunked_prefill_size=256,mem_fraction_static=.9,
                disable_cuda_graph=True,port=18205)
fields=['model_path','dtype','cpu_offload_gb','context_length','max_total_tokens',
        'max_running_requests','chunked_prefill_size','mem_fraction_static',
        'moe_runner_backend','attention_backend','kv_cache_dtype','page_size',
        'disable_cuda_graph','disable_piecewise_cuda_graph','port']
flags=['SGLANG_OPT_FP8_WO_A_GEMM','SGLANG_OPT_USE_TOPK_V2','SGLANG_OPT_USE_TILELANG_MHC_PRE',
       'SGLANG_OPT_DEEPGEMM_HC_PRENORM','SGLANG_FP8_PAGED_MQA_LOGITS_TORCH']
dist=importlib.metadata.distribution('sglang');records=[]
for relative in ['sglang/srt/models/deepseek_v4.py','sglang/srt/server_args.py',
                 'sglang/srt/layers/quantization/mxfp4_marlin_moe.py',
                 'sglang/srt/layers/moe/fused_moe_triton/mxfp4_moe_sm120_triton.py',
                 'sglang/srt/utils/offloader.py']:
    p=Path(dist.locate_file(relative));body=p.read_bytes()
    expected=next((f.hash.value for f in dist.files if str(f)==relative and f.hash),None)
    actual=base64.urlsafe_b64encode(hashlib.sha256(body).digest()).decode().rstrip('=')
    dst=root/'config-sources'/relative;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(body)
    records.append(dict(path=relative,sha256=hashlib.sha256(body).hexdigest(),record_sha256=expected,
                        matches_dist_record=(actual==expected) if expected else None))
result=dict(status='arguments_resolved_only_no_model_or_inference',
            torch=torch.__version__,torch_path=torch.__file__,sglang=dist.version,
            gpu=torch.cuda.get_device_name(),capability=torch.cuda.get_device_capability(),
            args={k:getattr(args,k) for k in fields},flags={k:os.environ.get(k) for k in flags},sources=records)
(root/'resolved-config.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
