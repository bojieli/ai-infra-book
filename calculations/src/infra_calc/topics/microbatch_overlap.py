"""Two-microbatch FFN accounting with explicit paired concurrency cost."""
from ..models import qwen3
from ..sources import model_config,provenance
from ..units import positive_int
from .request_dag import schedule


def calculate(model='qwen3-8b',tokens=256,first_tokens=None,
              full_n_ns=400000,full_c_ns=800000,
              split_n_ns=None,split_c_ns=None,joint_window_ns=600000):
    split_n_ns=[200000,200000] if split_n_ns is None else split_n_ns
    split_c_ns=[480000,480000] if split_c_ns is None else split_c_ns
    first_tokens=tokens//2 if first_tokens is None else first_tokens
    for name,value in [('tokens',tokens),('first_tokens',first_tokens),('full_n_ns',full_n_ns),('full_c_ns',full_c_ns),('joint_window_ns',joint_window_ns)]:
        positive_int(value,name)
    if first_tokens>=tokens:raise ValueError('Both microbatches must be nonempty')
    for name,values in [('split_n_ns',split_n_ns),('split_c_ns',split_c_ns)]:
        if not isinstance(values,list) or len(values)!=2:raise ValueError(name+' must contain two durations')
        for value in values:positive_int(value,name)
    config=model_config(model);qwen3.validate(config)
    if tokens>config['max_position_embeddings']:raise ValueError('Tokens exceed pinned context')
    h,f=config['hidden_size'],config['intermediate_size']
    parameters=3*h*f;weight_bytes=2*parameters
    def task(name,duration,deps,resource):return dict(id=name,duration_ns=duration,deps=deps,resource=resource)
    full=[task('N',full_n_ns,[],'N'),task('C',full_c_ns,['N'],'C')]
    serial=[task('N0',split_n_ns[0],[],'N'),task('C0',split_c_ns[0],['N0'],'C'),
            task('N1',split_n_ns[1],['C0'],'N'),task('C1',split_c_ns[1],['N1'],'C')]
    ideal=[task('N0',split_n_ns[0],[],'N'),task('C0',split_c_ns[0],['N0'],'C'),
           task('N1',split_n_ns[1],['N0'],'N'),task('C1',split_c_ns[1],['C0','N1'],'C')]
    paired=[task('N0',split_n_ns[0],[],'N'),
            task('C0_and_N1',joint_window_ns,['N0'],'paired-window'),
            task('C1',split_c_ns[1],['C0_and_N1'],'C')]
    schedules={name:schedule(tasks) for name,tasks in [('full',full),('split_serial',serial),('split_ideal',ideal),('split_paired',paired)]}
    original=schedules['full']['finish_ns']
    threshold=original-split_n_ns[0]-split_c_ns[1]
    rows=[dict(tokens=m,matrix_flops=2*m*parameters,weight_read_once_bytes=weight_bytes) for m in (first_tokens,tokens-first_tokens)]
    return dict(schema_version=1,calculation='qwen-microbatch-overlap',model=model,
                scenario=dict(tokens=tokens,first_tokens=first_tokens,full_n_ns=full_n_ns,full_c_ns=full_c_ns,
                              split_n_ns=split_n_ns,split_c_ns=split_c_ns,joint_window_ns=joint_window_ns),
                sources=provenance(model),microbatch_rows=rows,request_schedules=schedules,
                summary=dict(ffn_parameters=parameters,unique_weight_bytes=weight_bytes,
                             matrix_flops=2*tokens*parameters,split_matrix_flops=sum(r['matrix_flops'] for r in rows),
                             full_weight_read_once_bytes=weight_bytes,split_cold_weight_read_bytes=2*weight_bytes,
                             split_compute_service_increase_ns=sum(split_c_ns)-full_c_ns,
                             full_finish_ns=original,split_serial_finish_ns=schedules['split_serial']['finish_ns'],
                             ideal_finish_ns=schedules['split_ideal']['finish_ns'],paired_finish_ns=schedules['split_paired']['finish_ns'],
                             joint_window_strict_upper_bound_ns=threshold,
                             positive_joint_window_can_win=threshold>0,
                             paired_beats_full=schedules['split_paired']['finish_ns']<original,
                             actual_gpu_seconds=None),
                assumptions=[
                    '官方Qwen Dense单层SwiGLU三矩阵参数3HF、矩阵工作2M*3HF，切两份数学工作守恒，允许不等长两份但时长须由输入另给。默认256行拆128/128。',
                    'BF16权重唯一容量288MiB；每份独立完整读一次、无跨微批缓存命中时逻辑读取576MiB，容量没有复制成576MiB。实际HBM须另查tile与缓存。',
                    'N为抽象访存或通信阶段、C为计算阶段，0.4/0.8ms与拆分0.2/0.48ms是独立教学计时，不由FFN FLOPs或权重字节推算成实测。N不一定等于本表权重读，不能用二者反推硬件带宽。',
                    '理想模式N与C分别串行但可跨资源重叠；成对模式将C0与N1从共同开始到两者均完成作为单一联合窗口，默认0.60ms是反例教学输入，不是NanoFlow实测。窗口内各自完成时刻未知，不造额外重叠。',
                    '最后C1须等待C0及N1，填充N0、联合窗口和排空C1均计入。小矩阵服务损失与联合争用分别输入；有限缓冲、提交、其它层及队列尚未加入。',
                    '联合窗口必须严格小于full_finish-N0-C1才比原batch快；阈值非正时任何正窗口都不能获益。该条件限定当前两份依赖结构，不直接推广任意多微批流水。',
                ])
