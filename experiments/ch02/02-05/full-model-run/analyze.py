"""Offline stdlib analysis of a completed actual run; raw files are never overwritten."""
import argparse
import hashlib
import importlib.util
import json
import math
import shutil
import statistics
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text())

def require(value, message):
    if not value:
        raise ValueError(message)

def finite(value):
    return type(value) in (int, float) and math.isfinite(value)

def analyze(out, destination=None):
    out = out.resolve()
    destination = destination or out / 'offline-analysis'
    require(not destination.exists(), 'Destination exists; choose a fresh --destination')
    supervisor = read(out / 'supervisor.json')
    require(supervisor.get('exit_code') == 0 and supervisor.get('reason') is None and supervisor.get('leftovers') == [], 'Partial/failed run: clean supervisor exit required')
    completion = read(out / 'completion.json')
    require(completion.get('status') == 'all_frozen_requests_returned' and completion.get('count') == 8, 'Eight completed requests required')
    require(not (out / 'failure.json').exists(), 'failure.json present: refusing completed-run report')
    ready = read(out / 'ready.json')
    require(ready.get('scope') == 'actual_43_layer_engine_constructor_returned', 'Actual full-engine ready evidence required')
    require(finite(ready.get('initialization_s')) and ready['initialization_s'] > 0, 'Invalid initialization time')
    candidate = read(out / 'candidate.json')
    server = ready['server_info']
    require('json_model_override_args' not in candidate and server.get('json_model_override_args') in (None, '{}', {}), 'Model overrides forbidden')
    require(server.get('model_path') == candidate['model_path'], 'Ready/candidate model mismatch')
    prep = out / 'preparation-evidence'
    metadata = read(prep / 'model-metadata.json')
    config = read(prep / 'metadata/config.json')
    index = read(prep / 'metadata/model.safetensors.index.json')
    shards = metadata['shards']
    require(metadata['layers'] == config['num_hidden_layers'] == 43, 'Expected original 43 layers')
    require(len(shards) == 48 and {s['name'] for s in shards} == set(index['weight_map'].values()), 'Expected all 48 indexed shards')
    require(metadata['model_path'] == candidate['model_path'], 'Preparation/candidate model mismatch')
    hashes = read(out / 'small-model-hashes.json')
    require(digest(prep / 'metadata/config.json') == hashes['config.json'], 'Prepared model config hash mismatch')
    require(digest(out / 'cases.json') == digest(prep / 'cases.json'), 'Frozen cases changed')
    package = read(out / 'execution-package-hashes.json')
    for name, expected in package.items():
        require(Path(name).name == name and digest(out / name) == expected, 'Execution package mismatch: ' + name)
    rows = read(out / 'requests.json')
    require(len(rows) == 8, 'Expected eight request records')
    # Execute the current scorer only on temporary COPIES, leaving all raw JSON intact.
    spec = importlib.util.spec_from_file_location('current_full_v4_score', BASE / 'score.py')
    scorer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scorer)
    with tempfile.TemporaryDirectory(prefix='v4-offline-score-') as temporary:
        work = Path(temporary)
        for name in ('cases.json', 'requests.json', 'run.log'):
            shutil.copyfile(out / name, work / name)
        scorer.score(work)
        scores = read(work / 'scores.json')
        pools = read(work / 'pool-log-evidence.json')
    require(scores['record_set_valid'] and scores['returned_count'] == 8 and scores['schema_valid_count'] == 8, 'Incomplete input/response schema')
    require(all(c['input_matches_frozen'] and c['sampling_matches_frozen'] for c in scores['cases']), 'Frozen input/sampling mismatch')
    for row in rows:
        require(finite(row.get('request_wall_s')) and row['request_wall_s'] > 0, 'Invalid request wall time')
        require(finite(row.get('sent_monotonic')), 'Missing request monotonic timestamp')
        meta = row['response']['meta_info']
        if 'prompt_tokens' in meta:
            require(type(meta['prompt_tokens']) is int and meta['prompt_tokens'] == len(row['input_ids']), 'Engine prompt token count mismatch')
    require(pools['observed'] and any('DSV4 pool sizes:' in line for line in pools['lines']), 'Actual DSV4 pool log evidence missing')
    samples = [json.loads(line) for line in (out / 'watchdog.jsonl').read_text().splitlines() if line.strip()]
    require(len(samples) >= 2, 'At least two watchdog samples required')
    fields = ('elapsed_s', 'own_rss_bytes', 'own_anon_bytes', 'own_gpu_mib', 'available_bytes', 'gpu_free_mib')
    for sample in samples:
        require(all(finite(sample.get(k)) and sample[k] >= 0 for k in fields), 'Malformed watchdog sample')
    gaps = [b['elapsed_s'] - a['elapsed_s'] for a, b in zip(samples, samples[1:])]
    require(all(gap > 0 for gap in gaps), 'Non-monotonic watchdog samples')
    resources = {k: dict(min=min(s[k] for s in samples), max=max(s[k] for s in samples)) for k in fields[1:]}
    resources.update(sample_count=len(samples), observed_span_s=samples[-1]['elapsed_s'] - samples[0]['elapsed_s'], interval_s=dict(min=min(gaps), median=statistics.median(gaps), max=max(gaps)), scope='Observed samples only, not continuous maxima. RSS is a sum over processes and may double-count shared mappings; GPU allocation is sampled nvidia-smi process accounting; free resources are shared-host values.')
    raw_names = ['supervisor.json', 'completion.json', 'ready.json', 'candidate.json', 'cases.json', 'requests.json', 'watchdog.jsonl', 'run.log', 'execution-package-hashes.json', 'small-model-hashes.json']
    for name in ('scores.json', 'scores-at-exit.json', 'score.py', 'preparation-evidence/model-metadata.json', 'preparation-evidence/metadata/config.json', 'preparation-evidence/metadata/model.safetensors.index.json'):
        if (out / name).is_file():
            raw_names.append(name)
    provenance = dict(analyzer_sha256=digest(BASE / 'analyze.py'), current_scorer_sha256=digest(BASE / 'score.py'), execution_scorer_sha256=digest(out / 'score.py'), scorer_changed_since_execution=digest(BASE / 'score.py') != digest(out / 'score.py'), source_sha256={name: digest(out / name) for name in raw_names}, original_scores_overwritten=False)
    report = dict(status='completed_actual_execution', quality_scope=scores['scope'], quality_strict_success=scores['strict_success'], denominator=8, initialization_s=ready['initialization_s'], request_wall_sum_s=sum(r['request_wall_s'] for r in rows), request_wall_scope=scores['request_wall_scope'], model_evidence=dict(layers=43, indexed_shards=48, shard_bytes=sum(s['bytes'] for s in shards), revision=metadata['revision'], scope='Prepared original config and shard stat/index evidence plus actual full-engine ready; not full payload SHA verification or layer-by-layer execution tracing.'), resources=resources, strict_numerical_clearance=False, numerical_limit='Existing M8 strict FP64 gate failure remains unresolved; retrieval does not clear it.', provenance=provenance)
    # Write derived artifacts only after every validation passed.
    destination.mkdir(parents=True, exist_ok=False)
    for name, value in [('analysis.json', report), ('scores-recomputed.json', scores), ('pool-log-evidence.json', pools)]:
        (destination / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    (destination / 'REPORT.md').write_text(f"Actual full-model run completed: {scores['strict_success']}/8 strict retrieval successes.\n\nInitialization: {ready['initialization_s']:.6f} s; sum of application request envelopes: {report['request_wall_sum_s']:.6f} s.\n\n{scores['request_wall_scope']}\n\n{resources['scope']}\n\n43 original layers and 48 indexed shards: preparation metadata plus actual Engine readiness; no full-payload integrity or per-layer execution claim.\n\n{report['numerical_limit']}\n\nOriginal raw files and exit-time scores were not overwritten. Current and execution scorer hashes are recorded in analysis.json.\n")
    return destination

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--destination', type=Path)
    args = parser.parse_args()
    print(analyze(args.out, args.destination))
