"""C52: declared Qwen TP×EP migration and service-lifetime accounting.

Standard library only. No engine execution, weight files, or performance prediction.
Weights and model geometry come from the checkout's pinned official configs.
"""
from copy import deepcopy
from fractions import Fraction
from math import prod, ceil

from infra_calc.models import qwen3, qwen3_moe
from infra_calc.sources import model_config, provenance
from infra_calc.topics.checkpoint_reshard import partition_ranges

RUNTIME_TERMS = ('local_materialization', 'drain', 'group_setup', 'weight_repack', 'state_validation',
                 'compile_graph', 'atomic_cutover', 'replay_prefill', 'queue_clearance')
COST_TERMS = ('startup', 'steady_service', 'routing_and_cache', 'migration',
              'warm_overlap', 'recovery_and_replay', 'failed_attempts', 'backlog_clearance',
              'network_storage', 'host_control_plane')


def integer(value, name, zero=False):
    if type(value) is not int or value < (0 if zero else 1):
        raise ValueError(f'{name} must be an integer >= {0 if zero else 1}')
    return value


def number(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Fraction)):
        raise ValueError(f'{name} must be a finite numeric value')
    try:
        result = Fraction(str(value))
    except (ValueError, ZeroDivisionError):
        raise ValueError(f'{name} must be a finite numeric value') from None
    if result < 0 or (positive and result == 0):
        raise ValueError(f'{name} must be nonnegative (positive for rates)')
    return result


def layout(config, spec):
    if integer(spec.get('pp', 1), 'pp') != 1 or integer(spec.get('dp', 1), 'dp') != 1:
        raise ValueError('This layout supports PP=DP=1 only')
    tp, ep = integer(spec['tp'], 'tp'), integer(spec['ep'], 'ep')
    devices = spec['devices']
    if (not isinstance(devices, list) or len(devices) != tp * ep
            or any(not isinstance(d, str) or not d for d in devices)
            or len(set(devices)) != len(devices)):
        raise ValueError('devices must be unique nonempty strings, EP-major then TP-major')
    experts = config.get('num_experts', 0)
    if (experts == 0 and ep != 1) or (experts and ep > experts):
        raise ValueError('Dense requires EP=1; every MoE EP rank must own experts')
    f = config.get('moe_intermediate_size', config['intermediate_size'])
    if any(n % tp for n in (config['num_attention_heads'], f, config['vocab_size'])):
        raise ValueError('TP must divide Q heads, FFN width and vocabulary')
    return tp, ep, devices


