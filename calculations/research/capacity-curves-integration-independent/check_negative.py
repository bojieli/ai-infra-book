"""Isolated exact-module verifier checks, never mutate shared results/figures."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
HERE=Path(__file__).resolve().parent;P=HERE.parents[1];C=HERE.parent/'capacity-curves'
sys.path.insert(0,str(P/'src'))
checks=[]
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);module=root/'src/infra_calc/capacity_plot.py';module.parent.mkdir(parents=True)
    shutil.copyfile(P/'src/infra_calc/capacity_plot.py',module)
    spec=importlib.util.spec_from_file_location('isolated_plot',module);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.PROJECT=root;m.DIRECTORY=root/'figures/capacity-curves';m.DIRECTORY.mkdir(parents=True)
    inputs=json.loads((C/'figures/data.json').read_text())['inputs']
    for row in inputs:
        dest=root/row['file'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(P/row['file'],dest)
    for name in ('figure.png','figure.svg','figure.pdf','data.json'):shutil.copyfile(P/'figures/capacity-curves'/name,m.DIRECTORY/name)
    def row(path):return {'file':str(path.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    good={'inputs':[row(root/x['file']) for x in inputs]+[row(module)],'artifacts':[row(m.DIRECTORY/n) for n in ('figure.png','figure.svg','figure.pdf','data.json')]}
    assert good == {k:json.loads((P/'figures/capacity-curves/manifest.json').read_text())[k] for k in ('inputs','artifacts')}
    path=m.DIRECTORY/'manifest.json'
    def write(x):path.write_text(json.dumps(x))
    write(good);assert m.verify()=={'verified_figures':3}
    checks.append('valid isolated manifest accepted')
    for key in ('inputs','artifacts'):
        for kind in ('empty','missing','duplicate','unexpected','wrong_type'):
            bad=copy.deepcopy(good)
            if kind=='empty':bad[key]=[]
            elif kind=='missing':bad[key].pop()
            elif kind=='duplicate':bad[key][-1]=bad[key][0]
            elif kind=='unexpected':bad[key][-1]['file']='unexpected.bin'
            else:bad[key]={}
            write(bad)
            try:m.verify()
            except ValueError:checks.append(key+':'+kind+':rejected')
            else:raise AssertionError((key,kind))
    write(good)
    for key in ('inputs','artifacts'):
        target=root/good[key][0]['file'];raw=target.read_bytes()
        target.write_bytes(bytes([raw[0]^1])+raw[1:])
        try:m.verify()
        except ValueError:checks.append(key+':same_length_tamper:rejected')
        else:raise AssertionError(key)
        target.write_bytes(raw)
        target.unlink()
        try:m.verify()
        except FileNotFoundError:checks.append(key+':file_missing:rejected')
        else:raise AssertionError(key)
        target.write_bytes(raw)
    assert m.verify()=={'verified_figures':3}
(HERE/'negative-results.json').write_text(json.dumps({'checks':checks,'count':len(checks),'public_module_sha':hashlib.sha256((P/'src/infra_calc/capacity_plot.py').read_bytes()).hexdigest(),'fixture':'exact public module, real rendered artifacts and inputs; isolated manifest entries proven equal to actual public manifest'},indent=2)+'\n')
print(len(checks),'checks passed')
