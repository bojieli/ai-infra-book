"""Experiment 6-9: capacity placement and a declared snapshot-read service model.

Capacity sizes come from the outline; interface rates and frequencies are explicitly
declared teaching assumptions. No remote
addressing, coherence, bandwidth aggregation or device API is inferred.
"""
from fractions import Fraction
from itertools import product, combinations
import json
from pathlib import Path

GIB = 2**30


def calculate(copies=1):
    if type(copies) is not int or not 1 <= copies <= 3:
        raise ValueError('copies must be 1, 2 or 3, on distinct donor nodes')
    capacity = [64*GIB]*4
    demand = [80*GIB,48*GIB,32*GIB,32*GIB]
    deficit = [max(0,d-c) for d,c in zip(demand,capacity)]
    free = [max(0,c-d) for d,c in zip(demand,capacity)]
    # Entire indivisible jobs may be reassigned, but not split; colocation is allowed subject to capacity.
    assignments = []
    for owners in product(range(4), repeat=4):
        used = [sum(demand[j] for j in range(4) if owners[j]==node) for node in range(4)]
        if all(u<=c for u,c in zip(used,capacity)):
            assignments.append(list(owners))
    borrowed = deficit[0]
    donors = [node for node in range(1,4) if free[node]>=borrowed][:copies]
    placed = [min(d,c) for d,c in zip(demand,capacity)]
    for donor in donors:
        placed[donor] += borrowed
    failures=[]
    for count in range(1,5):
        for failed_tuple in combinations(range(4),count):
            failed=set(failed_tuple)
            # Each job needs its local data/compute node. Borrower additionally
            # requires at least one complete remote snapshot copy.
            unavailable=sorted(failed | ({0} if set(donors)<=failed else set()))
            failures.append(dict(failed_nodes=list(failed_tuple),
                                 unavailable_job_owners=unavailable))
    access=[]
    for bandwidth in (10*10**9,40*10**9):
        for latency_ns in (2000,20000):
            for transactions in (128,4096):
                # One payload-bearing transaction is256 bytes; this window is
                # declared, not deduced from number of replicas or GPU threads.
                effective=min(Fraction(bandwidth),Fraction(transactions*256*10**9,latency_ns))
                for frequency in (Fraction(1,60),Fraction(1),Fraction(20)):
                    read=borrowed
                    service=Fraction(5000,10**9)+max(Fraction(latency_ns,10**9),Fraction(read,effective))
                    period=1/frequency
                    access.append(dict(interface_bandwidth_bytes_per_second=bandwidth,
                        latency_ns=latency_ns,active_transactions=transactions,
                        transaction_bytes=256,startup_ns=5000,
                        reads_per_second_exact=str(frequency),read_payload_bytes=read,
                        offered_payload_bytes_per_second_exact=str(read*frequency),
                        effective_upper_bytes_per_second_exact=str(effective),
                        serialized_read_service_seconds_exact=str(service),
                        period_seconds_exact=str(period),
                        load_exact=str(service*frequency),
                        deterministic_serial_queue_bounded=service<=period,
                        spare_time_per_period_seconds_exact=str(period-service),
                        max_read_frequency_exact=str(1/service),
                        measured_decode_seconds=None))
    return dict(calculation='memory-pool-access-candidate',scenario=dict(copies=copies),
        capacity=dict(node_capacity_bytes=capacity,job_demand_bytes=demand,
            total_capacity_bytes=sum(capacity),total_demand_bytes=sum(demand),
            local_deficit_bytes=deficit,unusable_local_slack_before_pool_bytes=sum(free),
            added_local_capacity_bytes=sum(deficit),
            whole_job_migration_feasible_assignments=assignments,
            whole_job_migration_infeasibility='80GiB job exceeds every64GiB node',
            splittable_compute_migration_bytes=borrowed,
            splittable_compute_migration_feasible_if_supported=True,
            splittable_compute_migration_runtime_cost=None,
            borrowed_unique_bytes=borrowed,donor_nodes=donors,
            physical_used_after_pool_bytes=placed,
            physical_free_after_pool_bytes=[c-u for c,u in zip(capacity,placed)],
            extra_replica_storage_bytes=(copies-1)*borrowed,
            total_physical_used_bytes=sum(placed)),
        failure_sets=failures,access_scenarios=access,
        assumptions=[
            '四个64GiB、80/48/32/32GiB工作集来自实验6-9教学例，不对应任何硬件远程访问能力。副本在不同节点、读请求只选一个活副本；副本数不会自动倍增带宽。',
            '完整80GiB任务迁到另一台64GiB仍放不下。若允许拆分计算/数据并迁走16GiB，则容量可行，但拆分、依赖和执行收益必须另算。',
            '只借容量时借用者保留计算任务、本地64GiB，远端16GiB在所列供体持有。借用不制造额外唯一数据；额外完整副本另计容量，初始填充/复制流量与创建时间未计。',
            '访问场景反复读取同一16GiB快照，冷/热体现为1/60、1、20次每秒。动态KV追加、版本同步、写入和计算不在本快照账；不能称完整decode时间。',
            '接口/窗口参数与频率均是新增教学假设，不是原文给出的测量。以min(B,Nq/L)上界计算乐观服务，再显式假定它就是本串行模型的固定服务时长startup+max(L,payload/rate)。严格周期到达下service<=period才不增长积压，等号无余量；这只是声明模型的条件，不保证真实系统稳定，突发/随机到达/其他竞争另算。',
            '故障表是指定节点集合永久不可用时的静态依赖可用性，无概率、检测/恢复时长或可靠性排名。失去本地计算节点的任务不可用，即使某个远端副本仍在。'])


if __name__=='__main__':
    result={f'copies{n}':calculate(n) for n in (1,2,3)}
    Path(__file__).with_name('result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