def intervals(config, spec, batch, history, auxiliary_bytes):
    """Each tensor uses an invariant sharding axis, other axes folded into unit_bytes.

    Layer template repeats remain distinct logical copies with identical placement.
    Column slices describe logical rectangles, not contiguous checkpoint file reads.
    """
    tp, ep, devices = layout(config, spec)
    adapter = qwen3_moe if config['model_type'] == 'qwen3_moe' else qwen3
    weights = adapter.weights(config)
    expert_ranges = partition_ranges(config['num_experts'], 1, ep, 'rows') if ep > 1 else [(0, config.get('num_experts', 0))]
    entries = {}
    for w in weights:
        name, shape = w.name, w.shape
        expert = int(name.split('.experts.')[1].split('.')[0]) if '.experts.' in name else None
        axis, unit, count = None, 2 * w.copies, 1
        if name in ('model.embed_tokens.weight', 'lm_head.weight'):
            axis = 0
        elif any(s in name for s in ('.q_proj.', '.k_proj.', '.v_proj.')):
            axis = 0
        elif '.o_proj.' in name or '.down_proj.' in name:
            axis = 1
        elif '.gate_proj.' in name or '.up_proj.' in name:
            axis = 0
        if axis is None:
            unit *= prod(shape)
        else:
            count = shape[axis]
            unit *= prod(shape[:axis] + shape[axis + 1:])
        owners = []
        for e in range(ep):
            if expert is not None and not expert_ranges[e][0] <= expert < expert_ranges[e][1]:
                continue
            for t in range(tp):
                if axis is None:
                    start, stop = 0, 1
                elif '.k_proj.' in name or '.v_proj.' in name:
                    q = config['num_attention_heads'] // tp
                    group = config['num_attention_heads'] // config['num_key_value_heads']
                    start = (t * q // group) * config['head_dim']
                    stop = (( (t + 1) * q - 1) // group + 1) * config['head_dim']
                else:
                    start, stop = t * (count // tp), (t + 1) * (count // tp)
                owners.append(dict(device=devices[e * tp + t], start=start, stop=stop))
        entries[name] = dict(kind='weight', unit_bytes=unit, owners=owners)
    if batch * history:
        owners = []
        for e in range(ep):
            for t in range(tp):
                q = config['num_attention_heads'] // tp
                group = config['num_attention_heads'] // config['num_key_value_heads']
                owners.append(dict(device=devices[e * tp + t], start=t*q//group,
                                   stop=((t+1)*q-1)//group+1))
        entries['request_kv'] = dict(kind='kv', unit_bytes=2 * 2 * config['num_hidden_layers'] * batch * history * config['head_dim'], owners=owners)
    if auxiliary_bytes:
        quotient,remainder=divmod(auxiliary_bytes,len(devices))
        ranges=[(i*quotient+min(i,remainder),(i+1)*quotient+min(i+1,remainder)) for i in range(len(devices))]
        entries['auxiliary_state'] = dict(kind='auxiliary', unit_bytes=1,
            owners=[dict(device=d, start=a, stop=b) for d, (a,b) in zip(devices, ranges)])
    return entries


def transfer_plan(source, target):
    """Choose local copy first, otherwise lexicographically first valid source.

    Every destination coordinate is covered once, even if sources replicate it.
    This is deterministic direct unicast, not an optimal network schedule.
    """
    pieces = []
    for name, dst in target.items():
        src = source[name]
        if src['unit_bytes'] != dst['unit_bytes']:
            raise ValueError('State geometry/format changed')
        for owner in dst['owners']:
            cuts = {owner['start'], owner['stop']}
            for old in src['owners']:
                cuts.update(x for x in (old['start'], old['stop']) if owner['start'] < x < owner['stop'])
            cuts = sorted(cuts)
            for a, b in zip(cuts, cuts[1:]):
                candidates = [o['device'] for o in src['owners'] if o['start'] <= a and o['stop'] >= b]
                if not candidates:
                    raise ValueError(f'Unavailable source range: {name} [{a}, {b})')
                chosen = owner['device'] if owner['device'] in candidates else min(candidates)
                pieces.append(dict(tensor=name, kind=dst['kind'], start=a, stop=b,
                    source=chosen, target=owner['device'], bytes=(b-a)*dst['unit_bytes'],
                    local=chosen == owner['device']))
    return pieces


def amortization(overhead, saving_per_step):
    """Nonnegative incremental overhead and signed per-step savings, same units."""
    if overhead is None or saving_per_step is None:
        return dict(status='missing_input', break_even_steps=None, strictly_better_steps=None)
    overhead = number(overhead, 'overhead')
    if isinstance(saving_per_step, bool):
        raise ValueError('saving_per_step must be numeric')
    saving = Fraction(str(saving_per_step))
    if saving <= 0:
        return dict(status='no_positive_saving', break_even_steps=0 if overhead == 0 else None,
                    strictly_better_steps=None)
    ratio = overhead / saving
    return dict(status='conditional', continuous_steps_exact=str(ratio),
                break_even_steps=ceil(ratio), strictly_better_steps=ratio.numerator // ratio.denominator + 1)


def deployment_cost(spec):
    """All declared spend including unsuccessful work; no vendor prices inferred.

    Each category is null/missing, an explicit zero list, or charge rows with
    quantity × rate in one declared currency. Unknown fields survive in input.
    """
    if spec and (not isinstance(spec.get('currency'),str) or not spec['currency'].strip()):
        raise ValueError('A nonempty cost currency/unit is required')
    terms = spec.get('terms', {})
    subtotals, missing = {}, []
    for key in dict.fromkeys((*COST_TERMS, *terms)):
        rows = terms.get(key)
        if rows is None:
            subtotals[key] = None
            missing.append(key)
            continue
        if not isinstance(rows, list):
            raise ValueError('Cost categories must be lists or null')
        total = Fraction(0)
        for row in rows:
            if row.get('quantity') is None or row.get('rate') is None:
                missing.append(key)
                total = None
                break
            total += number(row['quantity'], 'quantity') * number(row['rate'], 'rate')
        subtotals[key] = str(total) if total is not None else None
    known = sum((Fraction(v) for v in subtotals.values() if v is not None), Fraction(0))
    successful = spec.get('slo_valid_completed_requests')
    if successful is not None:
        integer(successful, 'slo_valid_completed_requests', zero=True)
    return dict(currency=spec.get('currency'), subtotals_exact=subtotals,
                known_subtotal_exact=str(known), missing_terms=missing,
                full_declared_cost_exact=None if missing else str(known),
                cost_per_slo_valid_request_exact=str(known / successful) if not missing and successful else None,
                observed_or_measured=False)


def calculate(scenario):
    s = deepcopy(scenario)
    model = s['model']
    c = model_config(model)
    if c['model_type'] not in ('qwen3', 'qwen3_moe'):
        raise ValueError('Only pinned Qwen3 Dense/MoE supported')
    batch = integer(s.get('batch', 1), 'batch')
    history = integer(s.get('history', 0), 'history', zero=True)
    if history > c['max_position_embeddings']:
        raise ValueError('History exceeds pinned context')
    aux = integer(s.get('auxiliary_state_bytes', 0), 'auxiliary_state_bytes', zero=True)
    if s.get('state_policy', 'migrate') not in ('migrate', 'replay'):
        raise ValueError('state_policy must be migrate or replay')
    if s.get('same_weight_version', True) is not True or s.get('state_identity_verified', False) is not True:
        raise ValueError('Requires same weight version and explicit state identity/format verification')
    source = intervals(c, s['source'], batch, history, aux)
    target = intervals(c, s['target'], batch, history, aux)
    pieces = transfer_plan(source, target)
    if s.get('state_policy') == 'replay':
        pieces = [p for p in pieces if p['kind'] != 'kv']
    sent, received = {}, {}
    totals = {k:dict(local_bytes=0, network_bytes=0) for k in ('weight','kv','auxiliary')}
    for p in pieces:
        totals[p['kind']]['local_bytes' if p['local'] else 'network_bytes'] += p['bytes']
        if not p['local']:
            sent[p['source']] = sent.get(p['source'], 0) + p['bytes']
            received[p['target']] = received.get(p['target'], 0) + p['bytes']
    rates = s.get('bandwidth', {})
    network = sum(sent.values())
    bounds = {}
    for key, payload in (('fabric_bytes_per_second', network),
                         ('sender_bytes_per_second', max(sent.values(), default=0)),
                         ('receiver_bytes_per_second', max(received.values(), default=0))):
        rate = rates.get(key)
        bounds[key] = str(Fraction(payload) / number(rate, key, positive=True)) if rate is not None else ('0' if not network else None)
    complete_bound = all(v is not None for v in bounds.values())
    bound = max((Fraction(v) for v in bounds.values() if v is not None), default=Fraction(0))
    runtime = s.get('runtime_seconds', {})
    missing_runtime = [k for k in dict.fromkeys((*RUNTIME_TERMS, *runtime)) if runtime.get(k) is None]
    runtime_sum = sum((number(v, k) for k,v in runtime.items() if v is not None), Fraction(0))
    # Fully materialized new buffers on every target; no aliasing even for local bytes.
    cards = []
    def resident(entries, device):
        return sum((o['stop']-o['start'])*v['unit_bytes'] for v in entries.values() for o in v['owners'] if o['device']==device)
    for d in sorted(set(s['source']['devices'] + s['target']['devices'])):
        old, new = resident(source,d), resident(target,d)
        extra = s.get('extra_live_bytes_by_device', {}).get(d, 0)
        integer(extra, 'extra_live_bytes', zero=True)
        cap = s.get('capacity_bytes_by_device', {}).get(d)
        if cap is not None:
            integer(cap, 'capacity_bytes')
        cards.append(dict(device=d, old_resident_bytes=old, target_resident_bytes=new,
                          declared_copy_before_release_peak_bytes=old+new+extra,
                          capacity_bytes=cap, fits_declared_peak=None if cap is None else old+new+extra<=cap))
    a = s.get('amortization', {})
    supplied_transfer=s.get('network_transfer_seconds')
    if supplied_transfer is not None:
        supplied_transfer=number(supplied_transfer,'network_transfer_seconds')
        if supplied_transfer<bound:raise ValueError('Network transfer time is below a known resource lower bound')
    if not network and supplied_transfer is None:supplied_transfer=Fraction(0)
    horizon=a.get('remaining_steps')
    if horizon is not None:integer(horizon,'remaining_steps',zero=True)
    def scoped_amortization(overhead,saving):
        result=amortization(overhead,saving)
        result['remaining_steps']=horizon
        result['strictly_better_within_horizon']=None if horizon is None or overhead is None or saving is None else (result['strictly_better_steps'] is not None and horizon>=result['strictly_better_steps'])
        result['scope']='Caller incremental overhead and equal-work per-step saving; independent of unmeasured switch latency. Capacity and SLO feasibility must be checked separately.'
        return result
    return dict(schema_version=1, calculation='tp-ep-reconfiguration', model=model, scenario=s,
        sources=provenance(model), transfers=pieces, migration_totals=totals,
        sender_bytes=sent, receiver_bytes=received, placement_cards=cards,
        transfer_bounds_exact_seconds=bounds,
        summary=dict(network_bytes=network, transfer_lower_bound_exact_seconds=str(bound) if complete_bound else None,
            partial_known_transfer_bound_exact_seconds=str(bound), missing_runtime_terms=missing_runtime,
            known_serial_runtime_seconds_exact=str(runtime_sum),
            conditional_serial_switch_lower_bound_exact_seconds=str(bound+runtime_sum) if complete_bound and not missing_runtime else None,
            supplied_network_transfer_seconds_exact=None if supplied_transfer is None else str(supplied_transfer),
            declared_serial_switch_seconds_exact=str(supplied_transfer+runtime_sum) if supplied_transfer is not None and not missing_runtime else None,
            local_materialization_read_write_bytes=2*sum(v['local_bytes'] for v in totals.values()),
            all_declared_capacities_fit=False if any(c['fits_declared_peak'] is False for c in cards) else (None if any(c['fits_declared_peak'] is None for c in cards) else True),
            measured_switch_seconds=None, predicted_end_to_end_seconds=None),
        amortization=dict(time=scoped_amortization(a.get('extra_seconds'),a.get('seconds_saved_per_step')),
                          money=scoped_amortization(a.get('extra_cost'),a.get('cost_saved_per_step'))),
        deployment_cost=deployment_cost(s.get('deployment_cost', {})),
        assumptions=[
            'One inference TP×EP group, PP=DP=1. EP owns contiguous quotient/remainder expert IDs; nonexpert weights and the SAME request KV replicate across EP groups. No independent EP request batches inferred.',
            'BF16 full weights and BF16 GQA KV; all routed experts included. TP follows dense_placement axes, whole KV heads replicate when TP exceeds KV heads. Router/norm weights replicate.',
            'Same layer/head/token/position/model-version/format identities are caller-verified assertions, not engine validation. Auxiliary bytes describe caller-defined flat immutable snapshot state, not inferred optimizer/WAL contents.',
            'Direct unicast selects a local source then first device lexicographically; source replicas are not double counted. Byte intervals on sharding axes are logical rectangles; column slices require packing, not contiguous file reads.',
            'Snapshot is quiescent. No background mutation, dirty KV chase, automatic retry or failed-source reconstruction. Replay transfers no old KV but target KV capacity remains budgeted; replay/token-log availability and time must be supplied.',
            'Same-card local_bytes means destination materialization from a local source, not zero-copy retained buffers. Its read+write interfaces are reported; local_materialization time is separately required. Partial tensor aliases are not assumed.',
            'Bandwidths are hypothetical effective aggregate fabric and per-device rates. Maximum resource bound is necessary only; known serial runtime sum is a declared schedule, not measured readiness or SLO.',
            'Peak uses old+fully materialized target+declared extras per physical device, with old buffers held until release. Extra graph/workspace/allocator/transfer scratch require caller budgeting; fit is only for declared allocations.',
            'Cost ledger includes all declared lifecycle terms and extra categories; unknown terms stay null. Quantities/rates, SLO counts and per-step savings are teaching inputs, not measured data or prices. Categories must be disjoint to avoid double charging.',
        ])


def markdown(result):
    """Render migration ownership separately from the generic placement schema."""
    import json
    from collections import defaultdict

    def cell(value):
        return '未知' if value is None else str(value).replace('|', '\\|').replace('\n', ' ')

    lines = ['# TP/EP 重配置迁移子账', '',
             '范围：静止快照、BF16、PP=DP=1；资源下界不是实际运行时间，原 C52 完整部署成本尚未闭合。', '',
             '## 输入', '', '```json', json.dumps(result['scenario'], ensure_ascii=False, indent=2), '```', '',
             '## 载荷与本地物化', '', '| 类别 | 本地源 bytes | 网络 bytes |', '| --- | ---: | ---: |']
    for kind, row in result['migration_totals'].items():
        lines.append(f"| {kind} | {row['local_bytes']} | {row['network_bytes']} |")
    lines.extend(['', '本地源仍创建目标缓冲；不假设零复制别名。读写接口为本地载荷的两倍。', '',
                  '## 逐卡容量', '', '| 设备 | 旧 bytes | 目标 bytes | 保留旧缓冲时峰值 bytes | 声明容量 bytes | 可容纳 |',
                  '| --- | ---: | ---: | ---: | ---: | --- |'])
    for row in result['placement_cards']:
        lines.append('| ' + ' | '.join(cell(row[k]) for k in ('device', 'old_resident_bytes', 'target_resident_bytes',
                     'declared_copy_before_release_peak_bytes', 'capacity_bytes', 'fits_declared_peak')) + ' |')
    lines.extend(['', '## 资源下界与声明时间', '',
                  '以下秒数为精确有理数。缺项保持未知；即使容量合格，也不推出切换可达、SLO合格或恢复成功。', '',
                  '| 字段 | 值 |', '| --- | --- |'])
    for key, value in {**result['transfer_bounds_exact_seconds'], **result['summary']}.items():
        lines.append(f'| {key} | {cell(value)} |')
    lines.extend(['', '## 传输端点汇总', '',
                  '每个目标坐标只选一个源，优先同卡，再按设备名字排序。完整 tensor/axis 坐标保留在 JSON；这不是最优链路调度。', '',
                  '| 类别 | 源 | 目标 | 本地 | bytes |', '| --- | --- | --- | --- | ---: |'])
    grouped = defaultdict(int)
    for row in result['transfers']:
        grouped[(row['kind'], row['source'], row['target'], row['local'])] += row['bytes']
    for key, value in sorted(grouped.items()):
        lines.append('| ' + ' | '.join(cell(v) for v in (*key, value)) + ' |')
    for title, key in [('条件摊销与剩余步数', 'amortization'), ('声明生命周期费用', 'deployment_cost')]:
        lines.extend(['', '## ' + title, '', '```json', json.dumps(result[key], ensure_ascii=False, indent=2), '```'])
    lines.extend(['', '## 假设与未闭合项', ''])
    lines.extend('- ' + value for value in result['assumptions'])
    lines.extend(['', '## 固定官方来源', '', '```json', json.dumps(result['sources'], ensure_ascii=False, indent=2), '```', ''])
    return '\n'.join(lines)
