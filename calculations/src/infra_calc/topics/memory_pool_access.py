"""Experiment 6-9: capacity placement and a declared snapshot-read service model.

Capacity sizes come from the outline; interface rates and frequencies are explicitly
declared teaching assumptions. No remote
addressing, coherence, bandwidth aggregation or device API is inferred.
"""
from fractions import Fraction
from itertools import product, combinations
import json
from pathlib import Path
import hashlib
from ..paths import PROJECT

GIB = 2**30


def calculate(copies=1):
    lock = json.loads((PROJECT / 'configs/memory-pool.lock.json').read_text())
    for row in lock:
        data = (PROJECT / row['file']).read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Memory pool outline snapshot changed')
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
    return dict(calculation='memory-pool-access',scenario=dict(copies=copies),sources=lock,
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


def markdown(result):
    c = result['capacity']
    lines = ['# 内存池：容量、周期访问与副本依赖', '',
             '| 节点 | 原容量GiB | 任务需求GiB | 借用后物理占用GiB | 剩余GiB |', '|---|---:|---:|---:|---:|']
    for i in range(4):
        lines.append(f"| {i} | 64 | {c['job_demand_bytes'][i]//GIB} | {c['physical_used_after_pool_bytes'][i]//GIB} | {c['physical_free_after_pool_bytes'][i]//GIB} |")
    lines += ['', '完整80GiB任务无法迁到任一64GiB节点；允许拆分并迁走16GiB才是另一种容量可行方案，其执行成本未知。', '',
              '| 带宽GB/s | 延迟us | 在途事务 | 读/秒 | 条件服务秒 | 负载 | 周期模型不积压 |', '|---|---:|---:|---:|---:|---:|---|']
    for row in result['access_scenarios']:
        lines.append(f"| {row['interface_bandwidth_bytes_per_second']/10**9:g} | {row['latency_ns']/1000:g} | {row['active_transactions']} | {row['reads_per_second_exact']} | {float(Fraction(row['serialized_read_service_seconds_exact'])):.9f} | {float(Fraction(row['load_exact'])):.6f} | {row['deterministic_serial_queue_bounded']} |")
    lines += ['', '| 故障节点 | 不可用任务所有者 |', '|---|---|']
    lines += [f"| {row['failed_nodes']} | {row['unavailable_job_owners']} |" for row in result['failure_sets']]
    lines += ['', *result['assumptions'], '', '```json', json.dumps(result,ensure_ascii=False,indent=2),'```','']
    return '\n'.join(lines)


def layout_svg(result):
    """Figure6-8 from the same sizes, one-copy case; no performance scaling."""
    if result['scenario']['copies'] != 1:
        raise ValueError('Figure6-8 draws the one-copy placement only')
    c=result['capacity']
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="650" viewBox="0 0 1200 650">',
           '<rect width="1200" height="650" fill="white"/>',
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10Z" fill="#b45f06"/></marker></defs>',
           '<style>text{font-family:sans-serif;fill:#17324d} .small{font-size:15px} .title{font-size:22px;font-weight:bold}</style>',
           '<text x="30" y="35" class="title">Figure 6-8: aggregate capacity does not ensure local fit or read service</text>']
    labels=['Local: node 0 needs 80 GiB','Borrow: 16 GiB stored on node 1','Read: computation stays on node 0']
    for panel,label in enumerate(labels):
        x=30+panel*390
        parts.append(f'<text x="{x}" y="80" class="small">{label}</text>')
        for node in range(4):
            y=120+node*90
            local=min(c['job_demand_bytes'][node],64*GIB)//GIB
            parts.extend([f'<text x="{x}" y="{y}" class="small">Node {node}</text>',
                          f'<rect x="{x+62}" y="{y-18}" width="256" height="34" fill="#e8edf2" stroke="#61758a"/>',
                          f'<rect x="{x+62}" y="{y-18}" width="{local*4}" height="34" fill="#3182bd"/>'])
            if panel and node==1:
                parts.append(f'<rect x="{x+62+local*4}" y="{y-18}" width="64" height="34" fill="#ef993c"/>')
            parts.append(f'<text x="{x+65}" y="{y+40}" class="small">Local {local} GiB'+(' + remote 16 GiB' if panel and node==1 else '')+'</text>')
        if panel:
            parts.append(f'<path d="M {x+330} 210 L {x+350} 210 L {x+350} 120 L {x+330} 120" fill="none" stroke="#b45f06" stroke-width="3" marker-end="url(#arrow)"/>')
    parts.extend(['<text x="30" y="520" class="small">Blue: local data. Orange: remote snapshot for node 0. Gray: free capacity. No copy back to the full local node.</text>',
                  '<text x="30" y="555" class="small">Each read: 16 GiB. At 1/60, 1, 20 reads/s, payload demand is about 0.286, 17.18, 343.60 GB/s.</text>',
                  '<text x="30" y="590" class="small">Check link service, latency and transaction window separately. Dynamic KV updates and task compute are excluded.</text>', '</svg>'])
    return '\n'.join(parts)+'\n'
