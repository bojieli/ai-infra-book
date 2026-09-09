"""Isolated complete-set and checksum rejection tests for figure verification."""
from pathlib import Path
import tempfile,sys,shutil,json,hashlib,copy
P=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(P/'src'))
from infra_calc import chat_agent_plot as m
checks=[]
original=m.DIRECTORY
with tempfile.TemporaryDirectory(dir=P/'research') as tmp:
    m.DIRECTORY=Path(tmp)
    def entry(path):return dict(file=str(path.relative_to(P)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    names=('figure.png','figure.svg','figure.pdf','data.json')
    for name in names:shutil.copyfile(P/'research/chat-agent-figure/figure'/name,m.DIRECTORY/name)
    valid=dict(inputs=[entry(P/name) for name in sorted(m.expected_inputs())],artifacts=[entry(m.DIRECTORY/name) for name in names])
    manifest=m.DIRECTORY/'manifest.json'
    manifest.write_text(json.dumps(valid));assert m.verify()=={'verified_figures':3};checks.append('valid')
    for key in ('inputs','artifacts'):
        for mode in ('empty','missing','duplicate','wrong-path','wrong-hash','not-list'):
            bad=copy.deepcopy(valid)
            if mode=='empty':bad[key]=[]
            elif mode=='missing':bad[key].pop()
            elif mode=='duplicate':bad[key].append(bad[key][0])
            elif mode=='wrong-path':bad[key][0]['file']='unknown'
            elif mode=='wrong-hash':bad[key][0]['sha256']='0'*64
            else:bad[key]={}
            manifest.write_text(json.dumps(bad))
            try:m.verify()
            except ValueError:checks.append(key+':'+mode)
            else:raise AssertionError(key+mode)
    manifest.write_text(json.dumps(valid))
    image=m.DIRECTORY/'figure.png';image.write_bytes(image.read_bytes()+b' ')
    try:m.verify()
    except ValueError:checks.append('altered image')
    else:raise AssertionError('altered image accepted')
    m.DIRECTORY=original
(Path(__file__).parent/'manifest-checks.json').write_text(json.dumps(dict(checks=len(checks),names=checks),indent=2)+'\n')
print(len(checks),'isolated manifest checks passed')
