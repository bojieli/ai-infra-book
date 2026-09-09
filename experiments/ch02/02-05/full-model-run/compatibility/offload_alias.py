"""Private SGLang OffloaderV1 correction-bias alias adaptation.

Install in every model-worker process before its first forward. No disk patch.
The caller must pin/audit SGLang sources separately. This is a modified runtime.
"""
from functools import wraps
import hashlib
import json
import os
from pathlib import Path

_first_bias_logged = False


def _record(kind, data):
    directory = os.environ.get('V4_FULL_COMPAT_LOG_DIR')
    if directory:
        out = Path(directory)
        out.mkdir(parents=True, exist_ok=True)
        path = out / f'{os.getpid()}-{kind}.json'
        with path.open('x') as f:
            json.dump(dict(pid=os.getpid(), kind=kind, **data), f, indent=2)


def adapt_functional_call(original):
    @wraps(original)
    def call(module, parameter_and_buffer_dicts, *args, **kwargs):
        global _first_bias_logged
        # V1 passes one state dictionary. Leave other calling conventions alone.
        if not isinstance(parameter_and_buffer_dicts, dict):
            return original(module, parameter_and_buffer_dicts, *args, **kwargs)
        state = parameter_and_buffer_dicts
        registered = {id(p): name for name, p in module.named_parameters()}
        changed = []
        try:
            for child in module.modules():
                # Restrict the patch to the precise SGLang TopK alias contract.
                cls = type(child)
                if cls.__name__ != 'TopK' or cls.__module__ != 'sglang.srt.layers.moe.topk':
                    continue
                config = child.topk_config
                old = config.correction_bias
                if old is None:
                    continue
                name = registered.get(id(old))
                if name is None or not name.endswith('gate.e_score_correction_bias'):
                    raise RuntimeError('TopK correction bias is not the expected registered gate parameter')
                if name not in state:
                    raise RuntimeError('Offloader state is missing the TopK gate correction bias')
                replacement = state[name]
                if replacement.shape != old.shape or replacement.dtype != old.dtype:
                    raise RuntimeError('Offloader bias shape/dtype changed')
                changed.append((config, old))
                config.correction_bias = replacement
                if not _first_bias_logged:
                    _record('first-bias', dict(key=name, shape=list(old.shape), dtype=str(old.dtype), old_device=str(old.device), replacement_device=str(replacement.device)))
                    _first_bias_logged = True
            return original(module, state, *args, **kwargs)
        finally:
            for config, old in reversed(changed):
                config.correction_bias = old
    call._v4_offload_bias_alias_adapter = True
    return call


def install():
    import sglang.srt.utils.offloader as offloader
    if getattr(offloader.functional_call, '_v4_offload_bias_alias_adapter', False):
        return False
    offloader.functional_call = adapt_functional_call(offloader.functional_call)
    _record('installed', dict(adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), offloader_path=offloader.__file__, offloader_sha256=hashlib.sha256(Path(offloader.__file__).read_bytes()).hexdigest(), patch_entry='sglang.srt.utils.offloader.functional_call'))
    return True
