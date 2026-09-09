"""C62: declared clone/startup budgets alongside separate archived local trials."""
from fractions import Fraction
import hashlib
import json
from ..paths import PROJECT
from .environment_resources import sampled_rss

GIB=1024**3
MIB=1024**2


def fraction(value):
    if isinstance(value,bool) or not isinstance(value,(int,str)):
        raise ValueError('Use exact integer or fraction string inputs')
    result=Fraction(value)
    if result<0: raise ValueError('Inputs must be nonnegative')
    return result


def recorded_prewarm():
    records=json.loads((PROJECT/'configs/environment-lifecycle.lock.json').read_text())
    files={}
    for row in records:
        data=(PROJECT/row['file']).read_bytes()
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise ValueError('Lifecycle record checksum mismatch')
        files[row['file'].split('environment-lifecycle/',1)[1]]=data
    original=json.loads(files['11-06/manifest.json'])['files']
    for name,data in files.items():
        if name.startswith('11-06/') and name!='11-06/manifest.json':
            entry=original[name.removeprefix('11-06/')]
            if entry['sha256']!=hashlib.sha256(data).hexdigest() or entry['bytes']!=len(data):
                raise ValueError('Original prewarm manifest mismatch')
    env=json.loads(files['11-06/results/environment.json'])
    for name in ('run.py','worker.py','tools.py'):
        if hashlib.sha256(files['11-06/'+name]).hexdigest()!=env['source_hashes'][name]:
            raise ValueError('Measured prewarm source identity differs')
    if json.loads(files['11-06/results/completion.json']) != dict(completed_cases=12,completed=True):
        raise ValueError('Archived prewarm suite did not complete')
    fixture=json.loads(files['11-06/fixture.json'])['rounds']; rows=[]
    for trial,policy in env['plan']:
        raw=json.loads(files[f'11-06/results/{trial}-{policy}/raw.json'])
        if raw['trial']!=trial or raw['policy']!=policy or len(raw['rows'])!=len(fixture):
            raise ValueError('Measured trial identity differs')
        maps={kind:{r['pid']:r for r in raw['events'] if r['event']==kind} for kind in ('launch','ready','destroy')}
        if not maps['launch'].keys()==maps['ready'].keys()==maps['destroy'].keys():
            raise ValueError('Incomplete observed process lifecycle')
        used=set(); wait=0
        for r,f in zip(raw['rows'],fixture):
            if r['response']['reply']!=f['tool_result'] or r['file_sha256']!=f['file_sha256']:
                raise ValueError('Prewarm policies did not replay the same task')
            if not r['call_ns']<=r['send_ns']<=r['response']['start_ns']<=r['response']['end_ns']<=r['received_ns']:
                raise ValueError('Invalid tool timeline')
            if policy.startswith('predict') and r['prediction_hit']!=(r['predicted']==r['kind']):
                raise ValueError('Prediction hit does not match tool identity')
            used.add(r['worker_pid']);wait+=r['received_ns']-r['call_ns']
        if not used.issubset(maps['launch']): raise ValueError('Tool used an unrecorded worker')
        unused=set(maps['launch'])-used; ready_unused=launch_unused=0; startup=[]
        for pid in maps['launch']:
            start,ready,end,reaped=[maps[k][pid][field] for k,field in
                                    [('launch','t_ns'),('ready','t_ns'),('destroy','t_ns'),('destroy','end_ns')]]
            if not start<=ready<=end<=reaped: raise ValueError('Invalid preparation lifetime')
            startup.append(ready-start)
            if pid in unused: ready_unused+=end-ready;launch_unused+=end-start
        points=[(Fraction(s['start_ns']+s['end_ns'],2*10**9),sum(w['rss_bytes'] for w in s['workers'])) for s in raw['samples']]
        rss=sampled_rss(points)
        rows.append(dict(trial=trial,policy=policy,rounds=len(fixture),launches=len(startup),
                         prediction_hits=sum(r['prediction_hit'] is True for r in raw['rows']) if policy.startswith('predict') else None,
                         unused_preparations=len(unused),unused_ready_seconds=float(Fraction(ready_unused,10**9)),
                         unused_allocated_lifecycle_seconds=float(Fraction(launch_unused,10**9)),
                         launch_to_ready_seconds=[float(Fraction(x,10**9)) for x in startup],
                         call_to_tool_reply_seconds=float(Fraction(wait,10**9)),
                         completion_seconds=float(Fraction(raw['work_done_ns']-raw['origin_ns'],10**9)),
                         measured_unused_physical_memory_byte_seconds=None,**rss))
    return rows,json.loads(files['11-02/summary.json']),records


