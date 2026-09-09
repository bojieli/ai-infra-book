import json,subprocess,sys,concurrent.futures
from pathlib import Path
B=Path(__file__).absolute().parent
keys=['_step','_runtime','_timestamp','iteration_step','consumed_tokens','time_per_iteration_ms','tokens_per_sec','tokens_per_sec_per_gpu','model_tflops_per_gpu','lm_loss','lr']
spec=json.dumps({'keys':keys,'samples':1000})
def get(name):
 q='query { project(name:"SmolLM3-training-logs",entityName:"huggingface"){run(name:'+json.dumps(name)+'){name state sampledHistory(specs:['+json.dumps(spec)+'])}}}'
 r=subprocess.run([sys.executable,str(B/'query.py'),'wandb/history-'+name+'.json'],input=json.dumps({'query':q}),capture_output=True,text=True);assert r.returncode==0,r.stderr;return r.stdout
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:
 for result in p.map(get,['uliytlp7','28jt9vhg','8ey7uow0']):print(result.strip())
