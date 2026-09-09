from pathlib import Path
import ast,json,hashlib
P=Path(__file__).parent; source=json.loads((P/'source.json').read_text());b=(P/'mma.py').read_bytes();assert hashlib.sha256(b).hexdigest()==source['sha256'] and len(b)==source['bytes']; tree=ast.parse(b); rows=[]
for name in ('MmaF16BF16Op','MmaF16BF16SparseOp'):
 n=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==name);doc=ast.get_docstring(n);assert '| BF16        | BF16        | F32      |' in doc;assert '| F16         | F16         | F16, F32 |' in doc;assert 'sm_100a' in doc and 'sm_103a' in doc;rows.append({'class':name,'line':n.lineno,'bf16_accumulator':['F32'],'f16_accumulator':['F16','F32'],'supported_architecture_family':['sm100','sm103','sm110']})
result={'source':source,'checks':rows,'interpretation':'Official explicit supported combination tables; not inferred from independent descriptor bit fields, nor claimed GPU execution test','all_passed':True};(P/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('Two dense/sparse explicit BF16/F32 tables verified; pinned SHA verified')
