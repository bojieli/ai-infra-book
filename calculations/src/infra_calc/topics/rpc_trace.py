"""Recompute sealed RPC stages and paired differences without network execution."""
import hashlib
import json
from statistics import median
from ..paths import PROJECT


def read_records():
    lock=json.loads((PROJECT/'configs/rpc-traces.lock.json').read_text())
    records={};sources=[]
    for entry in lock['files']:
        path=PROJECT/entry['file'];raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=entry['sha256']:
            raise ValueError('RPC trace hash mismatch: '+entry['file'])
        name=entry['file'].split('sources/rpc-traces/')[1]
        if path.suffix=='.jsonl':records[name]=[json.loads(line) for line in raw.decode().splitlines()]
        elif path.suffix=='.json':records[name]=json.loads(raw)
        sources.append(dict(file=entry['file'],url='../../'+entry['origin'],sha256=entry['sha256']))
    return records,sources


def calculate(payload_bytes=1048576):
    records,sources=read_records()
    clients=records['results/client/requests.jsonl']
    servers=records['results/server/requests.jsonl']
    by_id={row['id']:row for row in servers}
    if len(clients)!=264 or len(servers)!=264 or len(by_id)!=264 or len({row['id'] for row in clients})!=264:
        raise ValueError('Expected 264 unique paired RPCs')
    fixtures={};derived=[]
    client_keys=['start_ns','encode_end_ns','prepare_end_ns','send_end_ns','receive_end_ns','end_ns']
    phase_names=['encode_ns','prepare_ns','send_ns','response_wait_ns','verify_ns']
    for row in clients:
        server=by_id[row['id']]
        if server!=row['server'] or server['sha256']!=row['payload_sha256'] or server['payload_bytes']!=row['size']:
            raise ValueError('Client/server identity mismatch')
        key=(row['size'],row['trial'])
        fixtures.setdefault(key,row['payload_sha256'])
        if fixtures[key]!=row['payload_sha256']:
            raise ValueError('Paired modes used different payload')
        times=[row[key] for key in client_keys]
        if times!=sorted(times):raise ValueError('Client phase order mismatch')
        metrics=dict(zip(phase_names,[b-a for a,b in zip(times,times[1:])]))
        metrics.update(total_ns=times[-1]-times[0],client_cpu_ns=row['client_cpu_ns'])
        for label,start,end in [('server_receive_ns','recv_start_ns','recv_end_ns'),
                                ('server_decode_ns','decode_start_ns','decode_end_ns'),
                                ('server_queue_ns','submit_ns','worker_start_ns'),
                                ('server_hash_ns','worker_start_ns','worker_end_ns'),
                                ('server_observe_ns','worker_end_ns','complete_observed_ns')]:
            if server[end]<server[start]:raise ValueError('Server interval reversed')
            metrics[label]=server[end]-server[start]
        derived.append(dict(id=row['id'],size=row['size'],mode=row['mode'],name=row['name'],
                            trial=row['trial'],warmup=row['warmup'],metrics=metrics,
                            request_application_bytes=row['request_application_bytes']))
    selected=[row for row in derived if row['size']==payload_bytes and not row['warmup']]
    if len(selected)!=80:raise ValueError('Payload must match a recorded 1024, 65536 or 1048576-byte case')
    groups=[]
    for mode in range(4):
        group=sorted([row for row in selected if row['mode']==mode],key=lambda row:row['trial'])
        if [row['trial'] for row in group]!=list(range(20)):
            raise ValueError('Missing paired trial')
        values={key:[row['metrics'][key] for row in group] for key in group[0]['metrics']}
        groups.append(dict(mode=mode,name=group[0]['name'],samples=20,
                           medians_ns={key:median(value) for key,value in values.items()},
                           total_min_ns=min(values['total_ns']),total_max_ns=max(values['total_ns']),
                           total_p95_ns=sorted(values['total_ns'])[18],
                           request_application_bytes=sorted({row['request_application_bytes'] for row in group})))
    pairs=[]
    indexed={(row['mode'],row['trial']):row for row in selected}
    for before,after in ((0,1),(1,2),(2,3)):
        differences=[indexed[before,trial]['metrics']['total_ns']-indexed[after,trial]['metrics']['total_ns'] for trial in range(20)]
        pairs.append(dict(before=groups[before]['name'],after=groups[after]['name'],
                          saved_ns=differences,median_saved_ns=median(differences),
                          positive_pairs=sum(value>0 for value in differences),
                          median_difference_ns=groups[before]['medians_ns']['total_ns']-groups[after]['medians_ns']['total_ns']))
    return dict(schema_version=1,calculation='rpc-trace',scenario=dict(payload_bytes=payload_bytes),
                sources=sources,rpc_groups=groups,rpc_pairs=pairs,rpc_requests=selected,
                summary=dict(verified_record_pairs=264,selected_measured_calls=80,excluded_warmup_calls=24,
                             json_client_cpu_median_ns=groups[0]['medians_ns']['client_cpu_ns'],
                             binary_client_cpu_median_ns=groups[1]['medians_ns']['client_cpu_ns'],
                             json_request_application_bytes=groups[0]['request_application_bytes'],
                             binary_request_application_bytes=groups[1]['request_application_bytes'],
                             json_to_binary_paired_median_saved_ns=pairs[0]['median_saved_ns'],
                             json_to_binary_positive_pairs=pairs[0]['positive_pairs']),
                assumptions=[
                    '真实实验7-4：Apple M2 Max客户端到RTX主机Linux CPU服务端，经持久TCP和SSH转发，单次一个在途；GPU未使用。不是模型推理、RDMA、数据中心直连或裸链路测量。',
                    '三种载荷、四种模式、每条件2次预热20次正式测量，共264次。校验封存哈希、两端记录、载荷身份与同轮各模式配对；当前选定一种载荷80次正式调用。',
                    '客户端相邻五阶段逐次相加等于完整RPC；CPU时间另列，不与墙钟相加。服务端时钟独立，只算本地差值；服务端阶段与客户端发送／等待重叠，不能再加到客户端总时间。',
                    '各阶段中位数不保证相加等于总中位数。配对差为同轮before-after，正数表示变快；差的中位数不等于两个中位数之差，保留全部20个差值与正差次数。p95取20条排序第19条。',
                    '应用请求字节不含TCP/IP/SSH framing。binary copy→view同时改变拼接／发送API与服务端物化；worker→inline改变交接路径。局部CPU下降不自动证明完整调用稳定变快，有限配对结果不是显著性或总体性能保证。',
                ])
