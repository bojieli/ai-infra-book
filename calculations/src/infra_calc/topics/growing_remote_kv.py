"""A versioned growing-KV communication ledger for fixed official Qwen configs.

This explicitly chosen all-replica-commit protocol is not claimed to describe
UB, RDMA or a serving engine. Compute and real transport time remain unknown.
"""
import json
from fractions import Fraction
from pathlib import Path
from ..sources import model_config, provenance, read_source
from ..units import positive_int


def geometry(model):
    if model not in ('qwen3-8b','qwen3.6-35b-a3b'):
        raise ValueError('Only pinned Qwen3-8B and Qwen3.6-35B-A3B are supported')
    config=model_config(model)
    sources=provenance(model)
    for source in sources:
        read_source(source['file'])
    t=config.get('text_config',config)
    linear=0 if model=='qwen3-8b' else t['layer_types'].count('linear_attention')
    full=t['num_hidden_layers']-linear
    fixed=linear*(4*t.get('linear_num_value_heads',0)*t.get('linear_key_head_dim',0)*t.get('linear_value_head_dim',0))
    conv=linear*2*(2*t.get('linear_num_key_heads',0)*t.get('linear_key_head_dim',0)+t.get('linear_num_value_heads',0)*t.get('linear_value_head_dim',0))*t.get('linear_conv_kernel_dim',0)
    return dict(model=model,full_attention_layers=full,linear_layers=linear,
        kv_bytes_per_position=full*2*t['num_key_value_heads']*t['head_dim']*2,
        qk_pv_flops_per_position_pair=full*4*t['num_attention_heads']*t['head_dim'],
        local_recurrent_bytes_per_request=fixed,local_convolution_bytes_per_request=conv,
        max_positions=t['max_position_embeddings'],sources=sources)


