"""Finite input slots for a real Qwen QK tile under declared service budgets.

Issue bandwidth, asynchronous completion latency, register staging and matrix
service are separate. No mapping to an actual instruction/SM is inferred.
"""
from pathlib import Path
import sys
import json
from fractions import Fraction
import argparse

PROJECT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(PROJECT/'src'))
from infra_calc.sources import model_config, provenance
from infra_calc.units import positive_int


def ticks(work, rate):
    """Declared discrete tick model, rounded up separately for each operation."""
    return (work + rate - 1) // rate


def schedule(load_ticks, matrix_ticks, latency_ticks, slots, register_ticks=0, synchronous=False):
    """Each input slot stays owned until the consuming GEMM chunk finishes."""
    if not load_ticks or len(load_ticks)!=len(matrix_ticks):
        raise ValueError('Equal nonempty chunk service lists required')
    for value in load_ticks+matrix_ticks:positive_int(value,'service ticks')
    positive_int(slots,'slots')
    positive_int(latency_ticks,'latency ticks',allow_zero=True)
    positive_int(register_ticks,'register ticks',allow_zero=True)
    if type(synchronous) is not bool:raise ValueError('synchronous must be bool')
    if not synchronous and register_ticks:raise ValueError('Direct async path has no register staging')
    rows=[]
    issue_free=compute_free=0
    for i,(load,compute) in enumerate(zip(load_ticks,matrix_ticks)):
        slot_free=rows[i-slots]['compute_end'] if i>=slots else 0
        issue=max(issue_free,slot_free,compute_free if synchronous else 0)
        transfer_end=issue+load
        ready=transfer_end+latency_ticks+register_ticks
        start=max(ready,compute_free)
        end=start+compute
        rows.append(dict(chunk=i,slot=i%slots,issue_start=issue,transfer_end=transfer_end,
                         data_ready=ready,compute_start=start,compute_end=end,
                         slot_released=end,slot_wait_ticks=max(0,slot_free-issue_free),
                         compute_idle_ticks=start-compute_free))
        issue_free=transfer_end
        compute_free=end
    return dict(chunks=rows,finish_tick=compute_free,
                total_compute_busy_ticks=sum(matrix_ticks),
                total_compute_idle_ticks=sum(r['compute_idle_ticks'] for r in rows))


def calculate(tile_m=128,tile_n=128,tile_k=32,latency_ticks=128,
              input_bytes_per_tick=256,matrix_flops_per_tick=8192,
              register_bytes_per_tick=256,capacity_bytes=65536):
    for name,value in locals().copy().items():
        positive_int(value,name,allow_zero=name=='latency_ticks')
    c=model_config('qwen3-8b');d=c['head_dim']
    if d%tile_k:raise ValueError('This exact chunk example requires tile_k dividing head_dim')
    if tile_m>c['max_position_embeddings'] or tile_n>c['max_position_embeddings']:
        raise ValueError('Q/K positions exceed official context range')
    count=d//tile_k
    slot_bytes=2*(tile_m+tile_n)*tile_k
    chunk_flops=2*tile_m*tile_n*tile_k
    load=ticks(slot_bytes,input_bytes_per_tick)
    compute=ticks(chunk_flops,matrix_flops_per_tick)
    # Register ingress and egress are distinct byte interfaces.
    reg=ticks(2*slot_bytes,register_bytes_per_tick)
    rows=[]
    for mode in ('synchronous-register-stage','asynchronous-direct-to-buffer'):
        for slots in (1,2,4,8):
            sync=mode.startswith('synchronous')
            timing=schedule([load]*count,[compute]*count,latency_ticks,slots,reg if sync else 0,sync)
            rows.append(dict(mode=mode,input_slots=slots,smem_reserved_bytes=slots*slot_bytes,
                             smem_capacity_passes=slots*slot_bytes<=capacity_bytes,
                             register_staging_reserved_bytes=slot_bytes if sync else 0,
                             accumulator_reserved_bytes=4*tile_m*tile_n,
                             register_interface_bytes=2*slot_bytes*count if sync else 0,
                             external_input_payload_bytes=slot_bytes*count,
                             timing=timing,
                             capacity_qualified_finish_tick=timing['finish_tick'] if slots*slot_bytes<=capacity_bytes else None))
    async_rows=[r for r in rows if r['mode'].startswith('asynchronous')]
    unlimited=schedule([load]*count,[compute]*count,latency_ticks,count)
    minimum=next((r['input_slots'] for r in async_rows if r['timing']['finish_tick']==unlimited['finish_tick']),None)
    feasible=[r for r in async_rows if r['smem_capacity_passes']]
    fastest=min((r['timing']['finish_tick'] for r in feasible),default=None)
    return dict(calculation='qwen-attention-input-pipeline',model='qwen3-8b',sources=provenance('qwen3-8b'),
                scenario=dict(tile_m=tile_m,tile_n=tile_n,tile_k=tile_k,latency_ticks=latency_ticks,
                              input_bytes_per_tick=input_bytes_per_tick,matrix_flops_per_tick=matrix_flops_per_tick,
                              register_bytes_per_tick=register_bytes_per_tick,capacity_bytes=capacity_bytes),
                shapes={'Q':[tile_m,d],'K_math':[d,tile_n],'scores':[tile_m,tile_n]},
                chunks=count,chunk_flops=chunk_flops,total_flops=count*chunk_flops,
                chunk_input_bytes=slot_bytes,rows=rows,
                no_slot_backpressure_finish_tick=unlimited['finish_tick'],
                smallest_enumerated_slots_matching_unlimited=minimum,
                fastest_capacity_qualified_async_tick=fastest,
                assumptions=['One rectangular QK GEMM split along real head_dim. Chunks accumulate serially into FP32 scores; no causal mask or instruction legality is inferred.',
                             'Tick is an abstract scheduling unit, not a GPU clock measurement. All rates/latencies are declared effective inputs. Each service duration rounds up separately.',
                             'Input issue consumes one bandwidth server for load_ticks; completion has additional latency and may overlap later issues. At most slots loads/consumers can own storage.',
                             'Slot is acquired at issue and released at compute end, with same-tick reuse. Input is not assumed copied into hidden extra buffers before compute finishes.',
                             'Synchronous mode serializes load, extra register ingress/egress service, and compute. Async removes that declared staging path; actual instructions/address/descriptor costs remain unmodeled.',
                             'SMEM input capacity, register staging and FP32 accumulator capacities are separate tiers. Only SMEM capacity is screened; passing it does not prove complete resource feasibility.',
                             'Time ends when final QK accumulator is ready. Output write, softmax/PV, launch, bank conflicts and synchronization overhead are not measured or set to zero.',
                             'No-slot reference allocates one slot per chunk. Reported saturation is finite-workload and enumerated-slot specific, not a universal minimum.'])


def scenarios():
    return {'base':calculate(), 'matrix-double':calculate(matrix_flops_per_tick=16384),
            'long-latency':calculate(latency_ticks=512),
            'tile-k16':calculate(tile_k=16), 'tile-k64':calculate(tile_k=64),
            'capacity-one-slot':calculate(capacity_bytes=16384)}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.write_text(json.dumps(scenarios(),indent=2)+'\n')
