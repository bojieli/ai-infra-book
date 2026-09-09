import pathlib,hashlib,json
root=pathlib.Path(__file__).resolve().parents[1];files=[]
for p in sorted(root.rglob('*')):
 if p.is_file() and p.name!='manifest.json' and '.analysis-venv' not in p.parts:
  files.append(dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(root/'manifest.json').write_text(json.dumps(files,indent=2))
print('Sealed',len(files),'files,',sum(x['bytes'] for x in files),'bytes (private analysis venv excluded)')
