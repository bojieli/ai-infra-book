"""Only the original six cases; observations, never suggested implementations."""
import ast, copy, json, runpy
from pathlib import Path
# Read the literal cases from the frozen visible checker without executing it twice.
tree=ast.parse(Path('test_intervals.py').read_text())
cases=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='cases' for t in n.targets))
f=runpy.run_path('intervals.py')['merge_intervals'];rows=[]
for original,expected in cases:
 data=copy.deepcopy(original);before=copy.deepcopy(data)
 try:
  actual=f(data);after=copy.deepcopy(data);value=copy.deepcopy(actual)
  passed=value==expected and after==before
  aliases=[{'output_index':i,'input_index':j} for i,x in enumerate(actual) for j,y in enumerate(data) if x is y]
  row=dict(input_before=before,expected=expected,actual=value,input_after=after,unchanged=after==before,passed=passed,output_is_input=actual is data,nested_aliases=aliases)
 except Exception as e:row=dict(input_before=before,expected=expected,input_after=copy.deepcopy(data),passed=False,error=repr(e))
 if not row['passed']:rows.append(row)
print(json.dumps(rows))
