"""Independent identity-placement and exact D/D/1 audit of experiment 6-9.

Only imports candidate output; no writes to calculate.py. One identity below
represents one GiB of one job's distinct data; copies repeat identities.
"""
from collections import Counter
from fractions import Fraction as F
from itertools import product, combinations
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('pool_candidate', HERE/'calculate.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
GiB = 1073741824
sizes = (80, 48, 32, 32)
identities = {owner: {(owner, unit) for unit in range(size)} for owner, size in enumerate(sizes)}
unique_expected = set().union(*identities.values())
assert len(unique_expected) == 192
rows = []
previous_access = None
for copies in (1, 2, 3):
    result = module.calculate(copies)
    cap = result['capacity']
    donors = list(range(1, copies+1))
    remote = {(0, unit) for unit in range(64, 80)}
    placement = [identities[0] - remote, *[set(identities[i]) for i in range(1,4)]]
    for donor in donors:
        placement[donor] |= remote
    assert all(len(items) <= 64 for items in placement)
    actual_multiplicity = Counter(identity for items in placement for identity in items)
    assert set(actual_multiplicity) == unique_expected
    assert all(count == (copies if identity in remote else 1) for identity, count in actual_multiplicity.items())
    assert cap['donor_nodes'] == donors
    assert cap['physical_used_after_pool_bytes'] == [len(items)*GiB for items in placement]
    assert cap['physical_free_after_pool_bytes'] == [(64-len(items))*GiB for items in placement]
    assert cap['total_physical_used_bytes'] == (192+16*(copies-1))*GiB
    assert cap['extra_replica_storage_bytes'] == 16*(copies-1)*GiB
    assert cap['borrowed_unique_bytes'] == 16*GiB
    assert cap['local_deficit_bytes'] == [16*GiB, 0, 0, 0]
    assert cap['unusable_local_slack_before_pool_bytes'] == 80*GiB
    assert cap['total_capacity_bytes'] == 256*GiB
    assert cap['total_demand_bytes'] == 192*GiB
    assert cap['added_local_capacity_bytes'] == 16*GiB
    # Exhaust all4^4 whole-job placements independent of candidate's list.
    feasible = []
    for assignment in product(range(4), repeat=4):
        if all(sum(sizes[job] for job in range(4) if assignment[job] == node) <= 64 for node in range(4)):
            feasible.append(list(assignment))
    assert feasible == cap['whole_job_migration_feasible_assignments'] == []
    # Feasible split witness: move exactly owner0 identities64..79 and their
    # associated partition of computation to node1. This asserts capacity only.
    split = [identities[0] - remote, identities[1] | remote, identities[2], identities[3]]
    assert [len(x) for x in split] == [64,64,32,32]
    assert cap['splittable_compute_migration_bytes'] == len(remote)*GiB
    assert cap['splittable_compute_migration_feasible_if_supported'] is True
    assert cap['splittable_compute_migration_runtime_cost'] is None
    expected_failures = set()
    for count in range(1,5):
        expected_failures.update(combinations(range(4),count))
    assert {tuple(x['failed_nodes']) for x in result['failure_sets']} == expected_failures
    for failure in result['failure_sets']:
        failed = set(failure['failed_nodes'])
        surviving_data = set().union(*(placement[n] for n in range(4) if n not in failed))
        unavailable = [owner for owner in range(4) if owner in failed or not identities[owner] <= surviving_data]
        assert failure['unavailable_job_owners'] == unavailable
    scenarios = result['access_scenarios']
    assert len(scenarios) == 24
    keys = {(r['interface_bandwidth_bytes_per_second'], r['latency_ns'], r['active_transactions'], F(r['reads_per_second_exact'])) for r in scenarios}
    assert keys == set(product((10_000_000_000,40_000_000_000),(2000,20000),(128,4096),(F(1,60),F(1),F(20))))
    if previous_access is not None:
        assert scenarios == previous_access, 'Replicas must not multiply per-read bandwidth'
    previous_access = scenarios
    arrivals = []
    for index,r in enumerate(scenarios):
        bandwidth = r['interface_bandwidth_bytes_per_second']
        latency = F(r['latency_ns'],1_000_000_000)
        window_bytes = r['active_transactions'] * 256
        # Derive service from the slower full-payload bottleneck directly,
        # independent of candidate's effective rate substitution.
        link_seconds = F(16*GiB,bandwidth)
        window_seconds = F(16*GiB,window_bytes)*latency
        service = F(5,1_000_000) + max(latency,link_seconds,window_seconds)
        frequency = F(r['reads_per_second_exact']); period = 1/frequency
        assert F(r['serialized_read_service_seconds_exact']) == service
        assert F(r['effective_upper_bytes_per_second_exact']) == F(16*GiB,max(link_seconds,window_seconds))
        assert F(r['period_seconds_exact']) == period
        assert F(r['load_exact']) == service/period
        assert F(r['offered_payload_bytes_per_second_exact']) == 16*GiB*frequency
        assert F(r['spare_time_per_period_seconds_exact']) == period-service
        assert F(r['max_read_frequency_exact']) == 1/service
        assert r['deterministic_serial_queue_bounded'] == (service <= period)
        assert r['read_payload_bytes'] == 16*GiB
        assert r['measured_decode_seconds'] is None
        previous_finish = F(0)
        timeline = []
        for n in range(8):
            arrival = n*period
            start = max(arrival,previous_finish)
            finish = start+service
            wait = start-arrival
            assert wait == n*max(F(0),service-period)
            timeline.append(dict(arrival=str(arrival),start=str(start),finish=str(finish),wait=str(wait)))
            previous_finish = finish
        arrivals.append(dict(index=index,load=str(service/period),bounded=service<=period,first_eight=timeline))
    assert sum(r['deterministic_serial_queue_bounded'] for r in scenarios) == 10
    rows.append(dict(copies=copies,
        identity_placement=[dict(node=n,identities=[list(i) for i in sorted(items)]) for n,items in enumerate(placement)],
        total_unique_identities=len(unique_expected),physical_gib=sum(len(x) for x in placement),
        failure_sets_checked=15,access_cases_checked=24,arrival_traces=arrivals))
for invalid in (0,4,-1,True,1.0,'2',None):
    try:
        module.calculate(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError(('Invalid copies accepted',invalid))
# Equal service/period yields no queue growth but zero headroom, conditional
# on exact periodic arrival and exact service. The24 grid cases do not hit it.
period=F(3,7); finish=F(0)
for n in range(8):
    arrival=n*period; start=max(arrival,finish); assert start==arrival; finish=start+period
artifact=dict(status='passed',replica_counts_checked=3,access_cases_checked=72,
    failure_sets_checked=45,arrivals_per_case=8,invalid_inputs_checked=7,results=rows,
    scope='Identity placement and exact declared deterministic service only; no real runtime, remote access, or queue guarantee.')
(HERE/'check-result.json').write_text(json.dumps(artifact,indent=2)+'\n')
print('PASS: 3 identity placements; 45 failure sets; 72 exact access scenarios; 576 arrivals; 7 invalid inputs; equality boundary.')