def calculate(environments=100,template_bytes=2*GIB,touched_bytes=512*MIB,dirty_bytes=128*MIB,
              hot_readonly_bytes=256*MIB,private_overhead_bytes=4*MIB,local_budget_bytes=64*GIB,
              snapshot_delta_bytes=128*MIB,effective_transfer_bytes_per_second=GIB,
              preparation_seconds='2',lead_seconds='1',prediction_hit_probability='3/4',
              wrong_prediction_timeout_seconds='3',warm_environment_bytes=2*GIB):
    inputs=locals().copy()
    for name,value in inputs.items():
        if name.endswith('_bytes') or name=='environments' or name=='effective_transfer_bytes_per_second':
            if isinstance(value,bool) or not isinstance(value,int) or value<0: raise ValueError('Byte/count inputs must be nonnegative integers')
    if environments<1 or template_bytes<1 or effective_transfer_bytes_per_second<1:
        raise ValueError('Environment count, template and transfer service must be positive')
    if not 0<=dirty_bytes<=touched_bytes<=template_bytes or hot_readonly_bytes>touched_bytes-dirty_bytes:
        raise ValueError('Dirty and hot read-only ranges must fit the touched template')
    if snapshot_delta_bytes>template_bytes: raise ValueError('Snapshot delta exceeds declared template state')
    prep,lead,hit,timeout=[fraction(inputs[k]) for k in ('preparation_seconds','lead_seconds','prediction_hit_probability','wrong_prediction_timeout_seconds')]
    if hit>1: raise ValueError('Hit probability exceeds one')
    placements=[]
    for name,data in [('full_copy',template_bytes),('install_touched',touched_bytes),
                      ('share_readonly_copy_dirty',dirty_bytes),('localize_hot_readonly',dirty_bytes+hot_readonly_bytes)]:
        private=data+private_overhead_bytes
        placements.append(dict(placement=name,per_environment_local_bytes=private,total_local_bytes=environments*private,
                               separately_retained_shared_template_bytes=template_bytes,
                               total_bytes_across_declared_pools=template_bytes+environments*private,
                               memory_only_environment_upper_bound=local_budget_bytes//private if private else None,
                               initial_local_data_install_bytes=environments*data,
                               aggregate_serial_transfer_lower_exact_seconds=str(Fraction(environments*data,effective_transfer_bytes_per_second))))
    saved=hit*min(prep,lead)
    expected_wait=prep-saved
    allocated=hit*max(prep,lead)+(1-hit)*(lead+timeout+prep)
    wasted=hit*max(lead-prep,0)+(1-hit)*(lead+timeout)
    measured,contracts,sources=recorded_prewarm()
    paths=[]
    # A declared two-hop staging example: source fetch first, private page install
    # second. These bytes are not inferred from the E2B API contract.
    for name,fetch,install in [('cold_template',template_bytes,touched_bytes),
                               ('warm_template',0,touched_bytes),
                               ('pause_resume',touched_bytes,touched_bytes),
                               ('snapshot_clone',touched_bytes,touched_bytes),
                               ('clean_rebuild',template_bytes,template_bytes)]:
        paths.append(dict(path=name,declared_source_fetch_bytes=fetch,declared_local_install_bytes=install,
                          serial_byte_service_lower_exact_seconds=str(Fraction(fetch+install,effective_transfer_bytes_per_second)),
                          create_api_seconds=None,first_tool_complete_seconds=None,reconnect_seconds=None,measured=False))
    return dict(schema_version=1,calculation='environment-lifecycle',model='declared-environment-budget',scenario=inputs,sources=sources,
                clone_placements=placements,measured_prewarm_trials=measured,e2b_documented_contracts=contracts,
                snapshot_budget=dict(shared_base_bytes=template_bytes,branch_delta_bytes=snapshot_delta_bytes,
                                     branches=environments,total_base_plus_private_deltas_bytes=template_bytes+environments*snapshot_delta_bytes,
                                     full_independent_snapshots_bytes=environments*template_bytes,
                                     one_delta_upload_lower_exact_seconds=str(Fraction(snapshot_delta_bytes,effective_transfer_bytes_per_second)),
                                     incremental_format_supported_by_measured_platform=None),
                prewarm_budget=dict(expected_call_preparation_wait_exact_seconds=str(expected_wait),
                                    expected_avoided_wait_exact_seconds=str(saved),
                                    expected_allocated_pretool_environment_seconds=str(allocated),
                                    expected_unused_environment_seconds=str(wasted),
                                    expected_pretool_memory_byte_seconds=str(allocated*warm_environment_bytes),
                                    expected_extra_pretool_memory_byte_seconds_vs_demand=str((allocated-prep)*warm_environment_bytes),
                                    expected_unused_memory_byte_seconds=str(wasted*warm_environment_bytes),
                                    cpu_core_seconds=None),
                creation_paths=paths,
                summary=dict(evidence_scope='Teaching capacity/expectation inputs plus separate archived local process measurements',
                             measured_prewarm_trials=len(measured),e2b_four_path_runtime_measured=False,
                             complete_environment_memory_peak_bytes=None,complete_environment_startup_seconds=None),
                assumptions=['Clone placement inputs reproduce the separate 2 GiB/100 environment teaching case; no E2B/CXLfork benchmark values are inferred.',
                             'Touched includes dirty and disjoint hot read-only bytes. Shared checkpoint remains separate from the local budget. Capacity is memory-only and logical, not sum-of-RSS physical measurement.',
                             'Creation byte paths are a declared serial two-hop staging scenario: cold fetches full template then installs touched pages; warm has source cached but still installs touched; resume/clone fetch and install touched; clean rebuild fetches and installs full template. One shared effective byte service is assumed. Control, init, first-tool execution and reconnect remain unknown, so these are not startup times.',
                             'Base-plus-deltas assumes a declared deduplicated incremental format and independent branch deltas; actual E2B persistence/storage dedup is unknown. Delta upload is byte/service lower bound, not snapshot completion.',
                             'Prewarm begins lead seconds before the call. A correct environment survives until max(call,ready); a wrong one is canceled timeout seconds after call, even if preparation is unfinished. Wrong calls additionally start on-demand preparation.',
                             'Full configured environment bytes are charged from preparation launch to first usability or cancellation. Ready idle plus all unused wrong preparations are separated; CPU work and actual allocated RSS are unknown.',
                             'Expected wait presumes no contention, instantaneous cancellation and the same preparation duration for demanded/predicted environments; correctness hit is not an observed ready-at-call rate.',
                             'Measured prewarm records are local process fixture replays with actual gap waits, not E2B microVM, live prediction-model quality or cold/resume benchmarks. They are never used to calibrate teaching preparation_seconds.',
                             'RSS is trapezoidal interpolation of aggregate observed worker samples only, with no tails. Shared pages may be counted more than once; unused lifecycle time is not measured unused physical GiB-seconds.',
                             'Official E2B documentation contracts are retained with measured timing null: file/process state, instance identity and reconnection are distinct; snapshots do not undo external effects.'])
