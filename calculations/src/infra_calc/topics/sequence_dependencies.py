"""C06: executable four-token/three-layer teaching recurrence and attention.

No checkpoint is claimed. All values are Python binary64; FLOPs use 2*m*n*k
rather than claiming an instruction trace. Different models are never compared
for equivalence. Inputs including the fifth token are supplied, not sampled.
"""
import math

D, F, L = 4, 8, 3
TOKENS = (0, 1, 2, 3)


def matrix(rows, cols, seed):
    return [[(((i+1)*17+(j+1)*11+seed*7)%19-9)/32 for j in range(cols)] for i in range(rows)]


def project(x, w):
    return [sum(x[i]*w[i][j] for i in range(len(x))) for j in range(len(w[0]))]


def embedding(token, position):
    # Fixed non-trained position signal; same input vectors in both teaching models.
    return [matrix(5,D,1)[token][j]+((position+1)*(j+1))/64 for j in range(D)]


def weights():
    return [dict(wx=matrix(D,D,2+7*l), wh=matrix(D,D,3+7*l),
                 q=matrix(D,D,4+7*l), k=matrix(D,D,5+7*l),
                 v=matrix(D,D,6+7*l), o=matrix(D,D,7+7*l),
                 up=matrix(D,F,8+7*l), down=matrix(F,D,9+7*l)) for l in range(L)]


def rnn_step(x, state, params):
    updated=[]
    for layer, w in enumerate(params):
        a,b=project(x,w['wx']),project(state[layer],w['wh'])
        x=[math.tanh(u+v) for u,v in zip(a,b)]
        updated.append(x)
    return x,updated


def attention(q, keys, values):
    scores=[sum(a*b for a,b in zip(q,k))/math.sqrt(D) for k in keys]
    shifted=[math.exp(s-max(scores)) for s in scores]
    total=sum(shifted); probs=[p/total for p in shifted]
    return [sum(p*v[j] for p,v in zip(probs,values)) for j in range(D)]


def transformer_layer(x, k, v, w):
    attended=project(attention(project(x,w['q']),k,v),w['o'])
    residual=[a+b for a,b in zip(x,attended)]
    ff=project([math.tanh(a) for a in project(residual,w['up'])],w['down'])
    return [a+b for a,b in zip(residual,ff)]


def transformer_full(tokens, params):
    xs=[embedding(t,i) for i,t in enumerate(tokens)]
    for w in params:
        keys=[project(x,w['k']) for x in xs]; values=[project(x,w['v']) for x in xs]
        xs=[transformer_layer(x,keys[:i+1],values[:i+1],w) for i,x in enumerate(xs)]
    return xs


def transformer_step(x, cache, params):
    for layer,w in enumerate(params):
        keys,values=cache[layer]
        keys.append(project(x,w['k'])); values.append(project(x,w['v']))
        x=transformer_layer(x,keys,values,w)
    return x,cache


def dependency_graph(model, tokens=4):
    nodes=[dict(id=f'l{l}t{t}',layer=l,token=t) for l in range(1,L+1) for t in range(tokens)]
    edges=[]
    for node in nodes:
        l,t=node['layer'],node['token']
        if model=='rnn':
            if l>1: edges.append(dict(source=f'l{l-1}t{t}',target=node['id'],kind='depth'))
            if t>0: edges.append(dict(source=f'l{l}t{t-1}',target=node['id'],kind='recurrent_state'))
        else:
            if l>1:
                for history in range(t+1):
                    edges.append(dict(source=f'l{l-1}t{history}',target=node['id'],
                                      kind='query_and_kv' if history==t else 'historical_kv'))
    depth={}
    for node in nodes:
        parents=[e['source'] for e in edges if e['target']==node['id']]
        depth[node['id']]=1+max((depth[p] for p in parents),default=0)
    return dict(nodes=nodes,edges=edges,unit_node_critical_path=max(depth.values()),
                timing_assumption='Each complete layer/token cell is one unit; input embeddings are ready at time zero. Not kernel latency.',
                input_edges='Each first-layer token cell also reads its input embedding; Transformer reads input embeddings at all causal positions.')


def transformer_cache_graph(tokens=4):
    nodes=[dict(id=f'input{t}',kind='supplied_embedding',token=t) for t in range(tokens)]
    edges=[]
    for l in range(1,L+1):
        for t in range(tokens):
            base=f'input{t}' if l==1 else f'l{l-1}t{t}'
            kv=f'kv{l}t{t}'; output=f'l{l}t{t}'
            nodes.extend([dict(id=kv,kind='new_kv_projection',layer=l,token=t),
                          dict(id=output,kind='query_attention_ff_output',layer=l,token=t)])
            edges.extend([dict(source=base,target=kv,kind='project_current_input'),
                          dict(source=base,target=output,kind='query_and_residual')])
            for history in range(t+1):
                edges.append(dict(source=f'kv{l}t{history}',target=output,
                                  kind='read_current_kv' if history==t else 'read_retained_kv'))
    return dict(nodes=nodes,edges=edges,
                execution_order='For state reuse: token ascending, then layer ascending; each KV projection executes once.',
                boundary='Explicit supplied inputs; no invented edge from a sampled token or vocabulary head.')


