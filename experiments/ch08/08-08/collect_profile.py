import json,os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
nsys=os.environ['NSYS']
for name in ['bf16','fp8']:
    out=root/'profiles'/name
    if out.exists():raise RuntimeError(f'Profile output already exists: {out}')
    out.parent.mkdir(exist_ok=True)
    command=[nsys,'profile','--trace=cuda,nvtx','--trace-fork-before-exec=true','--sample=none','--cpuctxsw=none',
        '--capture-range=cudaProfilerApi','--capture-range-end=stop',
        '--output='+str(out),sys.executable,str(root/'profile_run.py'),'--format',name,'--output',str(out)]
    with (out.parent/f'{name}.log').open('w') as f:
        subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
    subprocess.run([nsys,'export','--type=sqlite','--output='+str(out)+'.sqlite',str(out)+'.nsys-rep'],check=True)
    (out/'command.json').write_text(json.dumps(dict(command=command,version=subprocess.check_output([nsys,'--version'],text=True)),indent=2)+'\n')
    print(name,'profiled',flush=True)
