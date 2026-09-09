import json,tempfile
from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location('original_tools', 'tools-linux-original.py')
tools=importlib.util.module_from_spec(spec);spec.loader.exec_module(tools)
f=json.loads(Path('fixture.json').read_text())['fixture']
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)
 for n,k in [('intervals.py','INITIAL'),('test_intervals.py','CHECKER'),('SPEC.txt','SPEC')]: (p/n).write_text(f[k])
 try: result=tools.execute({'tool':'run_tests'},p)
 except Exception as e: result={'error':type(e).__name__+': '+str(e)}
 Path('compatibility-probe.json').write_text(json.dumps(result,indent=2)+'\n')
 print(result)
