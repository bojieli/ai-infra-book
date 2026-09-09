"""Official FFN offload bytes with safe finite-slot prefetch scheduling."""
from fractions import Fraction
from ..models import forward,qwen3
from ..sources import model_config,provenance
from ..schema import Scenario
from ..units import positive_int
from .request_dag import schedule


def calculate(model='qwen3-8b',offloaded_layers=None,buffer_slots=1,passes=1,batch=1,tokens=1,
              history=8192,kv_length=8192,bandwidth_bytes_per_second=24*2**30,
              layer_compute_ns=1000000):
    c=model_config(model);qwen3.validate(c);layers=c['num_hidden_layers']
    offloaded_layers=list(range(3,layers,4)) if offloaded_layers is None else offloaded_layers
    if not isinstance(offloaded_layers,list) or not offloaded_layers or len(set(offloaded_layers))!=len(offloaded_layers):raise ValueError('Unique nonempty layer list required')
    for layer in offloaded_layers:
        positive_int(layer,'layer',allow_zero=True)
        if layer>=layers:raise ValueError('Offload layer outside model')
    offloaded_layers=sorted(offloaded_layers)
    for name,value in [('buffer_slots',buffer_slots),('passes',passes),('batch',batch),('tokens',tokens),('kv_length',kv_length),
                       ('bandwidth_bytes_per_second',bandwidth_bytes_per_second),('layer_compute_ns',layer_compute_ns)]:positive_int(value,name)
    positive_int(history,'history',allow_zero=True)
    if passes>16 or buffer_slots>len(offloaded_layers):raise ValueError('At most16 passes; slots must not exceed offloaded groups')
    if kv_length>c['max_position_embeddings']:raise ValueError('KV comparison length exceeds context')
    work=forward(model,Scenario(batch=batch,history=history,tokens=tokens,output_head='last'))
    ffn_parameters=3*c['hidden_size']*c['intermediate_size'];group_bytes=ffn_parameters*2
    removed=len(offloaded_layers)*group_bytes;buffer=buffer_slots*group_bytes;net=removed-buffer
    kv_request=4*c['num_hidden_layers']*c['num_key_value_heads']*c['head_dim']*kv_length
    copy_ns=Fraction(group_bytes*10**9,bandwidth_bytes_per_second)
    tasks=[];copies=[];previous_compute=None;previous_copy=None
    for iteration in range(passes):
        for layer in range(layers):
            compute_id=f'compute-{iteration}-{layer}';deps=[previous_compute] if previous_compute else []
            if layer in offloaded_layers:
                index=len(copies);copy_id=f'copy-{iteration}-{layer}'
                copy_deps=[previous_copy] if previous_copy else []
                if index>=buffer_slots:copy_deps.append(copies[index-buffer_slots]['consumer'])
                tasks.append(dict(id=copy_id,duration_ns=copy_ns,deps=copy_deps,resource='H2D'))
                copies.append(dict(id=copy_id,consumer=compute_id,pass_index=iteration,layer=layer,slot=index%buffer_slots))
                previous_copy=copy_id;deps.append(copy_id)
            tasks.append(dict(id=compute_id,duration_ns=layer_compute_ns,deps=deps,resource='GPU'))
            previous_compute=compute_id
    scheduled=schedule(tasks);by_id={t['id']:t for t in scheduled['tasks']};rows=[]
    for row in copies:
        cp=by_id[row['id']];consumer=by_id[row['consumer']]
        rows.append(dict(**row,bytes=group_bytes,copy_start_ns_exact=str(cp['start_ns']),copy_end_ns_exact=str(cp['end_ns']),
                         consume_start_ns_exact=str(consumer['start_ns']),consume_end_ns_exact=str(consumer['end_ns'])))
    baseline=passes*layers*layer_compute_ns;finish=scheduled['finish_ns'];traffic=passes*removed
    # Full layer compute duration is a conservative slot lifetime: the precise
    # last FFN-weight read within the layer is not known.
    return dict(schema_version=1,calculation='weight-offload',scenario=dict(model=model,offloaded_layers=offloaded_layers,
                buffer_slots=buffer_slots,passes=passes,batch=batch,tokens=tokens,history=history,kv_length=kv_length,
                bandwidth_bytes_per_second=bandwidth_bytes_per_second,layer_compute_ns=layer_compute_ns),sources=provenance(model),
                offload_copies=rows,offload_compute=[dict(id=t['id'],start_ns_exact=str(t['start_ns']),end_ns_exact=str(t['end_ns'])) for t in scheduled['tasks'] if t['resource']=='GPU'],
                summary=dict(ffn_parameters_per_layer=ffn_parameters,ffn_bytes_per_layer=group_bytes,
                             offloaded_unique_weight_bytes=removed,host_weight_bytes=removed,gpu_buffer_bytes=buffer,
                             net_gpu_weight_bytes_saved=net,equivalent_independent_kv_requests=net//kv_request,
                             kv_bytes_per_independent_request=kv_request,remaining_saved_bytes=net%kv_request,
                             per_forward_h2d_bytes=removed,total_h2d_bytes=traffic,
                             per_forward_copy_service_ns_exact=str(copy_ns*len(offloaded_layers)),
                             copy_service_per_input_token_ns_exact=str(copy_ns*len(offloaded_layers)/(batch*tokens)),
                             copy_only_decode_throughput_upper_tokens_per_s=float(Fraction(batch*10**9,1)/(copy_ns*len(offloaded_layers))) if tokens==1 else None,
                             baseline_compute_ns=baseline,scheduled_finish_ns_exact=str(finish),
                             exposed_wait_ns_exact=str(finish-baseline),
                             selected_ffn_matrix_flops_per_forward=2*batch*tokens*ffn_parameters*len(offloaded_layers),
                             target_matrix_flops_per_forward=work['summary']['matrix_flops']),
                assumptions=[
                    '官方Dense Qwen各层SwiGLU三矩阵BF16相同shape，显式选中层卸载FFN。默认36层每四层选最后一层共9份；主存保存全部卸载权重，GPU静态槽每槽可放一份。未执行真实引擎。',
                    '独立H2D串行资源与GPU逐层串行资源，所有主存权重从时刻0可读；复制按层／pass顺序尽早排队，消费者等待当前权重。槽从复制开始到消费层结束不可覆盖，同槽下次复制依赖上次消费者结束。',
                    '每次pass完整重新搬入选中权重，包含首次填充、跨pass环回及最后消费；即使最终槽内容碰巧可复用也不跳过复制。层时长为显式教学输入，不能从Async、UVA或预取名称推断这种重叠已实现。',
                    'layer_compute_ns计完整层且各层相同，包括其中未单列算术；copy带宽为有效单向教学速率，未套双向链路宣传峰值，未模拟H2D／GPU对主存和HBM的竞争。缓冲延迟释放到层末是保守约定。',
                    '容量净节省=卸载BF16权重-静态GPU槽，另比独立BF16 KV；未计pinning副本、页／图／工作区与其他模型权重。更多槽不改变每pass复制字节，会减少KV可用空间。',
                    'batch/tokens用于一次固定形状forward的矩阵工作与流量摊销；多个pass是重复该形状的执行调度，不是历史增长的完整生成请求。copy-only吞吐上限仅对decode(tokens=1)，不将每token摊销时间当单请求步延迟。',
                ])