def matrix_rows(model, positions, invocation, cached):
    """positions are zero-based query positions; cached=False recomputes prefix."""
    rows=[]
    def add(layer,name,m,k,n,rhs):
        rows.append(dict(model=model,invocation=invocation,layer=layer,operation=name,
                         lhs_shape=[m,k],rhs_shape=[k,n],output_shape=[m,n],
                         flops=2*m*k*n,rhs_kind=rhs,
                         logical_lhs_bytes=8*m*k,logical_rhs_bytes=8*k*n,logical_output_bytes=8*m*n))
    for layer in range(L):
        if model=='rnn':
            for t in positions:
                add(layer,'input_projection_t'+str(t),1,D,D,'weight')
                add(layer,'state_projection_t'+str(t),1,D,D,'weight')
        else:
            count=len(positions)
            for name in ('q','k','v','o'): add(layer,name,count,D,D,'weight')
            add(layer,'ff_up',count,D,F,'weight'); add(layer,'ff_down',count,F,D,'weight')
            for t in positions:
                add(layer,'qk_t'+str(t),1,D,t+1,'activation')
                add(layer,'av_t'+str(t),1,t+1,D,'activation')
    return rows


def calculate():
    params=weights(); all_tokens=TOKENS+(4,)
    checks=[]
    rs=[[0.]*D for _ in range(L)]; cache=[([],[]) for _ in range(L)]
    for position,token in enumerate(all_tokens):
        rstream,rs=rnn_step(embedding(token,position),rs,params)
        ts,cache=transformer_step(embedding(token,position),cache,params)
        refstate=[[0.]*D for _ in range(L)]
        for i,t in enumerate(all_tokens[:position+1]):
            rfull,refstate=rnn_step(embedding(t,i),refstate,params)
        tfull=transformer_full(all_tokens[:position+1],params)[-1]
        for name,a,b in [('rnn',rfull,rstream),('transformer',tfull,ts)]:
            error=max(abs(x-y) for x,y in zip(a,b))
            checks.append(dict(model=name,prefix_tokens=position+1,recomputed_output=a,reused_output=b,
                               max_absolute_error=error,absolute_tolerance=1e-12,passed=error<=1e-12))
    matrices=[]; work=[]; states=[]
    for model in ('rnn','transformer'):
        cases=[('known_four_tokens',[list(range(4))],False),
               ('four_prefixes_recomputed',[list(range(n)) for n in range(1,5)],False),
               ('four_tokens_state_reused',[[t] for t in range(4)],True),
               ('fifth_token_prefix_recomputed',[list(range(5))],False),
               ('fifth_token_state_reused',[[4]],True)]
        for mode,queries,cached in cases:
            group=[]
            for call,positions in enumerate(queries):
                rows=matrix_rows(model,positions,call,cached)
                for row in rows: row['mode']=mode
                group.extend(rows)
            matrices.extend(group)
            work.append(dict(model=model,mode=mode,matrix_flops=sum(r['flops'] for r in group),
                             weight_matrix_flops=sum(r['flops'] for r in group if r['rhs_kind']=='weight'),
                             attention_matrix_flops=sum(r['flops'] for r in group if r['rhs_kind']=='activation')))
        for n in (1,2,3,4,5):
            elements=L*D if model=='rnn' else 2*L*n*D
            states.append(dict(model=model,after_tokens=n,persistent_history_elements=elements,
                               persistent_history_bytes=8*elements,
                               newly_written_state_bytes=8*L*D if model=='rnn' else 8*2*L*D,
                               capacity_growth_bytes=0 if model=='rnn' else 8*2*L*D,
                               next_token_prior_history_read_bytes=8*elements,
                               next_token_current_kv_attention_read_bytes=0 if model=='rnn' else 8*2*L*D))
    return dict(schema_version=1,calculation='sequence-dependencies',model='fixed-teaching-rnn-and-causal-transformer',
                scenario=dict(tokens=list(TOKENS),next_supplied_token=4,layers=L,width=D,ff_width=F,heads=1,dtype='fp64'),
                sources=[],sequence_matrices=matrices,sequence_work=work,sequence_states=states,
                sequence_checks=checks,sequence_graphs={m:dependency_graph(m) for m in ('rnn','transformer')},
                sequence_transformer_cache_graph=transformer_cache_graph(),
                teaching_weights=params,input_embeddings=[embedding(t,i) for i,t in enumerate(all_tokens)],
                summary=dict(all_same_model_cache_checks_pass=all(r['passed'] for r in checks),
                             max_absolute_error=max(r['max_absolute_error'] for r in checks),
                             rnn_weight_parameters=L*2*D*D,transformer_weight_parameters=L*(4*D*D+2*D*F),
                             shared_input_table_parameters=5*D,complete_runtime_peak_bytes=None,complete_runtime_seconds=None),
                assumptions=['Fixed pedagogical weights: ((17(i+1)+11(j+1)+7seed)%19-9)/32; distinct layer seeds, weights shared over time.',
                             'RNN is h=tanh(xWx+h_previousWh), zero initial states; no bias, gate, residual or output head.',
                             'Transformer is one-head scaled causal softmax attention, output projection and residual, tanh FFN and residual; no norm, bias, dropout or output head.',
                             'Four known tokens and supplied fifth token use fixed additive positional signals. No sampling, tokenizer, vocabulary logits or checkpoint claim.',
                             'Only outputs of the same model are compared. Prefix recomputation and cache/state reuse include the same entire three-layer model.',
                             'Python float is binary64; 2mnk is the declared matrix FLOPs convention. tanh/exp/sqrt, reductions outside GEMM, residuals and softmax are excluded from matrix totals.',
                             'Ragged attention rows count only valid causal pairs, not dense masked upper triangle execution. Logical operand bytes do not claim HBM transfers.',
                             'State bytes include persistent per-layer hidden vectors or K/V only, not weights, current temporary activations or allocator peak. Initial RNN zeros are retained capacity, not prior token history.',
                             'Graph unit-node critical path compares dependencies under equal cell costs; actual transformer attention cell work grows with position. Cached generation additionally requires each supplied next input.'])
