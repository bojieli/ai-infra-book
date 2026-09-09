"""Observed corrupted-page prefetch policies, preserving censored requests."""
import hashlib
import json
from ..paths import PROJECT
from ..models import forward
from ..schema import Scenario


def read_records():
    lock=json.loads((PROJECT/'configs/cache-fault.lock.json').read_text());raw={};sources=[]
    for entry in lock['files']:
        data=(PROJECT/entry['file']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('Fault source SHA mismatch')
        raw[entry['file'].split('sources/cache-fault/',1)[1]]=data
        sources.append(dict(file=entry['file'],url='../../'+entry['origin'],sha256=entry['sha256']))
    return raw,sources


def calculate():
    raw,sources=read_records();baseline=json.loads(raw['wait_complete/config.json'])
    reference=json.loads((PROJECT/'sources/cache-restart/results/producer-v6/raw.json').read_text())['requests'][0]['response']['output_ids']
    if baseline['dtype']!='bfloat16' or not baseline['model_path'].endswith('b968826d9c46dd6066d109eabc6255188de91218'):
        raise ValueError('Unexpected reference model')
    work=forward('qwen3-8b',Scenario(tokens=1024,output_head='last'))
    rows=[];hashes=set()
    for policy in ('wait_complete','timeout','best_effort'):
        sup=json.loads(raw[f'{policy}/results/supervisor.json'])
        config=json.loads(raw[f'{policy}/config.json'])
        if config!={**baseline,'hicache_storage_prefetch_policy':policy}:raise ValueError('Uncontrolled configuration difference')
        for file,sha in sup['source_hashes'].items():
            if hashlib.sha256(raw[f'{policy}/{file}']).hexdigest()!=sha:raise ValueError('Execution identity mismatch')
        original=(PROJECT/'sources/cache-restart/storage-v3'/sup['truncated_file']).read_bytes()
        if len(original)!=sup['original_bytes'] or len(original)-sup['truncated_bytes']!=2:
            raise ValueError('Incorrect truncation size')
        if hashlib.sha256(original).hexdigest()!=sup['original_sha256'] or hashlib.sha256(original[:-2]).hexdigest()!=sup['truncated_sha256']:
            raise ValueError('Corruption does not match reference truncation')
        if sup['final_truncated_file_sha256']!=sup['truncated_sha256'] or sup['members_after_cleanup']:
            raise ValueError('Unexpected storage/cleanup outcome')
        hashes.add(sup['truncated_sha256'])
        lifecycle=[json.loads(line) for line in raw[f'{policy}/results/lifecycle.jsonl'].decode().splitlines()]
        trace=[json.loads(line) for line in raw[f'{policy}/results/storage.jsonl'].decode().splitlines()]
        starts=[row for row in lifecycle if row['event']=='request_start'];returns=[row for row in lifecycle if row['event']=='request_return']
        if len(starts)!=1:raise ValueError('Expected one observed request')
        start=starts[0]['time_s']
        gets=[row for row in trace if row['method']=='get' and row['event']=='begin']
        errors=[row for row in trace if row['event']=='exception']
        if len(gets)!=1 or len(errors)!=1 or errors[0]['type']!='OSError' or 'Short read' not in errors[0]['message']:
            raise ValueError('Missing actual short-read observation')
        if not start<=gets[0]['start_s']<=errors[0]['end_s']:raise ValueError('Read did not occur after request')
        if policy=='wait_complete':
            if returns or sup['reason']!='request_observation_expired':raise ValueError('Expected censored wait-complete request')
            elapsed=None;cached=None;matches=None;flops=None
        else:
            if len(returns)!=1 or sup['exit_code']!=0 or not any(row['event']=='shutdown_end' for row in lifecycle):
                raise ValueError('Missing completed request/clean shutdown')
            response=returns[0]['response'];meta=response['meta_info']
            if response['output_ids']!=reference or meta['cached_tokens']!=0 or meta['prompt_tokens']!=1024 or meta['completion_tokens']!=16:
                raise ValueError('Fallback output/workload mismatch')
            if errors[0]['end_s']>returns[0]['time_s']:raise ValueError('Fault was not observed before completion')
            elapsed=returns[0]['time_s']-start;cached=0;matches=True;flops=work['summary']['matrix_flops']
        rows.append(dict(policy=policy,completed=elapsed is not None,completion_seconds=elapsed,
                         observed_request_seconds=sup['request_observed_s'],
                         incomplete_observation_lower_seconds=sup['request_observed_s'] if elapsed is None else None,
                         get_attempts=len(gets),short_read_exceptions=len(errors),
                         exception_after_request_seconds=errors[0]['end_s']-start,
                         cached_tokens=cached,output_matches_reference=matches,
                         completed_fallback_prefill_matrix_flops=flops,
                         corrupt_file_reported_unchanged=True,process_exit_code=sup['exit_code']))
    if len(hashes)!=1:raise ValueError('Policies did not see the same damaged page')
    return dict(schema_version=1,calculation='cache-fault',scenario=dict(experiment='9-8 prefetch policy'),
                sources=sources+work['sources'],summary=dict(policies=3,completed_requests=2,censored_requests=1,
                    original_page_bytes=len(original),truncated_page_bytes=len(original)-2,
                    removed_bf16_elements=1,all_corrupt_files_reported_unchanged=True),fault_policy_rows=rows,
                assumptions=[
                    '导入三个策略独立进程的封存配置、执行源码、生命周期、I/O异常与监督记录；旧wait_complete不重跑。共同原页逐SHA核验，删末2bytes的预期损坏哈希与三个监督记录一致。',
                    '最终坏文件未改变来自监督器最终SHA记录，未取得三个运行存储目录的实际坏文件；不把记录核对说成再次读取坏文件。成功返回请求不等于存储已修复。',
                    'wait_complete在约60秒观测窗口未返回，完成时间为null，保留未完成观测下界；不能将观察截止当作一次完成或计算速度比。',
                    'timeout和best_effort均在返回前实际发生Short read，零缓存完成同1024输入／16输出；prefill矩阵为完整重算的逻辑工作，不含后续15decode和实际内核计量。',
                    '每策略一次、固定顺序、新条件复用编译缓存且其他服务存在，不报告吞吐、p95、SLO或性能排名。原生timeout等待阈值不是整个请求完成时限。',
                    '成功条件随后即关闭，未测试异常线程后续可用性、容量泄漏或长期服务；输出一致不构成任务质量或完整故障恢复证明。',
                ])
