"""Reaccount pinned real Agent runs; never execute model-generated code.

Measured host timings and cache-hit counters remain distinct from analytical
matrix work and hypothetical KV retention during tool waits.
"""
import hashlib
import json
from ..paths import PROJECT
from ..models import forward
from ..schema import Scenario
from ..sources import model_config, provenance
from ..units import positive_int, positive_number


def read_trace(trace):
    lock = json.loads((PROJECT / 'configs/agent-traces.lock.json').read_text())
    if trace not in lock:
        raise ValueError('Unknown pinned Agent trace')
    files = {}
    for record in lock[trace]:
        data = (PROJECT / record['file']).read_bytes()
        if hashlib.sha256(data).hexdigest() != record['sha256']:
            raise ValueError('Agent input checksum mismatch: ' + record['file'])
        name = record['file'].split('/')[-1]
        files[name] = ([json.loads(line) for line in data.splitlines()] if name.endswith('.jsonl') else json.loads(data))
    return files, lock[trace]


def calculate(trace: str = 'thinking-off', model_speedup: float = 1,
              selected_turn: int | None = None) -> dict:
    positive_number(model_speedup, 'model_speedup')
    files, records = read_trace(trace)
    raw = files['rounds.jsonl']
    if selected_turn is not None:
        positive_int(selected_turn, 'selected_turn', allow_zero=True)
        if selected_turn >= len(raw):
            raise ValueError('selected_turn is outside trace')
    model = 'qwen3-8b'
    sources = provenance(model)
    revision = files['environment.json']['config']['model'].split('/')[-1]
    if not any('/' + revision + '/' in s['url'] for s in sources):
        raise ValueError('Measured model revision differs from accounting config')
    c = model_config(model)
    unit = 4 * c['num_hidden_layers'] * c['num_key_value_heads'] * c['head_dim']
    rows = []
    previous_end = 0
    for i, record in enumerate(raw):
        p, g, hit = len(record['prompt_token_ids']), len(record['output_token_ids']), record['cached_tokens']
        positive_int(p, 'prompt tokens'); positive_int(g, 'output tokens')
        positive_int(hit, 'cached tokens', allow_zero=True)
        if hit >= p:
            raise ValueError('Trace requires at least one uncached query for last-position head')
        if record['turn'] != i:
            raise ValueError('Trace turn order is not contiguous')
        start, end, tool_start, tool_end = (record[k] for k in ('model_start_s','model_end_s','tool_start_s','tool_end_s'))
        if not previous_end <= start < end <= tool_start <= tool_end:
            raise ValueError('Trace is not a serial model/tool path')
        previous_end = tool_end
        cached = forward(model, Scenario(history=hit,tokens=p-hit))['summary']['matrix_flops']
        cold = forward(model, Scenario(tokens=p))['summary']['matrix_flops']
        decode = 0
        if g > 1:
            first = forward(model,Scenario(history=p,tokens=1))['summary']['matrix_flops']
            last = forward(model,Scenario(history=p+g-2,tokens=1))['summary']['matrix_flops']
            decode = (g-1)*(first+last)//2
        measured = end-start
        replacement = measured/model_speedup if selected_turn is None or i==selected_turn else measured
        # This is a retention scenario, not a measurement of engine cache blocks.
        retained = (p+g-1)*unit
        rows.append(dict(turn=i,prompt_tokens=p,output_tokens=g,cached_tokens=hit,uncached_tokens=p-hit,
                         finish_reason=record['finish_reason'],tool=record['action']['tool'],
                         measured_model_seconds=measured,measured_tool_seconds=tool_end-tool_start,
                         replacement_model_seconds=replacement,
                         cached_prefill_matrix_flops=cached,cold_prefill_matrix_flops=cold,
                         decode_matrix_flops=decode,
                         retained_logical_kv_bytes=retained,
                         hypothetical_tool_wait_kv_byte_seconds=retained*(tool_end-tool_start)))
    elapsed=files['final.json']['elapsed_s']
    model_seconds=sum(r['measured_model_seconds'] for r in rows)
    tool_seconds=sum(r['measured_tool_seconds'] for r in rows)
    other=elapsed-model_seconds-tool_seconds
    if elapsed < previous_end or other < 0:
        raise ValueError('Elapsed time cannot contain recorded serial stages')
    evaluation=files['independent-checks-v2.json']
    replacement=other+tool_seconds+sum(r['replacement_model_seconds'] for r in rows)
    return dict(schema_version=1,calculation='measured-agent-trace-accounting',model=model,
                scenario=dict(trace=trace,model_speedup=model_speedup,selected_turn=selected_turn),
                sources=sources+[dict(r,url='../'+r['file']) for r in records],agent_rounds=rows,
                summary=dict(turns=len(rows),input_tokens=sum(r['prompt_tokens'] for r in rows),
                             cached_input_tokens=sum(r['cached_tokens'] for r in rows),
                             uncached_input_tokens=sum(r['uncached_tokens'] for r in rows),
                             output_tokens=sum(r['output_tokens'] for r in rows),
                             cached_prefill_matrix_flops=sum(r['cached_prefill_matrix_flops'] for r in rows),
                             cold_prefill_matrix_flops=sum(r['cold_prefill_matrix_flops'] for r in rows),
                             decode_matrix_flops=sum(r['decode_matrix_flops'] for r in rows),
                             measured_model_seconds=model_seconds,measured_tool_seconds=tool_seconds,
                             measured_other_seconds=other,measured_elapsed_seconds=elapsed,
                             counterfactual_elapsed_seconds=replacement,
                             counterfactual_speedup=elapsed/replacement,
                             hypothetical_tool_wait_kv_byte_seconds=sum(r['hypothetical_tool_wait_kv_byte_seconds'] for r in rows),
                             maximum_round_logical_kv_bytes=max(r['retained_logical_kv_bytes'] for r in rows),
                             evaluation_cases=evaluation['cases'],
                             value_and_input_passed=evaluation['value_and_input_passed'],
                             including_alias_check_passed=evaluation['passed'],
                             actual_cache_peak_bytes=None),
                assumptions=[
                    '输入来自本书真实人工任务夹具的两条串行 Qwen3-8B/vLLM 轨迹，独立副本逐文件核对 SHA256 与原实验 manifest，模型 revision 对上官方 config。这里只读取数据，不执行模型生成代码。',
                    'prompt/output 长度取实际 token ID；命中取引擎 cached_tokens，不按文本相似度推算。未缓存输入不等于新增语义内容，thinking 截断与失败轮次均保留。两次结果不能当一般成功率或同工作量速度对照。',
                    '矩阵子账按有效因果位置与 last 输出头计量，冷前缀为相同输入完全重算的对照。实际引擎 chunked prefill/tile/转换/调度和采样另算，不由矩阵差额按比例缩放实测时间。prefill 产生第一个输出，之后 G−1 次 decode。',
                    '主机记录的模型墙钟包含调度和交付，工具墙钟不等于 CPU 核时；other 保留准备、间隙和最终验证等全部剩余时间。counterfactual 只替换指定模型段，其他阶段与质量假设不变；不保证更快模型仍会生成同一工具轨迹。',
                    '工具等待 KV 预算假设保留本轮全部已处理 P+G−1 个 BF16 槽，面积仅覆盖记录的工具执行区间；未证明引擎缓存实际保留这些块，不包括跨轮间隙、历史闲置块、分页对齐、并行复制或其它请求。实际缓存峰值留空。',
                    '原任务返回值／调用后输入不变通过数，与额外输出别名检查分别报告；失败任务所有轮次仍计成本，不用输出 token 总数冒充成功产出。',
                ])
