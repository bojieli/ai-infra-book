import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
subprocess.run(['python3','prepare.py'],cwd=ROOT,check=True)
for case in ['first','middle']:
 with (ROOT/f'{case}.log').open('x') as log:
  subprocess.run(['sh','launch.sh','--phase',case,'--output',f'results/{case}','--storage',f'storage-{case}'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
