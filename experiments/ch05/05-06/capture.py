import argparse,asyncio,hashlib,json,os
from pathlib import Path
async def main(out):
 os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0';root=Path(__file__).resolve().parent
 if out.exists():raise RuntimeError('Use fresh output directory')
 out.mkdir(parents=True)
 from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
 cfg=json.loads((root/'engine-config.json').read_text());task=json.loads((root/'input.json').read_text())
 engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**cfg));result={}
 try:
  result['installed']=await engine.collective_rpc('install_capture',args=(str((out/'tensors').resolve()),))
  final=None
  async for output in engine.generate({'prompt_token_ids':task['prompt_token_ids']},SamplingParams(temperature=0,max_tokens=2,ignore_eos=True),'capture'):final=output
  result['output_ids']=list(final.outputs[0].token_ids)
  result['records']=await engine.collective_rpc('capture_snapshot')
 finally:
  engine.shutdown();result['source_hashes']={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in ['capture.py','capture_worker.py','engine-config.json','input.json']}
  (out/'capture.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();asyncio.run(main(a.output))
