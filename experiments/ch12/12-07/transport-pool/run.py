"""Build and run the pinned native Queqiao benchmark in ABBA order."""
import hashlib,json,os,platform,subprocess,time
from pathlib import Path
BASE=Path(__file__).absolute().parent

def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
    lock=json.loads((BASE/'source-lock.json').read_text())
    for r in lock['files']:
        data=(BASE/'source'/r['path']).read_bytes()
        assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
    out=BASE/'runs';out.mkdir(exist_ok=False)
    env=os.environ.copy();env['GOTOOLCHAIN']='auto'
    binary=out/'queqiaobench'
    cmd=['go','build','-buildvcs=false','-o',str(binary),'./cmd/queqiaobench']
    with (out/'build.log').open('w') as f:subprocess.run(cmd,cwd=BASE/'source',env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=600)
    save(out/'environment.json',dict(platform=platform.platform(),machine=platform.machine(),revision=lock['revision'],build_command=cmd,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),build_info=subprocess.check_output(['go','version','-m',str(binary)],text=True)))
    for i,pool in enumerate([True,False,False,True]):
        d=out/f'{i}-pool-{str(pool).lower()}';d.mkdir()
        cmd=[str(binary),'--stacks=baseline,queqiao','--rtt=40','--rate=100','--queue=500000','--loss=0','--bytes=355000','--seed=1207','--trials=1','--flows=1,4','--congestion=bbr-tuic','--latency','--timeout=30s',f'--quic-pool={str(pool).lower()}','--json='+str(d/'raw.json')]
        start=time.time()
        with (d/'stdout.log').open('w') as so,(d/'stderr.log').open('w') as se:
            p=subprocess.run(cmd,cwd=BASE/'source',env=env,stdout=so,stderr=se,timeout=360)
        save(d/'execution.json',dict(command=cmd,start_unix_s=start,end_unix_s=time.time(),exit_code=p.returncode))
        assert p.returncode==0
        raw=json.loads((d/'raw.json').read_text())
        print(i,pool,'bulk',[(r['stack'],r['flows'],r['complete']) for r in raw['trials']],flush=True)
    binary.unlink()
if __name__=='__main__':main()
