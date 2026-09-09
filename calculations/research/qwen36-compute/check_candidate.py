from pathlib import Path
import sys, importlib.util, types, json
base=Path(__file__).resolve().parent
sys.path.insert(0,str(base.parents[1]/'src'))
from infra_calc.topics import qwen35_forward as old
pkg=types.ModuleType('infra_calc.candidate')
pkg.__path__=[str(base)]
sys.modules[pkg.__name__]=pkg
from infra_calc.candidate import qwen35_forward as new
from infra_calc.candidate.qwen35_reference_steps import supplement
cases=[{},dict(tokens=1),dict(tokens=65),dict(tokens=3,history=8),dict(tokens=1,history=8192),dict(batch=2,tokens=1,history=8192,output_head='last'),dict(tokens=1,record_past=True),dict(tokens=1,history=8,record_past=True)]
for kwargs in cases:
    a,b=old.calculate(**kwargs),new.calculate(**kwargs)
    # Known legacy dt_bias bug corrected: BF16 parameter was charged as FP32.
    assert a["summary"]["weight_read_bytes"] - b["summary"]["weight_read_bytes"] == 45 * 2 * 64
    assert a["reference_execution_steps"]["tensor_interface_read_bytes"] - b["reference_execution_steps"]["tensor_interface_read_bytes"] == 45 * 2 * 64
    for op in a["operators"]:
        if op["name"] == "linear.decay_and_beta":
            op["weight_read_bytes"] -= 2 * 64
            op["notes"] = next(x for x in b["operators"] if x["name"] == op["name"])["notes"]
    a["summary"]["weight_read_bytes"] -= 45 * 2 * 64
    for step in a["reference_execution_steps"]["steps"]:
        if step["name"] == "linear.a_dt_softplus_decay_multiply":
            step["tensor_input_bytes"] -= 2 * 64
    a["reference_execution_steps"]["tensor_interface_read_bytes"] -= 45 * 2 * 64
    # Public summary duplicates the statement-interface read total.
    for key in a["summary"]:
        if a["summary"][key] != b["summary"][key]:
            assert a["summary"][key] - b["summary"][key] == 5760, key
            a["summary"][key] = b["summary"][key]
    a["assumptions"] = b["assumptions"]
    assert a==b, [k for k in a if a[k]!=b[k]]
print('397B full result equality except verified dt_bias correction:',len(cases),'scenarios')
t=json.loads((base.parent/'qwen36-inputs/model/config.json').read_text())['text_config']
for T,S in [(1,0),(65,0),(1,8192),(3,8)]:
    M=2*T
    counts=[M*8//256+(i<M*8%256) for i in range(256)]
    r=supplement(2,T,S,counts,text_config=t)
    steps={x['name']:x for x in r['steps']}
    assert steps['norm.full_Q.input_fp32_cast']['tensor_input_bytes']==2*M*16*256
    assert steps['norm.linear_gated.input_fp32_cast']['tensor_input_bytes']==2*M*32*128
    assert steps['full.eager_masked_matrix_slots']['matrix_flops']==4*16*256*(2*T*(S+T)-2*(T*S+T*(T+1)//2))
    assert steps['linear.cache_update_recurrent_copy']['repeats']==30
    assert steps['router.logits_cast_softmax']['repeats']==40
    assert steps['router.logits_cast_softmax']['tensor_input_bytes']==6*M*256
    assert steps['moe.routed_silu_and_up_multiply']['tensor_input_bytes']==6*M*8*512
print('35B independent reference dimension checks: 4 scenarios')
for kwargs in cases:
    result=new.calculate(**kwargs, model='qwen3.6-35b-a3b', evidence_root='sources/qwen3.6-35b-a3b', mask_source='sources/qwen3.6-35b-a3b/transformers/src/transformers/masking_utils.py')
    assert result['summary']['base_text_parameters']==34660610688
    assert result['summary']['base_checkpoint_bytes']==69321221376
    assert len(result['weights'])==693
    ops={r['name']:r for r in result['operators']}
    B=kwargs.get('batch',1);T=kwargs.get('tokens',8192);S=kwargs.get('history',0);M=B*T
    assert ops['full.q_and_gate']['matrix_flops']==2*M*2048*8192
    assert ops['full.q_and_gate']['repeats']==10
    assert ops['linear.qkv']['matrix_flops']==2*M*2048*8192
    assert ops['linear.qkv']['repeats']==30
    assert ops['linear.decay_and_beta']['weight_read_bytes']==128
    assert result['state']['linear_recurrent_fp32_bytes']==30*B*32*128*128*4
    assert result['state']['full_kv_after_bytes']==10*B*(S+T)*2*2*256*2
    steps={r['name']:r for r in result['reference_execution_steps']['steps']}
    assert steps['linear.A_fp32_cast']['tensor_input_bytes']==64
    assert steps['linear.A_fp32_cast']['tensor_output_bytes']==128
print('35B full calculate with verified public sources:',len(cases),'scenarios')
