"""Explicit local endpoint/peer relations and isolated shared transport counts."""
from ..units import positive_int


def calculate(threads=64, peers=128, isolation_classes=1, relations=None,
              endpoint_state_bytes=256, relation_state_bytes=64,
              transport_state_bytes=1024, budget_bytes=1048576):
    for name,value in (('threads',threads),('peers',peers),('isolation_classes',isolation_classes)):
        positive_int(value,name)
    for name,value in (('endpoint_state_bytes',endpoint_state_bytes),
                       ('relation_state_bytes',relation_state_bytes),
                       ('transport_state_bytes',transport_state_bytes),('budget_bytes',budget_bytes)):
        positive_int(value,name,allow_zero=True)
    if threads*peers>100000 and relations is None:
        raise ValueError('Provide sparse relations for large endpoint products')
    # A local endpoint belongs to one isolation class; sharing never crosses it.
    if relations is None:
        relations=[dict(thread=t,peer=p) for t in range(threads) for p in range(peers)]
    if not isinstance(relations,list):
        raise ValueError('relations must be a list')
    unique=set()
    groups={}
    for relation in relations:
        thread,peer=relation['thread'],relation['peer']
        positive_int(thread,'thread index',allow_zero=True)
        positive_int(peer,'peer index',allow_zero=True)
        if thread>=threads or peer>=peers:
            raise ValueError('Relation index exceeds configured endpoints')
        if (thread,peer) in unique:
            raise ValueError('Duplicate endpoint-peer relation')
        unique.add((thread,peer))
        groups.setdefault((peer,thread%isolation_classes),[]).append(thread)
    endpoints=threads*endpoint_state_bytes
    bindings=len(unique)*relation_state_bytes
    coupled_transport=len(unique)*transport_state_bytes
    shared_transport=len(groups)*transport_state_bytes
    coupled=endpoints+bindings+coupled_transport
    shared=endpoints+bindings+shared_transport
    rows=[dict(peer=peer,isolation_class=cls,threads=sorted(members),
               relation_count=len(members),transport_state_bytes=transport_state_bytes)
          for (peer,cls),members in sorted(groups.items())]
    return dict(schema_version=1,calculation='connection-states',
                scenario=dict(threads=threads,peers=peers,isolation_classes=isolation_classes,
                              relations=relations,endpoint_state_bytes=endpoint_state_bytes,
                              relation_state_bytes=relation_state_bytes,
                              transport_state_bytes=transport_state_bytes,budget_bytes=budget_bytes),
                sources=[],transport_groups=rows,
                summary=dict(possible_local_relations=threads*peers,active_relations=len(unique),
                             allocated_local_endpoints=threads,active_local_endpoints=len({t for t,p in unique}),
                             active_peers=len({p for t,p in unique}),
                             coupled_transport_count=len(unique),shared_transport_count=len(groups),
                             endpoint_bytes=endpoints,relation_bytes=bindings,
                             coupled_transport_bytes=coupled_transport,shared_transport_bytes=shared_transport,
                             coupled_total_bytes=coupled,shared_total_bytes=shared,
                             saved_bytes=coupled-shared,coupled_fits_budget=coupled<=budget_bytes,
                             shared_fits_budget=shared<=budget_bytes,
                             largest_shared_group_relations=max((len(members) for members in groups.values()),default=0)),
                assumptions=[
                    '只计本机threads个已分配端点到peers个远端的有向活跃关系，不是集群全网无向连接数，不对接收端再乘二。默认完整笛卡尔积，可显式给稀疏关系。',
                    '教学组织一为每活跃关系独立传输状态，组织二按(peer, thread modulo isolation_classes)复用。关系绑定仍逐项保留，所有本地端点仍计容量；不跨隔离类共享。',
                    '默认端点256、关系绑定64、传输1024 bytes和1MiB预算均为显式教学假设，不是UB Jetty/TP或任何网卡/QP官方结构大小。计数映射不冒称实际实现。',
                    '共享组人数只描述共享范围，不是吞吐、公平、热点流量或队头阻塞预测。共享并未消除关系管理；队列、完成项、包缓存、页表和动态故障状态需另行给定。',
                ])
