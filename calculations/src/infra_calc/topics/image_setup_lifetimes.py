"""Declared eager temporary lifetimes for the pinned sinusoidal timestep helper.

Only get_timestep_embedding and its immediate output dtype conversion are added
here. Views alias their base; same-dtype .float()/.to() are aliases. The graph is
an explicit reference evaluation order, not an allocator trace or device peak.
"""


def timestep_temporary_events(batch, dtype):
    """Events relative to one helper call; its supplied input is caller-owned.

    Python keeps the named exponent until helper return, and the caller keeps
    timesteps_proj through the learned embedding call. Out-of-place assignments
    allocate their RHS before releasing the prior binding. No compiler fusion or
    storage reuse is assumed. Projector internals are deliberately outside scope.
    """
    if isinstance(batch, bool) or not isinstance(batch, int) or batch < 1:
        raise ValueError('Batch must be a positive integer')
    if dtype not in ('bf16', 'fp16', 'fp32'):
        raise ValueError('Unsupported timestep input dtype')
    events = []
    def emit(action, name, elements=0, element_bytes=4):
        row = dict(action=action, object='setup_timestep_'+name, bytes=elements*element_bytes)
        if action == 'allocate':
            row['dtype'] = 'fp32' if element_bytes == 4 else dtype
        events.append(row)
    def alloc(name, elements, element_bytes=4): emit('allocate', name, elements, element_bytes)
    def free(name): emit('release', name)
    n = batch*128
    alloc('arange',128)
    alloc('exponent_multiply',128); free('arange')
    alloc('exponent',128); free('exponent_multiply')
    alloc('exp_frequency',128)
    if dtype != 'fp32': alloc('input_upcast',batch)
    alloc('outer',n)
    if dtype != 'fp32': free('input_upcast')
    free('exp_frequency')
    alloc('scaled',n); free('outer')
    alloc('sin',n); alloc('cos',n)
    alloc('concat',2*n)
    free('sin'); free('cos'); free('scaled')
    alloc('flipped',2*n); free('concat')
    free('exponent')  # helper returns; flipped remains owned by timesteps_proj
    if dtype != 'fp32': alloc('model_features',2*n,2)
    # The immediate caller uses these features in its learned projector. Its
    # matrices/activations are not setup tensors and are not invented here.
    if dtype != 'fp32': free('model_features')
    free('flipped')
    return events


def setup_boundary_graph(result, baseline):
    """Replay baseline exactly once, injecting helper events before predictions.

    The conditional prediction already exists during the negative helper call,
    so CFG overlap follows the existing graph. Setup temporaries all die before
    the corresponding prediction boundary; no latent/prediction/scheduler buffer
    is duplicated. The old baseline is kept by the caller for direct comparison.
    """
    events, live = [], {}
    peak = 0
    baseline_peak = max((row['live_bytes_after'] for row in baseline),default=0)
    helper = timestep_temporary_events(result['scenario']['batch'],result['scenario']['dtype'])
    helper_peak = 0; helper_live = {}
    for row in helper:
        if row['action']=='allocate': helper_live[row['object']]=row['bytes']
        else: helper_live.pop(row['object'])
        helper_peak=max(helper_peak,sum(helper_live.values()))
    def append(row, phase, scope):
        nonlocal peak
        row=dict(row)
        if row['action']=='allocate':
            if row['object'] in live: raise ValueError('Duplicate setup graph allocation')
            live[row['object']]=row['bytes']
        else:
            row['bytes']=live.pop(row['object'])
        size=sum(live.values()); peak=max(peak,size)
        row.update(event=len(events),phase=phase,scope=scope,live_bytes_after=size,live_objects=list(live))
        events.append(row)
    inserted = 0
    for row in baseline:
        if (row['action']=='allocate' and row['object'] in ('prediction','negative_prediction')
                and row['phase'].endswith(('_conditional','_negative'))):
            for item in helper: append(item,row['phase']+'_timestep_setup','timestep_helper')
            inserted+=1
        append(row,row['phase'],'original_boundary')
    if inserted != result['summary']['transformer_invocations']:
        raise ValueError('Timestep helper invocation count disagrees with denoising graph')
    return dict(events=events,helper_invocations=inserted,
                helper_peak_bytes=helper_peak,declared_expanded_graph_peak_bytes=peak,
                original_boundary_graph_peak_bytes=baseline_peak,
                peak_increment_bytes=peak-baseline_peak,
                final_live_bytes=sum(live.values()),final_live_objects=list(live),
                actual_allocator_peak_bytes=None,
                scope='Original boundary graph plus pinned sinusoidal timestep helper and immediate output cast only',
                remaining=['caller-owned timestep inputs and scheduler arrays',
                           'text and DiT rotary-frequency construction lifetimes and persistent tables',
                           'learned timestep projector activations and all other block internals',
                           'actual backend fusion, storage reuse, allocator and device placement'])