def calculate(model='qwen3-8b',batch=1,prompt=8192,steps=128,copies=1,
              placement='remote_all',bandwidth_bytes_per_second=40*10**9,
              startup_ns=5000,local_tail_budget_bytes=1024**3):
    scenario=locals().copy()
    for name in ('batch','prompt','steps','copies','bandwidth_bytes_per_second','startup_ns','local_tail_budget_bytes'):
        positive_int(scenario[name],name,allow_zero=name in ('steps','startup_ns','local_tail_budget_bytes'))
    if copies>3:
        raise ValueError('At most three distinct remote replica nodes in this four-node example')
    if placement not in ('remote_all','remote_prefix_local_tail'):
        raise ValueError('Unknown history ownership policy')
    g=geometry(model)
    if prompt+steps>g['max_positions']:
        raise ValueError('Sequence exceeds pinned context')
    unit=batch*g['kv_bytes_per_position']
    transfer=lambda size: Fraction(0) if size==0 else Fraction(startup_ns,10**9)+Fraction(size,bandwidth_bytes_per_second)
    # Copy the already-produced prompt KV to each replica through one shared
    # sender interface. Record network send payload once per destination.
    initial_messages=[dict(replica=i,bytes=prompt*unit) for i in range(copies)]
    initial_time=sum((transfer(m['bytes']) for m in initial_messages),Fraction(0))
    cursor=initial_time
    rows=[]
    remote_lengths=[prompt]*copies
    for step in range(steps):
        prior=prompt+step
        remote_positions=prior if placement=='remote_all' else prompt
        local_positions=prior-remote_positions
        read_bytes=remote_positions*unit
        read_start=cursor
        cursor+=transfer(read_bytes)
        read_finish=cursor
        writes=[]
        if placement=='remote_all':
            # Each new complete position exists locally before these sends.
            # Epoch n+1 is usable by any replica only after all copies commit.
            for replica in range(copies):
                begin=cursor
                cursor+=transfer(unit)
                remote_lengths[replica]+=1
                writes.append(dict(replica=replica,position=prior,bytes=unit,
                    start_seconds_exact=str(begin),commit_seconds_exact=str(cursor)))
        after=prior+1
        tail_after=after-prompt if placement=='remote_prefix_local_tail' else 0
        rows.append(dict(step=step,required_remote_epoch=remote_positions,
            selected_read_replica=0,remote_prior_read_bytes=read_bytes,
            local_prior_read_bytes=local_positions*unit,
            current_kv_operand_bytes=unit,
            full_attention_qk_pv_flops=batch*(prior+1)*g['qk_pv_flops_per_position_pair'],
            read_start_seconds_exact=str(read_start),read_finish_seconds_exact=str(read_finish),
            replica_writes=writes,all_replica_commit_seconds_exact=str(cursor),
            remote_lengths_after=list(remote_lengths),
            local_tail_bytes_after=tail_after*unit,
            logical_full_history_bytes_after=after*unit))
    prior_reads=unit*(steps*prompt+steps*(steps-1)//2)
    remote_reads=sum(row['remote_prior_read_bytes'] for row in rows)
    local_reads=sum(row['local_prior_read_bytes'] for row in rows)
    append_network=sum(w['bytes'] for row in rows for w in row['replica_writes'])
    local_tail=steps*unit if placement=='remote_prefix_local_tail' else 0
    local_fixed=batch*(g['local_recurrent_bytes_per_request']+g['local_convolution_bytes_per_request'])
    per_replica=remote_lengths[0]*unit
    return dict(calculation='growing-remote-kv',scenario=scenario,sources=g.pop('sources'),geometry=g,
        initial_copy_messages=initial_messages,steps=rows,
        summary=dict(full_attention_qk_pv_flops=sum(row['full_attention_qk_pv_flops'] for row in rows),initial_copy_network_bytes=copies*prompt*unit,
            prior_history_logical_read_bytes=prior_reads,remote_prior_read_bytes=remote_reads,
            local_prior_read_bytes=local_reads,current_kv_operand_bytes=steps*unit,
            append_replica_network_bytes=append_network,
            total_network_bytes=copies*prompt*unit+remote_reads+append_network,
            remote_final_bytes_per_replica=per_replica,remote_physical_final_bytes=copies*per_replica,
            local_tail_final_bytes=local_tail,local_fixed_state_bytes=local_fixed,
            local_current_append_buffer_bytes=unit if steps else 0,
            final_unique_history_bytes=(prompt+steps)*unit,
            local_tail_budget_fits=local_tail<=local_tail_budget_bytes,
            communication_skeleton_seconds_exact=str(cursor),
            initial_copy_seconds_exact=str(initial_time),
            token_communication_seconds_exact=str(cursor-initial_time),
            actual_decode_seconds=None,actual_task_feasible=None),
        assumptions=[
            '所有配置/实现原件校验后使用；BF16完整attention KV按层/头计，Qwen3.6仅10层保存全历史KV，30层FP32递推和BF16卷积槽留在计算节点，不传成历史序列。',
            'prompt是已产生的KV位置数；steps是追加单token forward次数。输入token/输出token移位明确，当前位置操作数不混入远端旧历史读取。给出的QK/PV仅完整attention子账，不含投影/专家/DeltaNet等全部计算。',
            'remote_all复制完整prompt，逐步读一个副本的所有旧位置，再将新位置发给每个副本；共享发送接口串行写入，全副本提交屏障保证下一步所有可选副本都达到要求epoch。没有实现真实一致性协议或原子性证明。',
            'remote_prefix_local_tail保持远端prompt不变，新增位置留本地；每步远端prefix和本地tail各读一次。全部模型层仍需要本地递推/卷积等状态，尾部预算只检查新增完整attention KV，不是整机容量。',
            '初始化和每消息startup+bytes/B均为声明串行传输模型。当前KV生成完成后才可追加，但计算时长和与网络重叠未知；时间轴只列通信骨架，不能视为真实decode latency或吞吐。',
            '新KV在本地先产生，current append buffer另列，不和已增长tail盲目相加为内存峰值。远端读缓存/临时buffer/控制消息/ACK/重试/故障检测及恢复未计，不推测厂商能力。',
            '初始拷贝计从外部已产出的prompt向各副本的发送；原始prompt源是否释放另由上层所有权协议决定，不计成已释放容量。副本只增加存储/写入与静态冗余，不自动增加读带宽。'])


def markdown(result):
    lines=['# 增长KV：远端历史、追加副本与提交epoch', '', '## 场景', '', '```json',json.dumps(result['scenario'],ensure_ascii=False,indent=2),'```','',
           '| 汇总 | 值 |','|---|---:|']
    lines += [f'| {key} | {value} |' for key,value in result['summary'].items()]
    lines += ['', '| 步 | 所需远端epoch | 远端旧历史bytes | 本地旧历史bytes | 当前KVbytes | 副本写bytes | 提交秒 | 本地tailbytes |',
              '|---|---:|---:|---:|---:|---:|---:|---:|']
    for row in result['steps']:
        writes=sum(w['bytes'] for w in row['replica_writes'])
        lines.append(f"| {row['step']} | {row['required_remote_epoch']} | {row['remote_prior_read_bytes']} | {row['local_prior_read_bytes']} | {row['current_kv_operand_bytes']} | {writes} | {float(Fraction(row['all_replica_commit_seconds_exact'])):.9f} | {row['local_tail_bytes_after']} |")
    lines += ['',*result['assumptions'],'','```json',json.dumps(result,ensure_ascii=False,indent=2),'```','']
    return '\n'.join(lines)
