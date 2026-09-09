"""Static PTX sites from an archived SGLang probe; not official TileLang lowering."""
from pathlib import Path
from collections import Counter
import json,hashlib,re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CACHE=ROOT/'experiments/ch02/02-05/native-layer-probe/attempt-05/cache/triton/3QDR6VYV2MANJNREUAVCDMBGTFTWLNLNFX6PPICSWTKX73PFPNQQ'


def analyze():
    files=[CACHE/(f'_w8a8_block_fp8_matmul.{ext}') for ext in ('ptx','json','cubin')]
    ptx=files[0].read_text();meta=json.loads(files[1].read_text())
    if meta['name']!='_w8a8_block_fp8_matmul' or meta['target']['arch']!=120:
        raise ValueError('Unexpected archived compiled kernel identity')
    sites=[]
    # Archive uses one executable PTX statement per physical line. Fail instead
    # of silently ignoring a multi-line or multiple-instruction representation.
    for line_number,line in enumerate(ptx.splitlines(),1):
        code=line.split('//',1)[0].strip()
        if not code or code.startswith(('.', '$')) or code in ('{','}',')'):
            continue
        if ';' not in code:
            raise ValueError(f'Unsupported executable syntax at line {line_number}: {code}')
        if code.count(';')!=1 or not code.endswith(';'):
            raise ValueError('Multiple statements require a real PTX parser')
        match=re.fullmatch(r'(?:(@!?%\w+)\s+)?([a-z][a-z0-9_.]*)\s*(.*);',code)
        if not match:raise ValueError(f'Unsupported statement: {code}')
        predicate,opcode,operands=match.groups()
        sites.append(dict(line=line_number,predicate=predicate,opcode=opcode,operands=operands))
    histogram=Counter(s['opcode'] for s in sites)
    def selected(prefix):return [s for s in sites if s['opcode'].startswith(prefix)]
    virtual_registers={kind:int(count) for kind,count in re.findall(r'\.reg\s+\.(\w+)\s+%\w+<(\d+)>;',ptx)}
    return dict(scope='one archived SGLang SM120 FP8 GEMM compilation; static PTX text sites only',
                sources=[dict(file=str(f.relative_to(ROOT)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in files],
                identity=dict(entry=meta['name'],target=meta['target'],triton_version=meta['triton_version'],
                              ptx_target=re.search(r'\.target\s+(\S+)',ptx).group(1),
                              thread_block_threads=int(re.search(r'\.reqntid\s+(\d+)',ptx).group(1))),
                compiled_metadata=dict(shared_bytes=meta['shared'],num_warps=meta['num_warps'],num_stages=meta['num_stages'],
                                       tmem_size=meta['tmem_size'],tensordesc_meta=meta['tensordesc_meta']),
                virtual_ptx_register_declarations=virtual_registers,
                static_instruction_sites=len(sites),opcode_histogram=dict(sorted(histogram.items())),
                predicated_static_sites=sum(s['predicate'] is not None for s in sites),
                async_copy_sites=selected('cp.async'),matrix_load_sites=selected('ldmatrix'),
                tensor_map_sites=selected('tensormap'),bulk_tensor_sites=selected('cp.async.bulk.tensor'),
                instructions=sites,
                dynamic_instruction_count=None,hardware_registers_per_thread=None,measured_hbm_bytes=None,
                matches_official_tilelang_kernel=False,
                limitations=['This cache belongs to the archived four-layer truncated SGLang runtime probe; no per-kernel launch trace or argument binding is inferred from compilation cache presence.',
                             'Official TileLang source has M32 tiles and its own dispatch. This Triton backend must not fill its missing instruction counts.',
                             'PTX instruction text sites are not dynamic counts: loops, predicates, warp execution and compiler SASS lowering can change executed work.',
                             'PTX virtual register declarations are not allocated hardware registers. num_stages is compiler metadata, not a verified count of physical input buffers.',
                             'An empty tensor-map list and absence of a PTX opcode are scoped to this exact artifact, not device capability.',
                             'cp.async copy sizes and predicate/source-size operands do not directly establish physical HBM transactions or transferred bytes.'])

if __name__=='__main__':
    r=analyze();(HERE/'result.json').write_text(json.dumps(r,indent=2)+'\n')
    print({k:r[k] for k in ['identity','compiled_metadata','static_instruction_sites','virtual_ptx_register_declarations']})
