import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
nsys=os.environ['NSYS']
for mode in ['native','schedule']:
    out=ROOT/'profiles'/mode
    if out.exists():raise RuntimeError('Fresh output required')
    out.parent.mkdir(exist_ok=True)
    command=[nsys,'profile','--trace=cuda,nvtx','--trace-fork-before-exec=true','--sample=none','--cpuctxsw=none','--capture-range=cudaProfilerApi','--capture-range-end=stop','--output='+str(out),sys.executable,str(ROOT/'profile_run.py'),'--mode',mode,'--output',str(out)]
    with (out.parent/f'{mode}.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run([nsys,'export','--type=sqlite','--output='+str(out)+'.sqlite',str(out)+'.nsys-rep'],check=True)
    (out/'command.json').write_text(json.dumps(dict(command=command,version=subprocess.check_output([nsys,'--version'],text=True)),indent=2)+'\n')
    print(mode,'complete',flush=True)
