"""Bounded counterexamples. Shared project files are read only; network is mocked."""
from pathlib import Path
import tempfile,json,hashlib,sys
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'src'))
from infra_calc.schema import Weight,Operator,Scenario,linear
from infra_calc.units import positive_number
from infra_calc import sources,reproduce
out=[]
for name,f in [('Weight bool dimension',lambda:Weight('w',(True,2)).record(2)),('Weight negative dimension',lambda:Weight('w',(-2,3)).record(2)),('Weight bool element bytes',lambda:Weight('w',(2,3)).record(True)),('linear negative rows',lambda:linear('x',-1,2,3,Scenario()).record()),('Operator NaN work',lambda:Operator('x','custom',{},scalar_flops=float('nan')).record())]:
 try:v=f();out.append({'case':name,'accepted':True,'result_repr':repr(v)})
 except Exception as e:out.append({'case':name,'accepted':False,'error':repr(e)})
try:positive_number('2','x')
except Exception as e:out.append({'case':'positive_number string','error_type':type(e).__name__})
class Response:
 status=200;headers={}
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def read(self,*args):self.read_args=args;return b'abc'
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);row={'model':'demo','file':'s.txt','url':'https://example.invalid/fixed','status':'downloaded','bytes':2,'sha256':hashlib.sha256(b'abc').hexdigest()};response=Response()
 with patch.object(sources,'PROJECT',root),patch.object(sources,'records',return_value=[row]),patch.object(sources,'urlopen',return_value=response):
  r=sources.fetch_sources('demo');out.append({'case':'fetch nonrange bound and wrong locked bytecount','read_args':response.read_args,'accepted_wrong_length':(root/'s.txt').read_bytes()==b'abc'});out.append({'case':'read_source ignores locked bytecount','returned_bytes':len(sources.read_source('s.txt'))})
 (root/'results').mkdir();(root/'results/manifest.json').write_text(json.dumps({'inputs':[],'artifacts':[],'scope':'test'}))
 with patch.object(reproduce,'PROJECT',root),patch.object(reproduce,'verify_sources',return_value={}),patch.object(reproduce,'input_hashes',return_value=[]):out.append({'case':'empty artifact manifest','result':reproduce.verify_results(False)})
(Path(__file__).parent/'counterexamples.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
