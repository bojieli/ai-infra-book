"""Deterministic non-preemptive request DAG with explicit serial resources."""
from ..units import positive_int


def schedule(tasks):
    by_id={task['id']:task for task in tasks}
    pending=list(by_id);done={};resource_last={};rows=[]
    while pending:
        ready=[]
        for index,name in enumerate(pending):
            task=by_id[name]
            if not all(dep in done for dep in task['deps']):continue
            predecessors=list(task['deps'])
            resource=task.get('resource')
            if resource is not None and resource in resource_last:
                predecessors.append(resource_last[resource])
            predecessor=max(predecessors,key=lambda key:done[key]['end_ns']) if predecessors else None
            start=done[predecessor]['end_ns'] if predecessor else 0
            ready.append((start,index,name,predecessor,predecessors))
        if not ready:raise ValueError('Dependency cycle')
        start,index,name,predecessor,predecessors=min(ready)
        task=by_id[name]
        row=dict(id=name,resource=task.get('resource'),start_ns=start,end_ns=start+task['duration_ns'],
                 duration_ns=task['duration_ns'],critical_predecessor=predecessor,
                 scheduled_predecessors=list(dict.fromkeys(predecessors)))
        rows.append(row);done[name]=row;pending.remove(name)
        if task.get('resource') is not None:resource_last[task['resource']]=name
    terminal=max(done,key=lambda key:done[key]['end_ns'])
    path=[];cursor=terminal
    while cursor is not None:
        path.append(cursor);cursor=done[cursor]['critical_predecessor']
    path.reverse()
    return dict(tasks=rows,finish_ns=done[terminal]['end_ns'],critical_path=path,
                serial_work_ns=sum(task['duration_ns'] for task in tasks))


def calculate(tasks=None,duration_overrides=None,resource_overrides=None):
    example = tasks is None
    tasks=tasks if tasks is not None else [
        dict(id='prepare',duration_ns=10000,deps=[],resource='host'),
        dict(id='hotspot',duration_ns=60000,deps=['prepare'],resource='compute'),
        dict(id='parallel',duration_ns=40000,deps=['prepare'],resource='transfer'),
        dict(id='finish',duration_ns=10000,deps=['hotspot','parallel'],resource='host')]
    duration_overrides=({'hotspot':15000} if example else {}) if duration_overrides is None else duration_overrides
    resource_overrides={} if resource_overrides is None else resource_overrides
    if not isinstance(tasks,list) or not tasks:raise ValueError('Nonempty task list required')
    names=set()
    for task in tasks:
        name=task['id']
        if not isinstance(name,str) or not name or name in names:raise ValueError('Unique nonempty task IDs required')
        names.add(name)
        positive_int(task['duration_ns'],'duration_ns',allow_zero=True)
        if not isinstance(task['deps'],list) or any(not isinstance(x,str) for x in task['deps']):raise ValueError('deps must be IDs')
        if task.get('resource') is not None and not isinstance(task['resource'],str):raise ValueError('resource must be string or null')
    for task in tasks:
        if any(dep not in names for dep in task['deps']):raise ValueError('Unknown dependency')
    if not isinstance(duration_overrides,dict) or not isinstance(resource_overrides,dict):raise ValueError('Overrides must be mappings')
    if (set(duration_overrides)|set(resource_overrides))-names:raise ValueError('Override names unknown task')
    for value in duration_overrides.values():positive_int(value,'override duration',allow_zero=True)
    for value in resource_overrides.values():
        if value is not None and not isinstance(value,str):raise ValueError('resource override must be string or null')
    changed=[dict(task,duration_ns=duration_overrides.get(task['id'],task['duration_ns']),
                  resource=resource_overrides.get(task['id'],task.get('resource'))) for task in tasks]
    baseline=schedule(tasks);modified=schedule(changed)
    # Amdahl applies exactly to this explicit serial-equivalent work sum.
    serial_before=baseline['serial_work_ns'];serial_after=modified['serial_work_ns']
    old_path=set(baseline['critical_path'])
    frozen_path=sum(task['duration_ns'] for task in changed if task['id'] in old_path)
    return dict(schema_version=1,calculation='request-dag',
                scenario=dict(tasks=tasks,duration_overrides=duration_overrides,resource_overrides=resource_overrides),
                sources=[],request_schedules=dict(baseline=baseline,modified=modified),
                summary=dict(baseline_finish_ns=baseline['finish_ns'],modified_finish_ns=modified['finish_ns'],
                             request_speedup=baseline['finish_ns']/modified['finish_ns'] if modified['finish_ns'] else None,
                             baseline_critical_path=baseline['critical_path'],modified_critical_path=modified['critical_path'],
                             serial_equivalent_before_ns=serial_before,serial_equivalent_after_ns=serial_after,
                             serial_equivalent_speedup=serial_before/serial_after if serial_after else None,
                             frozen_old_path_ns=frozen_path,
                             actual_measured_request_ns=None),
                assumptions=[
                    '默认四节点是教学请求依赖图，prepare10us、hotspot60us、并行分支40us、finish10us；只将hotspot改为15us，不假称真实模型trace。',
                    '显式依赖完成后节点才可启动；相同resource为容量一的不可抢占串行资源，null表示不约束资源。调度选择最早可启动节点，同刻按输入顺序，记录资源前序形成的等待边，不声称全局最优调度。',
                    '完成定义为全部给定节点完成，不包含未输入的到达排队、启动或外部工作。资源为抽象互斥通路，不把不同资源名自动当成真实GPU可独占分区的证据。',
                    '关键路径在依赖与实际资源顺序构成的图上重算；frozen_old_path只展示旧路径换时长的值，不把它当优化后请求耗时。并行分支或资源顺序改变可能转移瓶颈。',
                    'serial_equivalent是将全部任务串行化后可用Amdahl比较的成本，不能把并行trace中kernel时间求和占比直接套到请求墙钟。',
                    'duration/resource覆盖支持显式校准或争用情景；共享资源减速不是由本模型自动预测，必须另给并发时长或经过验证的资源映射。无实验5-9替换前后记录时不声明真实请求收益。',
                ])
