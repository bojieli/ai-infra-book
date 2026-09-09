"""Run the final native configuration in a fresh sibling directory, preserving old evidence."""
from pathlib import Path
import argparse,shutil,subprocess,sys
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--name',required=True,help='New directory basename under this experiment');a=p.parse_args()
if not a.name or Path(a.name).name!=a.name or a.name in ('.','..'):p.error('Use a fresh simple directory basename')
cccl=Path('/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/lib/python3.10/site-packages/nvidia/cu13/include/cccl')
assert (cccl/'nv/target').is_file(),'Required existing CCCL headers unavailable'
overlay=B/'include-overlay';overlay.mkdir(exist_ok=True);link=overlay/'cccl'
if not link.exists():link.symlink_to(cccl,target_is_directory=True)
assert link.resolve()==cccl.resolve(),'Unexpected include overlay'
d=B/a.name;d.mkdir(exist_ok=False)
for name in ['run.py','launch.py']:shutil.copy2(B/'attempt-05'/name,d/name)
for source, target in [('jit-preflight/tvm-cache', 'cache/tvm'), ('jit-mhc-preflight/tilelang-cache', 'cache/tilelang')]:
 shutil.copytree(B/source, d/target)
raise SystemExit(subprocess.call([sys.executable,'-B',str(d/'launch.py')],cwd=d))
