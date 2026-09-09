import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--ncu',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise RuntimeError('Use a fresh output directory')
a.output.mkdir(parents=True)
metrics=['dram__bytes_op_read.sum','dram__bytes_op_write.sum','lts__t_bytes.sum','gpu__time_duration.sum']
records=[]
for m in [1,256]:
 for mode in ['reused','rotating']:
  label=f'm{m}-{mode}'
  command=['sudo','-n','env','PYTHONPATH='+os.pathsep.join(x for x in sys.path if x),a.ncu,
   '--target-processes','application-only','--profile-from-start','off','--replay-mode','application',
   '--cache-control','none','--clock-control','none','--metrics',','.join(metrics),'--export',str(a.output/label),
   sys.executable,str(ROOT/'counter_target.py'),'--m',str(m),'--mode',mode]
  with (a.output/f'{label}.log').open('w') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
  with (a.output/f'{label}.csv').open('w') as f:subprocess.run([a.ncu,'--import',str(a.output/f'{label}.ncu-rep'),'--page','raw','--csv','--print-units','base'],stdout=f,check=True)
  records.append(dict(m=m,mode=mode,label=label,command=command));print('Captured',label,flush=True)
(a.output/'collection.json').write_text(json.dumps(dict(records=records,metrics=metrics,ncu_version=subprocess.check_output([a.ncu,'--version'],text=True),
 source_hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['projection.py','counter_target.py','collect_counters.py']},
 scope='One target GEMM after 10 target warmups and 15 predecessor GEMMs. Application replay, normal cache and clock controls. Instrumented kernel times are separate from regular timing.'),indent=2)+'\n')
