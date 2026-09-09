import hashlib,json,os,pathlib,shutil,subprocess,tempfile
O=pathlib.Path(__file__).resolve().parent;R=O.parents[3];B=R/'experiments/ch11/11-04';P=R/'experiments/tools/mlx-runner-venv/bin/python'
results=[]
with tempfile.TemporaryDirectory(prefix='offline-replay-',dir=O) as t:
 c=pathlib.Path(t)/'experiment';shutil.copytree(B,c)
 for name in ['formal','smoke']:
  env=os.environ.copy();env.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='',USE_TORCH='0',USE_TF='0',USE_FLAX='0')
  run=subprocess.run([str(P),'-B',str(c/'analyze.py'),'--name',name],env=env,text=True,capture_output=True)
  (O/(name+'-replay.log')).write_text(run.stdout+run.stderr);assert run.returncode==0,run.stderr
  for file in ['checks.json','summary.json']:
   assert (B/name/file).read_bytes()==(c/name/file).read_bytes(),(name,file)
  results.append(dict(name=name,exit_code=run.returncode,checks=json.loads((c/name/'summary.json').read_text())['checks'],checks_and_summary_byte_identical=True))
(O/'replay-checks.json').write_text(json.dumps(dict(status='passed',model_loaded=False,results=results),indent=2)+'\n');print(results)
