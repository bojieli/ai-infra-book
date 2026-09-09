"""Necessary publication dependencies and a stale speculative-read witness."""
from ..sources import model_config, provenance
from ..units import positive_int
from .request_dag import schedule


def stale_read(speculative_read_ns=1000, data_visible_ns=2000,
               flag_visible_ns=3000, flag_read_ns=4000, response_ns=5000,
               reread_latency_ns=2000):
    times=locals().copy()
    for name,value in times.items():
        positive_int(value,name,allow_zero=True)
    if not data_visible_ns<=flag_visible_ns<=flag_read_ns<=response_ns:
        raise ValueError('Require data publication before flag visibility, flag read and response')
    if speculative_read_ns>flag_read_ns:
        raise ValueError('Speculative sample must precede or coincide with flag read')
    old=speculative_read_ns<data_visible_ns
    sampled=0 if old else 1
    repaired=max(response_ns,flag_read_ns+reread_latency_ns) if old else response_ns
    return dict(inputs=times,initial_data=0,published_data=1,flag_observed=1,
                speculative_data=sampled,response_order_only_data=sampled,
                response_order_only_valid=not old,conflict_requires_reread=old,
                repaired_data=1,repaired_delivery_ns=repaired,
                source_ordered_delivery_ns=flag_read_ns+reread_latency_ns,
                response_order_only_read_bytes=8,repaired_read_bytes=12 if old else 8,
                events=[dict(time_ns=speculative_read_ns,event='sample_data',value=sampled),
                        dict(time_ns=data_visible_ns,event='data_visible',value=1),
                        dict(time_ns=flag_visible_ns,event='flag_visible',value=1),
                        dict(time_ns=flag_read_ns,event='sample_flag',value=1),
                        dict(time_ns=response_ns,event='deliver_flag_then_saved_data',value=sampled),
                        *([dict(time_ns=flag_read_ns,event='detect_conflict_and_start_reread',value=0),
                           dict(time_ns=flag_read_ns+reread_latency_ns,event='reread_complete',value=1)] if old else []),
                        dict(time_ns=repaired,event='deliver_validated_data',value=1)])


def calculate(model='qwen3-8b',tokens=1,write_ns=20000,recovery_ns=80000,
              notification_ns=2000,independent_ns=10000,shared_resource=False,
              read_example=None):
    for name,value in (('tokens',tokens),('write_ns',write_ns),('recovery_ns',recovery_ns),
                       ('notification_ns',notification_ns),('independent_ns',independent_ns)):
        positive_int(value,name,allow_zero=name!='tokens')
    if not isinstance(shared_resource,bool):
        raise ValueError('shared_resource must be boolean')
    config=model_config(model)
    tasks=[dict(id='write_data',duration_ns=write_ns,deps=[],resource='publication'),
           dict(id='recover_and_make_visible',duration_ns=recovery_ns,deps=['write_data'],resource='publication'),
           dict(id='publish_notification',duration_ns=notification_ns,deps=['recover_and_make_visible'],resource='publication'),
           dict(id='independent_transfer',duration_ns=independent_ns,deps=[],resource='publication' if shared_resource else 'independent')]
    strict=[dict(task,deps=['publish_notification'] if task['id']=='independent_transfer' else task['deps']) for task in tasks]
    before=schedule(strict);after=schedule(tasks)
    read=stale_read(**(read_example or {}))
    def end(result,name):
        return next(row['end_ns'] for row in result['tasks'] if row['id']==name)
    return dict(schema_version=1,calculation='operation-ordering',
                scenario=dict(model=model,tokens=tokens,write_ns=write_ns,recovery_ns=recovery_ns,
                              notification_ns=notification_ns,independent_ns=independent_ns,
                              shared_resource=shared_resource,read_example=read['inputs']),
                sources=provenance(model),request_schedules=dict(strict=before,necessary_dependencies=after),
                stale_read_example=read,
                summary=dict(each_data_transfer_bytes=2*tokens*config['hidden_size'],
                             strict_all_done_ns=before['finish_ns'],dependency_all_done_ns=after['finish_ns'],
                             strict_independent_done_ns=end(before,'independent_transfer'),
                             dependency_independent_done_ns=end(after,'independent_transfer'),
                             notification_visible_ns=end(after,'publish_notification'),
                             all_done_saved_ns=before['finish_ns']-after['finish_ns'],
                             stale_response_valid=read['response_order_only_valid'],
                             reread_required=read['conflict_requires_reread'],
                             validated_read_delivery_ns=read['repaired_delivery_ns']),
                assumptions=[
                    '两个数据传输各取官方BF16 [tokens,H]载荷，通知大小未指定；时间是教学输入，不从线速推导。写完与恢复后可见分开，通知必须等可见，独立传输没有数据依赖。',
                    'strict为明确的全完成串行教学策略，不等于任意协议的保序语义。necessary_dependencies保留发布依赖；独立资源可并发，共用容量一资源时仍要等待。恢复阶段在本例占用publication抽象资源，不泛化真实网卡行为。',
                    '取值反例是独立的两个4-byte标量D/F事件模型，与前面BF16消息不同。初始D/F=0，先写D=1再发布F=1；同刻写入视为先于取值。先投机读D再读F，即使响应按F/D交付，缓存旧D仍可能错误。',
                    '修复假设具备完整冲突检测：若投机读早于数据可见，观察F后重新读取，完成后才能交付D；计额外4-byte读取和显式读取延迟。源端顺序对照为观察F后才读取D。未模拟检测消息、失效传播或实际硬件。',
                    '这是合法性事件见证和抽象调度，不是无同步C++/NVSHMEM程序，不宣称UB规范或现有网卡实现了远端排序硬件。实际执行序、可见性、完成与回收仍须对应具体规范。',
                ])
