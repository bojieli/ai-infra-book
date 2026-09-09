"""Run from this directory; imports original modules read-only without bytecode writes."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import json
import hashlib
from datetime import datetime, timezone
ROOT = Path('/Users/boj/book/ai-infra-book/calculations')
sys.path.insert(0, str(ROOT / 'src'))
from infra_calc.sources import records, read_source
from reconfiguration import calculate


def main():
    here = Path(__file__).resolve().parent
    output = here / 'results'
    evidence = here / 'evidence'
    output.mkdir(exist_ok=True)
    evidence.mkdir(exist_ok=True)
    scenarios = json.loads((here/'scenarios.json').read_text())
    models = {s['model'] for s in scenarios}
    manifest = []
    for record in records():
        if record['file'] in {f'configs/models/{m}/config.json' for m in models}:
            data = read_source(record['file'])
            dest = evidence / (record['model'] + '-config.json')
            dest.write_bytes(data)
            manifest.append({**record, 'local_file': str(dest.relative_to(here)),
                             'copied_at': datetime.now(timezone.utc).isoformat(),
                             'acquisition': 'Existing pinned official repository evidence; no network fetch'})
    (evidence/'sources.json').write_text(json.dumps(manifest, indent=2)+'\n')
    dependencies = ['src/infra_calc/topics/dense_placement.py', 'src/infra_calc/topics/weight_handoff.py',
                    'src/infra_calc/topics/checkpoint_reshard.py', 'src/infra_calc/models/qwen3.py',
                    'src/infra_calc/models/qwen3_moe.py', 'src/infra_calc/schema.py', 'src/infra_calc/sources.py']
    (evidence/'dependency_hashes.json').write_text(json.dumps([
        dict(file=str(ROOT/p), sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
        for p in dependencies],indent=2)+'\n')
    summary = []
    for scenario in scenarios:
        result = calculate(scenario)
        (output/(scenario['id']+'.json')).write_text(json.dumps(result,indent=2)+'\n')
        summary.append(dict(id=scenario['id'], migration_totals=result['migration_totals'],
                            summary=result['summary'], amortization=result['amortization'],
                            deployment_cost=result['deployment_cost']))
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(f'Generated {len(scenarios)} analytical scenarios; copied {len(manifest)} verified official configurations.')

if __name__ == '__main__':
    main()
