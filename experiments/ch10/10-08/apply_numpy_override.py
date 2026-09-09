"""Apply the single pinned wheel override in the private environment only."""
import json,os,pathlib,subprocess
root=pathlib.Path(os.environ['VERLRL_ROOT']);src=pathlib.Path(os.environ['VERLRL_SOURCE'])
assert str(src).startswith('/home/ubuntu/ai-infra-book-experiments/tools/verl-private/')
spec=json.loads((root/'numpy-override.json').read_text());wheel=spec['wheels'][0]
uv='/home/ubuntu/.local/bin/uv';python=str(src/'.venv/bin/python')
subprocess.run([uv,'pip','install','--python',python,'--no-deps','numpy @ '+wheel['url']+'#sha256='+wheel['sha256']],check=True)
subprocess.run([uv,'pip','check','--python',python],check=True)
