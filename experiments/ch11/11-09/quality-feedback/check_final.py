"""After model shutdown and raw transfer, run original holdout in bounded Linux children."""
import hashlib,json,os,resource,subprocess,sys,time
from pathlib import Path
from fixture import limits as original_limits
R=Path(__file__).resolve().parent

def limits():
 original_limits();resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,1024**2))
if __name__=='__main__':
 assert json.loads((R/'raw/exit.json').read_text())['remaining_owned']==[]
 for i,arm in enumerate(['baseline','feedback','feedback','baseline']):
  d=R/'raw'/f'{i}-{arm}';target=d/'independent-checks.json';assert not target.exists()
  start=time.monotonic();path=d/'workspace/intervals.py'
  p=subprocess.run([sys.executable,'-B',str(R/'check_code.py'),str(path),'--child'],capture_output=True,text=True,timeout=5,preexec_fn=limits)
  result=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,code_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),checker_sha256=hashlib.sha256((R/'check_code.py').read_bytes()).hexdigest(),elapsed_s=time.monotonic()-start,platform=sys.platform,affinity=sorted(os.sched_getaffinity(0)),limits=dict(cpu_s=2,address_space_bytes=512*1024**2,wall_s=5,file_bytes=1024**2))
  target.write_text(json.dumps(result,indent=2)+'\n')
