"""Finite conditional retry DAG: all terminal paths and their consumed resources."""
from fractions import Fraction

from ..units import positive_int


def rational(value, name):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError(name + ' requires an exact integer or fraction string')
    result = Fraction(value)
    if result < 0:
        raise ValueError(name + ' must be nonnegative')
    return result


def default_nodes():
    """Fictional conditional quality outcomes, not provider prices or measured retries."""
    return [
        dict(id='initial', cost='1/100', seconds=10, cpu_seconds=3, resident_bytes=2*1024**3,
             outcomes=[dict(probability='4/5', target='success'),
                       dict(probability='3/25', target='repair'), dict(probability='2/25', target='upgrade')]),
        dict(id='repair', cost='3/500', seconds=4, cpu_seconds=1, resident_bytes=2*1024**3,
             outcomes=[dict(probability='3/5', target='success'), dict(probability='2/5', target='upgrade')]),
        dict(id='upgrade', cost='3/100', seconds=8, cpu_seconds=2, resident_bytes=2*1024**3,
             outcomes=[dict(probability='49/50', target='success'), dict(probability='1/50', target='failure')]),
    ]


def calculate(nodes=None, start='initial', submitted_tasks=1000, deadline_seconds=20):
    positive_int(submitted_tasks, 'submitted_tasks')
    deadline = rational(deadline_seconds, 'deadline_seconds')
    nodes = default_nodes() if nodes is None else nodes
    if not isinstance(nodes, list) or not nodes or len(nodes) > 64:
        raise ValueError('Provide 1..64 finite DAG nodes')
    graph = {}
    for node in nodes:
        name = node['id']
        if not isinstance(name, str) or not name or name in graph or name in ('success', 'failure'):
            raise ValueError('Node IDs must be unique non-terminal strings')
        resources = {key: rational(node[key], key) for key in ('cost', 'seconds', 'cpu_seconds')}
        positive_int(node['resident_bytes'], 'resident_bytes', allow_zero=True)
        edges = [(rational(e['probability'], 'probability'), e['target']) for e in node['outcomes']]
        if not edges or sum(p for p, _ in edges) != 1:
            raise ValueError('Conditional outgoing probabilities must sum to one')
        graph[name] = dict(**resources, resident_bytes=node['resident_bytes'], edges=edges)
    if start not in graph:
        raise ValueError('Unknown start node')
    visited, active = set(), set()

    def validate(name):
        if name in ('success', 'failure'):
            return
        if name not in graph:
            raise ValueError('Unknown outcome target')
        if name in active:
            raise ValueError('Cycles are not finite retries; unroll attempts explicitly')
        if name in visited:
            return
        active.add(name)
        for _, target in graph[name]['edges']:
            validate(target)
        active.remove(name)
        visited.add(name)

    for name in graph:
        validate(name)
    paths, reaches = [], {name: Fraction(0) for name in graph}

    def walk(name, probability, sequence, cost, seconds, cpu, byte_seconds):
        if not probability:
            return
        if len(paths) >= 10000:
            raise ValueError('More than 10000 terminal paths; simplify the explicit scenario')
        if name in ('success', 'failure'):
            paths.append(dict(nodes=sequence, terminal=name, probability_exact=str(probability),
                              cost_exact=str(cost), seconds_exact=str(seconds), cpu_seconds_exact=str(cpu),
                              resident_byte_seconds_exact=str(byte_seconds),
                              quality_and_deadline_success=name == 'success' and seconds <= deadline))
            return
        reaches[name] += probability
        node = graph[name]
        for edge_probability, target in node['edges']:
            walk(target, probability*edge_probability, sequence+[name], cost+node['cost'],
                 seconds+node['seconds'], cpu+node['cpu_seconds'],
                 byte_seconds+node['resident_bytes']*node['seconds'])

    walk(start, Fraction(1), [], Fraction(0), Fraction(0), Fraction(0), Fraction(0))
    assert sum(Fraction(p['probability_exact']) for p in paths) == 1
    success = sum((Fraction(p['probability_exact']) for p in paths if p['terminal'] == 'success'), Fraction(0))
    timely = sum((Fraction(p['probability_exact']) for p in paths if p['quality_and_deadline_success']), Fraction(0))
    expected = {key: sum(Fraction(p['probability_exact'])*Fraction(p[key+'_exact']) for p in paths)
                for key in ('cost', 'seconds', 'cpu_seconds', 'resident_byte_seconds')}
    return dict(schema_version=1, calculation='retry-paths', sources=[],
                scenario=dict(nodes=nodes, start=start, submitted_tasks=submitted_tasks, deadline_seconds=str(deadline)),
                retry_terminal_paths=paths, retry_node_reach_probabilities={k:str(v) for k,v in reaches.items()},
                summary=dict(terminal_paths=len(paths), success_probability_exact=str(success),
                             quality_and_deadline_probability_exact=str(timely),
                             expected_attempts_exact=str(sum(reaches.values())),
                             expected_resources_per_submission={k:str(v) for k,v in expected.items()},
                             total_expected_cost_exact=str(submitted_tasks*expected['cost']),
                             expected_successes_exact=str(submitted_tasks*success),
                             cost_per_quality_success_exact=str(expected['cost']/success) if success else None,
                             cost_per_quality_and_deadline_success_exact=str(expected['cost']/timely) if timely else None),
                assumptions=[
                    '默认节点成本、时间、CPU和条件成功概率为假想教学输入；不是供应商报价、模型实测或失败后独立同分布的成功假设。输入概率明确条件于到达该节点，必要时将不同历史拆为不同节点。',
                    '有限无环图，success/failure为吸收终点。顺序尝试在结果可知后才进入下一节点，没有并行推测、超时中断、无限重试或自动重试到成功。不同路径到同节点的概率汇合，但路径时间与累计费用保留。',
                    '所有终点包含此前全部消耗，失败和超时成功费用不从分子删除；成功成本为预期费用/预期成功率，不是只取成功路径的条件平均费用。',
                    'deadline仅作完成质量与时限的联合判定，不停止正在执行的节点。零成功分母返回null，不输出0费用或无穷可靠性。',
                    '节点seconds为含等待的完整阶段墙钟，cpu_seconds为独立累计核秒；resident_bytes在该阶段内恒定，按byte-seconds累加，跨节点不重复持有。共享页、进程峰值、转移/恢复与持久状态需要另给分段。',
                    '有限图期望资源不是生产稳态吞吐或扩容收益；到达突发、并发准入、队列、实际质量关联和副作用重放仍需真实记录。',
                ])
