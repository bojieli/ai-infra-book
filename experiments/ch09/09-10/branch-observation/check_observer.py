"""CPU-only instrumentation test using AST-extracted, unmodified installed methods."""
import ast,json,os,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent

def exercise():
    from observer import install
    install()
    m=json.loads((R/'source-manifest.json').read_text());base=Path(m['installed_root'])
    namespace={}
    for rel,names in [('managers/cache_controller.py',['prefetch_rate_limited']),('mem_cache/hiradix_cache.py',['check_prefetch_progress'])]:
        tree=ast.parse((base/rel).read_text())
        for n in ast.walk(tree):
            if isinstance(n,ast.FunctionDef) and n.name in names:
                exec(compile(ast.Module(body=[n],type_ignores=[]),str(base/rel),'exec'),namespace)
    class Dummy:pass
    cc=Dummy();cc.prefetch_tokens_occupied=4096;cc.prefetch_capacity_limit=3276
    assert namespace['prefetch_rate_limited'](cc) is True
    cc.prefetch_tokens_occupied=3072
    assert namespace['prefetch_rate_limited'](cc) is False
    tc=Dummy();tc.ongoing_prefetch={};tc.prefetch_loaded_tokens_by_reqid={};tc.cache_controller=cc
    assert namespace['check_prefetch_progress'](tc,'cpu-absent') is True
    op=Dummy();op.host_indices=[1];op.request_id='cpu-wait';op.completed_tokens=0;op.hash_value=[]
    tc.ongoing_prefetch={'cpu-wait':(None,None,None,op)};tc.can_terminate_prefetch=lambda op:False
    assert namespace['check_prefetch_progress'](tc,'cpu-wait') is False
    op.host_indices=None
    assert namespace['check_prefetch_progress'](tc,'cpu-wait') is True

if __name__=='__main__':
    if '--child' in sys.argv:exercise()
    else:
        out=R/'cpu-check';out.mkdir(exist_ok=False)
        p=subprocess.run([sys.executable,__file__,'--child'],env=dict(os.environ,BOOK_BRANCH_TRACE=str(out/'events'),PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True)
        (out/'stdout.txt').write_text(p.stdout);(out/'stderr.txt').write_text(p.stderr)
        rows=[json.loads(line) for f in out.glob('events.*.jsonl') for line in f.read_text().splitlines()]
        returns=[r for r in rows if r.get('phase')=='return']
        assert p.returncode==0,p.stderr
        assert [r['return'] for r in returns]==[True,False,True,False,True],returns
        (out/'result.json').write_text(json.dumps(dict(exit_code=p.returncode,events=len(rows),returns=[{'method':r['method'],'line':r['line'],'request_id':r['request_id'],'return':r['return']} for r in returns],scope='CPU-only observer check; not experimental branch evidence'),indent=2)+'\n')
        print((out/'result.json').read_text())
