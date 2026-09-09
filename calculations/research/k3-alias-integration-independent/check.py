"""Finite documentation integration check; no public writes or GPU execution."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import warnings
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
sys.path.insert(0, str(PROJECT / 'src'))
from infra_calc.topics import k3_kda, k3_forward, kda_chunk


def digest(data):
    return hashlib.sha256(data).hexdigest()


def differences(a, b, path=''):
    if type(a) is not type(b):
        return [path]
    if isinstance(a, dict):
        assert a.keys() == b.keys()
        return sum((differences(a[k], b[k], path + '/' + k) for k in a), [])
    if isinstance(a, (list, tuple)):
        assert len(a) == len(b)
        return sum((differences(x, y, path + '/' + str(i)) for i, (x, y) in enumerate(zip(a, b))), [])
    return [] if a == b else [path]


def main():
    proposal = json.loads((PROJECT / 'research/k3-alog-reconciliation/recommendations.json').read_text())
    assert proposal['shape_repair'] is None
    p = proposal['proposals'][0]
    new = (PROJECT / p['file']).read_bytes()
    assert new.count(p['proposed'].encode()) == 1 and p['old'].encode() not in new
    old = new.replace(p['proposed'].encode(), p['old'].encode())
    expected = json.loads((PROJECT / 'research/k3-alias-integration/before-bindings.json').read_text())[0]['sha256']
    assert digest(old) == expected
    (HERE / 'original.snapshot.py').write_bytes(old)
    (HERE / 'public.snapshot.py').write_bytes(new)
    spec = importlib.util.spec_from_file_location('infra_calc.topics._k3_old_independent', HERE / 'original.snapshot.py')
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    sources = json.loads((PROJECT / 'research/k3-alog-reconciliation/source-bindings.json').read_text())['public_sources']
    wrapper_results = []
    for name in ('chunk.py', 'fused_recurrent.py'):
        source = next(x for x in sources if x['file'].endswith('/kda/' + name))
        data = (PROJECT / source['file']).read_bytes()
        assert digest(data) == source['sha256']
        tree = ast.parse(data)
        blocks = [n for n in ast.walk(tree) if isinstance(n, ast.If) and ast.unparse(n.test) == "'transpose_state_layout' in kwargs"]
        assert len(blocks) == 1
        code = compile(ast.Module(body=blocks, type_ignores=[]), source['file'], 'exec')
        cases = []
        for alias in (False, True):
            for current in (False, True):
                env = {'kwargs': {'transpose_state_layout': alias}, 'state_v_first': current, 'warnings': warnings}
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always')
                    try:
                        exec(code, env)
                    except ValueError:
                        assert current is True
                        status = 'reject truthy new flag plus deprecated flag'
                    else:
                        assert current is False and env['state_v_first'] is alias and env['kwargs'] == {}
                        assert len(caught) == 1 and caught[0].category is DeprecationWarning
                        status = 'alias assigned and popped'
                cases.append(dict(alias=alias, current=current, status=status))
        env = {'kwargs': {}, 'state_v_first': True, 'warnings': warnings}
        exec(code, env)
        assert env['state_v_first'] is True
        wrapper_results.append(dict(source=source, line=blocks[0].lineno, cases=cases, absent_alias_preserved=True))
    book = json.loads((PROJECT / 'scenarios/book.json').read_text())
    scenes = []
    for group, module in [('k3_kda', k3_kda), ('k3_forward', k3_forward), ('kda_chunk', kda_chunk)]:
        for scene in book[group]:
            args = {k: v for k, v in scene.items() if k != 'id'}
            after = module.calculate(**args)
            with patch.object(k3_kda, 'calculate', previous.calculate):
                before = module.calculate(**args)
            changed = differences(before, after)
            # Replacement must occur only as the specific assumption leaf.
            normalized = json.loads(json.dumps(after).replace(p['proposed'], p['old']))
            assert normalized == json.loads(json.dumps(before))
            assert all('/assumptions/' in x for x in changed)
            assert changed == ['/assumptions/2'] if group == 'k3_kda' else True
            scenes.append(dict(id=scene['id'], group=group, changed_paths=changed))
    archive = PROJECT / 'research/k3-alog-reconciliation'
    bindings = json.loads((archive / 'bindings.json').read_text())
    rec_bytes = (archive / 'reconciliation.json').read_bytes()
    assert digest(rec_bytes) == next(x['sha256'] for x in bindings if x['file'] == 'reconciliation.json')
    rec = json.loads(rec_bytes)
    mismatch = rec['public_checkpoint']['config_shape_mismatches']
    assert len(mismatch) == 69
    assert all(x['config_shape'] == [96] and x['checkpoint_shape'] == [128] for x in mismatch)
    assert rec['checkpoint_extra_parameters'] == 2208 and rec['checkpoint_extra_fp32_bytes'] == 8832
    report = dict(status='pass', python=sys.version, old_sha256=digest(old), public_sha256=digest(new), reverse_bytes_match=True, wrappers=wrapper_results, scenarios=scenes, preserved_shape_conflict=dict(layers=69, config_shape=[96], checkpoint_shape=[128], extra_parameters=2208, extra_fp32_bytes=8832, archive_sha256=digest(rec_bytes)), scope='AST alias block only, not CUDA/Triton execution or checkpoint compatibility')
    (HERE / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(status='pass', scenarios=len(scenes), wrapper_boolean_cases=8, shape_mismatches=69)))


if __name__ == '__main__':
    main()
