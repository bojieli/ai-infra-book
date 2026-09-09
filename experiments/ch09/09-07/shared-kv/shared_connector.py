"""Observe actual adapter submissions/completions, delegating native operations."""
import hashlib
import json
import os
import time
from pathlib import Path
from lmcache.integration.vllm.lmcache_mp_connector import LMCacheMPConnector
from lmcache.integration.vllm.vllm_multi_process_adapter import (
    LMCacheMPSchedulerAdapter, LMCacheMPWorkerAdapter)


def emit(kind, **values):
    path = Path(os.environ['SHARED_KV_TRACE']) / f'adapter-{os.getpid()}.jsonl'
    with path.open('a') as f:
        f.write(json.dumps(dict(kind=kind, pid=os.getpid(), time_s=time.monotonic(),
                               **values))+'\n')


class FutureObserver:
    def __init__(self, original, kind, request_id):
        self.original, self.kind, self.request_id = original, kind, request_id
        self.logged = False

    def __getattr__(self, name):
        return getattr(self.original, name)

    def result(self, *args, **kwargs):
        value = self.original.result(*args, **kwargs)
        if not self.logged:
            emit(self.kind+'_complete', request_id=self.request_id,
                 success=bool(value), result=repr(value))
            self.logged = True
        return value


def instrument():
    if getattr(LMCacheMPWorkerAdapter, '_book_observed', False):
        return
    LMCacheMPWorkerAdapter._book_observed = True
    for kind in ('store', 'retrieve'):
        original = getattr(LMCacheMPWorkerAdapter, f'submit_{kind}_request')
        def wrapped(self, request_id, op, event, cache_salt='', _fn=original, _kind=kind):
            begin = time.monotonic()
            result = _fn(self, request_id, op, event, cache_salt=cache_salt)
            futures = getattr(self, _kind+'_futures')
            submitted = request_id in futures
            emit(_kind+'_submit', request_id=request_id, start=op.start, end=op.end,
                 skip_first_n_tokens=op.skip_first_n_tokens,
                 token_ids_sha256=hashlib.sha256(json.dumps(op.token_ids).encode()).hexdigest(),
                 block_ids=op.block_ids, submitted=submitted,
                 begin_s=begin, healthy=self.is_healthy, instance_id=str(self.instance_id))
            if submitted:
                if _kind == 'store':
                    futures[request_id] = FutureObserver(futures[request_id], _kind, request_id)
                else:
                    future, blocks = futures[request_id]
                    futures[request_id] = (FutureObserver(future, _kind, request_id), blocks)
            return result
        setattr(LMCacheMPWorkerAdapter, f'submit_{kind}_request', wrapped)
    original_lookup = LMCacheMPSchedulerAdapter.check_lookup_result
    def lookup(self, request_id):
        result = original_lookup(self, request_id)
        if result is not None:
            emit('lookup', request_id=request_id, matched_tokens=result,
                 healthy=self.is_healthy)
        return result
    LMCacheMPSchedulerAdapter.check_lookup_result = lookup


instrument()


class ObservedMPConnector(LMCacheMPConnector):
    """Native connector, with adapter observations above."""
