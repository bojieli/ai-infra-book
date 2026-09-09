"""Explicit selected PyTorch fallback tensor operations, separate from HBM."""
def supplement(batch,tokens,history,counts,record_past=False):
    B,T,S=batch,tokens,history;M=B*T;H=4096;heads=64;k=v=128;channels=12288;C=64
    steps=[]
    def add(name,repeats=1,scalar=0,matrix=0,special=None,read=0,write=0,integer=0,notes=''):
        steps.append(dict(name=name,repeats=repeats,scalar_flops=scalar,matrix_flops=matrix,special_ops=special or {},tensor_input_bytes=read,tensor_output_bytes=write,integer_operations=integer,notes=notes))
    # Source executes the convolution before slicing away surplus positions.
    conv_update=S>0 and T==1 and not record_past
    L=(4+T if S else max(4,T)) if not record_past else (None if S else T)
    if L is not None:
        outputs=L-4+1 if conv_update else L+3
        kept=T if conv_update else L
        valid=sum(min(4,S+i+1) for i in range(T))
        extra=outputs*4-valid
        add('conv.additional_padded_and_discarded_products',45,matrix=2*B*channels*extra,read=2*B*channels*L,write=2*B*channels*outputs,notes='Dense convolution multiply-accumulate slots including zero-padding and outputs discarded by slices; FMA=2, not backend instruction count.')
        add('conv.extra_silu_before_final_crop',45,scalar=B*channels*(kept-T),special={'sigmoid':B*channels*(kept-T)},read=2*B*channels*kept,write=2*B*channels*kept)
        add('conv.cache_concat_or_initial_pad',45,read=2*B*channels*(L if S else T),write=2*B*channels*L,notes='Concat/pad interface; initial T>=4 has no copy in update_conv_state, so corrected below.')
        if not S and T>=4:steps[-1]['tensor_input_bytes']=steps[-1]['tensor_output_bytes']=0
        add('conv.cache_copy_last4',45,read=2*B*channels*4,write=2*B*channels*4)
        if not S:add('conv.cache_initial_zero',45,write=2*B*channels*4)
    else:outputs=kept=None
    recurrent=S>0 and T==1
    if not recurrent:
        chunks=(T+C-1)//C;G=B*heads*chunks;P=chunks*C;raw=M*heads;padded=B*heads*P
        # These supplement the existing Q/K norm and state/matrix operations.
        add('chunk.fp32_input_casts',45,read=2*raw*(2*k+v+1)+4*raw,write=4*raw*(2*k+v+2),notes='q/k/v/beta cast outputs; g is already FP32, transpose/contiguous alias behavior not equated to memory traffic.')
        add('chunk.pad_q_k_v_beta_g',45,read=4*raw*(2*k+v+2),write=4*padded*(2*k+v+2),notes='F.pad tensor interface even at zero padding; storage aliasing/backend copies not asserted.')
        add('chunk.beta_K_V',45*G,scalar=C*(k+v),read=4*C*(k+v+1),write=4*C*(k+v))
        add('chunk.cumsum',45*G,scalar=C-1,read=4*C,write=4*C,notes='Mathematical inclusive prefix-sum additions; parallel scan implementation may differ.')
        add('chunk.triu_mask_construction',45,integer=C*C,write=C*C,notes='One CxC mask per layer invocation, reused across all heads/chunks.')
        add('chunk.pairwise_decay_difference_mask_exp',45*G,scalar=C*C,special={'exp':C*C},read=8*C+C*C,write=12*C*C,notes='Broadcast diff, masked-fill and exp each write CxC; exp(-inf) slots included.')
        add('chunk.ut_and_intra_decay_multiply',45*G,scalar=2*C*C,read=16*C*C,write=8*C*C)
        add('chunk.exp_cum_for_decayed_Kbeta',45*G,scalar=C*k,special={'exp':C},read=4*C*(k+1),write=4*C*(k+1))
        add('chunk.exp_cum_for_Q',45*G,scalar=C*k,special={'exp':C},read=4*C*(k+1),write=4*C*(k+1))
        add('chunk.last_minus_cum_exp_for_K',45*G,scalar=C+C*k,special={'exp':C},read=4*(C*k+C+1),write=4*(C*k+2*C))
        add('chunk.exp_final_decay',45*G,special={'exp':1},read=4,write=4)
        add('chunk.unit_triangular_solver_interfaces',45*G,read=4*(2*C*C+C*(k+v)),write=4*C*(k+v),notes='Two linalg.solve_triangular calls. Mathematical solve arithmetic already in main operator ledger; solver workspace/algorithm not specified.')
        add('chunk.scan_vnew_subtract',45*G,read=8*C*v,write=4*C*v)
        add('chunk.scan_output_add',45*G,read=8*C*v,write=4*C*v)
        add('chunk.scan_state_decay_add',45*G,scalar=k*v,read=12*k*v+4,write=8*k*v,notes='Main ledger counted decay multiply; this adds omitted state-update addition and interfaces for both statements.')
        if not S:add('chunk.initial_state_zeros',45,write=4*B*heads*k*v)
        add('chunk.output_zeros_and_indexed_writes',45,write=8*B*heads*P*v,notes='zeros_like(new_values) plus per-chunk assignment; matrix/add outputs separately own their interfaces.')
        add('chunk.crop_and_output_cast',45,read=4*M*heads*v,write=2*M*heads*v)
    else:
        add('recurrent.fp32_casts',45,read=2*M*heads*(2*k+v+1)+4*M*heads,write=4*M*heads*(2*k+v+2))
        add('recurrent.decay_exp_interface',45,read=4*B*heads,write=4*B*heads)
        add('recurrent.decay_state_interface',45,read=4*B*heads*(k*v+1),write=4*B*heads*k*v)
        add('recurrent.K_state_products_and_reduce',45,read=4*B*heads*(k*v+k),write=4*B*heads*(k*v+v),notes='Eager product tensor then reduction; FMA convention in primary arithmetic ledger.')
        add('recurrent.delta_subtract_beta_multiply',45,read=4*B*heads*(4*v+1),write=8*B*heads*v)
        add('recurrent.outer_product_and_state_add',45,read=4*B*heads*(k+v+2*k*v),write=8*B*heads*k*v)
        add('recurrent.Q_state_products_and_reduce',45,read=4*B*heads*(k*v+k),write=4*B*heads*(k*v+v))
        add('recurrent.output_zero_assignment_cast',45,read=4*M*heads*v,write=10*M*heads*v)
    add('linear.cache_update_recurrent_copy',45,read=4*B*heads*k*v,write=4*B*heads*k*v)
    if not S:add('linear.cache_recurrent_initial_zero',45,write=4*B*heads*k*v)
    # Rotary invocation shared across all60 layers; source expands three axes
    # even for plain text. Config inverse-frequency buffer initialization is separate.
    half=32;axes=3
    add('rope.position_arange_and_history_add',integer=T,write=8*T,notes='Pure text default position_ids; views expanded to4 axes, three used by rotary.')
    add('rope.position_ids_fp32_cast',read=8*axes*M,write=4*axes*M)
    add('rope.frequency_outer_product',matrix=2*axes*M*half,read=4*(axes*B*half+axes*M),write=4*axes*M*half)
    add('rope.sin_cos_and_scaling',scalar=2*axes*M*half,special={'sin':axes*M*half,'cos':axes*M*half},read=8*axes*M*half,write=16*axes*M*half,notes='Source multiplies both sin and cos by attention_scaling=1.')
    add('rope.recompose_and_duplicate',read=8*M*(21+64),write=8*M*(21+64),notes='Two axis slices per sin/cos:11+10 values; concat duplicates32 frequencies to64.')
    add('rope.cast_BF16',read=8*M*64,write=4*M*64)
    add('rope.rotate_half_negation',15,scalar=M*(32+2)*32,read=2*M*(32+2)*32,write=2*M*(32+2)*32)
    add('rope.concat_rotated_and_passthrough',15,read=2*M*(32+2)*256,write=2*M*(32+2)*256)
    # Select the eager reference explicitly: full rectangular QK/PV, then mask.
    rect=B*T*(S+T);valid=B*(T*S+T*(T+1)//2);delta=rect-valid
    add('full.eager_masked_matrix_slots',15,matrix=4*32*256*delta)
    add('full.eager_additional_softmax_and_mask',15,scalar=4*32*delta+32*rect,special={'exp':32*delta,'max_comparisons':32*delta},notes='Additional rectangular softmax positions plus attention-mask addition to every score slot.')
    add('full.kv_cache_concat',15,read=2*2*B*(S+T)*2*256 if S else 0,write=2*2*B*(S+T)*2*256 if S else 0,notes='Dynamic cache concatenates old/new K and V; empty initial cache can alias incoming tensors.')
    add('full.repeat_kv_logical_materialization',15,read=2*2*B*(S+T)*2*256,write=2*2*B*(S+T)*32*256,notes='repeat_kv expand/reshape logical output shape; physical alias/fusion not asserted.')
    add('full.QK_interfaces',15,read=2*(M*32*256+B*(S+T)*32*256),write=2*32*rect)
    add('full.scale_mask_softmax_cast_interfaces',15,read=2*32*rect*3+4*32*rect,write=2*32*rect*3+4*32*rect,notes='Scale, mask add, FP32 softmax result, BF16 cast outputs; softmax internal reduction buffers are backend-dependent.')
    add('full.PV_interfaces',15,read=2*(32*rect+B*(S+T)*32*256),write=2*M*32*256)
    add('full.transpose_contiguous',15,read=2*M*32*256,write=2*M*32*256)
    # Router backend topk remains a primitive with declared input/output shape;
    # no guessed comparison count for the algorithm selected by torch.
    E=512;top=10;A=M*top;hit=sum(n>0 for n in counts)
    add('router.topk_primitive_interfaces',60,read=4*M*E,write=M*top*(4+8),notes='Exact data types/shapes, implementation comparison schedule unspecified.')
    add('router.probability_cast_and_selected_renorm',60,read=4*M*E+4*M*top,write=2*M*top,notes='Softmax FP32 allocation represented by full probability tensor; arithmetic counted in main router operator.')
    add('router.one_hot_initialize_scatter',60,integer=A,read=8*A,write=8*A*E+8*A,notes='int64 one_hot logical zero initialization plus one selected entry per assignment.')
    add('router.expert_hit_reduce_compare_nonzero',60,integer=E*(A-1)+E,read=8*A*E,write=8*E+E+8*hit,notes='Integer reduction, >0 and nonzero output; primitive scan scheduling unspecified.')
    add('router.where_per_active_expert',60,integer=hit*top*M,read=8*hit*top*M,write=16*A)
    add('router.input_gather',60,read=8*A+2*A*H,write=2*A*H)
    add('router.probability_gather',60,read=16*A+2*A,write=2*A)
    add('router.destination_zero_fill',60,write=2*M*H)
    add('router.index_add_destination_interfaces',60,read=8*A+4*A*H,write=2*A*H,notes='Logical source + destination per assignment, no deduplication/HBM inference.')
    return dict(steps=steps,conv=dict(input_positions=L,conv_output_positions_before_slice=outputs,silu_positions_before_final_crop=kept,source_path='update' if conv_update else 'padded_fn',record_past_shape_known=L is not None),
        scalar_additions=sum(x['scalar_flops']*x['repeats'] for x in steps),matrix_additions=sum(x['matrix_flops']*x['repeats'] for x in steps),
        tensor_interface_read_bytes=sum(x['tensor_input_bytes']*x['repeats'] for x in steps),tensor_interface_write_bytes=sum(x['tensor_output_bytes']*x['repeats'] for x in steps),
        scope='Additional source-operation interfaces; not an exhaustive whole-model interface sum or measured HBM. Matmul FMA=2 and reductions mathematical counts; torch primitive backend algorithms remain unspecified.',
        startup=dict(rope_inv_freq_elements=32,scalar_divisions=64,special_ops={'power':32},note='Model construction only; not repeated each forward.'))
