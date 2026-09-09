import json,os,random,socket,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;out=R/'results';out.mkdir(exist_ok=False)
order=[(world,reshard) for world in [2,4] for reshard in [0,1]];random.Random(1001).shuffle(order)
(out/'order.json').write_text(json.dumps(order)+'\n');rows=[]
for world,reshard in order:
 case=out/f'world{world}-reshard{reshard}';case.mkdir()
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 cmd=[sys.executable,'-m','torch.distributed.run','--nnodes=1',f'--nproc_per_node={world}','--master_addr=127.0.0.1',f'--master_port={port}',str(R/'worker.py'),'--output',str(case),'--reshard',str(reshard)]
 start=time.time()
 with (case/'run.log').open('x') as f:r=subprocess.run(cmd,env=dict(os.environ,GLOO_SOCKET_IFNAME='lo0',OMP_NUM_THREADS='1'),stdout=f,stderr=subprocess.STDOUT,timeout=600)
 row=dict(world=world,reshard=reshard,command=cmd,start=start,end=time.time(),exit_code=r.returncode);rows.append(row);(out/'execution.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(row),flush=True)
 if r.returncode:raise SystemExit(r.returncode)
