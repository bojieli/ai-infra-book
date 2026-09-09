"""Read-only CPython execution observer. Installed before SGLang import, also on spawn.
No tensor data reads, no extra cache-method calls, no branch replacement.
Line events are BEFORE the source line; return events carry the actual result.
"""
import atexit, hashlib, json, os, sys, threading, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent
_INSTALLED = False
_LOCK = threading.Lock()
_SEQ = 0
_FD = None
_PREFIX = hashlib.sha256((ROOT/'inputs.json').read_bytes()).hexdigest()
FIELDS = ('prefetch_tokens_occupied','prefetch_capacity_limit','prefetch_threshold','page_size','enable_storage','prefetch_stop_policy')
REQFIELDS = ('rid','host_hit_length','storage_hit_length','extend_input_len','cached_tokens','cached_tokens_device','cached_tokens_host','cached_tokens_storage','already_computed')
SCALARS = ('req_id','request_id','prefetch_length','matched_length','matched_len','completed_tokens','min_completed_tokens','loaded_from_storage','prefetch_done','can_terminate','completed','operation_terminated','storage_hit_count','host_hit_length','host_total','storage_portion','host_portion','device_portion','pre_len','new_cached','last_hash')
LENGTHS = ('prefetch_key','fetched_key','new_input_tokens','host_indices','hash_value','hash_values','token_ids_to_match')
TARGETS = {
 'managers/cache_controller.py': {'prefetch_rate_limited','prefetch','terminate_prefetch','_storage_hit_query','_page_transfer'},
 'mem_cache/hiradix_cache.py': {'prefetch_from_storage','check_prefetch_progress','can_terminate_prefetch','pop_prefetch_loaded_tokens','match_prefix'},
 'managers/schedule_batch.py': {'init_next_round_input','prepare_for_extend'},
 'managers/scheduler.py': {'_prefetch_kvcache'},
}
# Scheduler line events restricted to staging and prefill selection, not idle loop.
SCHED_RANGE = (2658,2701)

def scalar(x):
    return x if x is None or type(x) in (str,int,float,bool) else {'type':type(x).__name__}

def length(x):
    if x is None: return None
    try: return len(x)
    except TypeError: return None

def reqstate(req):
    d={k:scalar(getattr(req,k,None)) for k in REQFIELDS}
    d['prefix_indices_len']=length(getattr(req,'prefix_indices',None))
    d['output_ids_len']=length(getattr(req,'output_ids',None))
    return d

def operation(op):
    if op is None: return None
    return {'object_id':id(op),'request_id':getattr(op,'request_id',None),
      'completed_tokens':scalar(getattr(op,'completed_tokens',None)),
      'host_indices_len':length(getattr(op,'host_indices',None)),
      'hash_value':list(getattr(op,'hash_value',[]) or [])}

def emit(event, **data):
    global _SEQ
    with _LOCK:
        _SEQ += 1
        row=dict(event=event,monotonic_ns=time.monotonic_ns(),pid=os.getpid(),ppid=os.getppid(),tid=threading.get_ident(),seq=_SEQ,prefix_input_sha256=_PREFIX,**data)
        os.write(_FD,(json.dumps(row,separators=(',',':'))+'\n').encode())

def context(frame):
    f=frame
    for _ in range(18):
        if f is None: break
        loc=f.f_locals
        for k in ('req_id','request_id'):
            if isinstance(loc.get(k),str): return loc[k]
        for k in ('req','self'):
            obj=loc.get(k)
            if hasattr(obj,'rid'): return obj.rid
        op=loc.get('operation')
        if hasattr(op,'request_id'): return op.request_id
        params=loc.get('params')
        if hasattr(getattr(params,'req',None),'rid'): return params.req.rid
        f=f.f_back
    return None

def snapshot(frame):
    loc=frame.f_locals; obj=loc.get('self'); rid=context(frame)
    d={'request_id':rid,'locals':{k:scalar(loc[k]) for k in SCALARS if k in loc},'lengths':{k:length(loc[k]) for k in LENGTHS if k in loc}}
    cc=getattr(obj,'cache_controller',obj)
    d['controller']={k:scalar(getattr(cc,k)) for k in FIELDS if hasattr(cc,k)}
    for name in ('mem_pool_host','mem_pool_device'):
        if hasattr(cc,name): d['controller'][name+'_size']=scalar(getattr(getattr(cc,name),'size',None))
    if hasattr(obj,'ongoing_prefetch'):
        ongoing=obj.ongoing_prefetch
        d['ongoing_ids']=list(ongoing); d['ongoing_present']=rid in ongoing
        if rid in ongoing: d['ongoing_operation']=operation(ongoing[rid][3])
        d['loaded_by_req']=dict(obj.prefetch_loaded_tokens_by_reqid)
    if 'operation' in loc: d['operation']=operation(loc['operation'])
    req=loc.get('req',obj if hasattr(obj,'rid') else None)
    if req is not None: d['req']=reqstate(req)
    if hasattr(obj,'reqs'): d['batch_reqs']=[reqstate(r) for r in obj.reqs]
    if 'adder' in loc: d['can_run_ids']=[r.rid for r in loc['adder'].can_run_list]
    return d

def trace(frame,event,arg):
    filename=frame.f_code.co_filename
    rel=_PATHS.get(filename)
    if rel is None: return None
    name=frame.f_code.co_name; line=frame.f_lineno
    selected=name in TARGETS.get(rel,set())
    scheduler=rel=='managers/scheduler.py' and name=='get_new_batch_prefill'
    # Installed scheduler's actual method name is verified in install().
    scheduler=rel=='managers/scheduler.py' and name==_SCHED_METHOD
    if not selected and not scheduler: return None
    if scheduler and (event!='line' or not SCHED_RANGE[0]<=line<=SCHED_RANGE[1]): return trace
    if event in ('call','line','return','exception'):
        data=snapshot(frame)
        if event=='return':
            data['return']=scalar(arg)
            if name=='match_prefix': data['match_result']={'device_indices_len':length(getattr(arg,'device_indices',None)),'host_hit_length':scalar(getattr(arg,'host_hit_length',None))}
        if event=='exception': data['exception']={'type':arg[0].__name__,'message':str(arg[1])}
        emit('trace',phase=event,source=rel,method=name,line=line,**data)
    return trace

def install():
    global _INSTALLED,_FD,_PATHS,_SCHED_METHOD
    if _INSTALLED or not os.environ.get('BOOK_BRANCH_TRACE'): return
    import ast
    m=json.loads((ROOT/'source-manifest.json').read_text()); base=Path(m['installed_root'])
    _PATHS={str(base/p):p for p in m['sha256']}
    for rel,h in m['sha256'].items():
        assert hashlib.sha256((base/rel).read_bytes()).hexdigest()==h,rel
    tree=ast.parse((base/'managers/scheduler.py').read_text())
    _SCHED_METHOD=next(n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.lineno<=2679<=n.end_lineno)
    _FD=os.open(os.environ['BOOK_BRANCH_TRACE']+'.'+str(os.getpid())+'.jsonl',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
    _INSTALLED=True
    emit('installed',source_sha256=m['sha256'],observer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),proc_stat=Path('/proc/self/stat').read_text(),scheduler_method=_SCHED_METHOD)
    atexit.register(lambda:emit('observer_exit'))
    threading.settrace(trace);sys.settrace(trace)
