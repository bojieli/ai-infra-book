"""Pinned public DeepSeek R1 Distill Llama70B analytical forward adapter.

Integrate as infra_calc.models.llama70. No tensors/weights are allocated.
"""
from collections import Counter
from dataclasses import asdict
from math import pi
from pathlib import Path
import hashlib
from infra_calc.paths import PROJECT
from infra_calc import schema
from infra_calc.models import qwen3
from infra_calc.schema import Operator, Scenario, Weight
from infra_calc.sources import model_config, provenance, read_source
from infra_calc.units import positive_int

MODEL = 'deepseek-r1-distill-llama-70b'


def validate(config):
    if config.get('model_type') != 'llama':
        raise ValueError('Expected Llama decoder config')
    for key in ('hidden_size','intermediate_size','num_hidden_layers','num_attention_heads',
                'num_key_value_heads','head_dim','vocab_size','max_position_embeddings'):
        positive_int(config[key], key)
    if config['hidden_size'] != config['num_attention_heads'] * config['head_dim']:
        raise ValueError('This adapter requires hidden_size = Q heads * head_dim')
    if config['num_attention_heads'] % config['num_key_value_heads'] or config['head_dim'] % 2:
        raise ValueError('Invalid GQA/rotary dimensions')
    if (config.get('attention_bias') or config.get('mlp_bias') or config.get('attention_dropout',0)
            or config.get('pretraining_tp',1) != 1 or config.get('partial_rotary_factor',1) != 1):
        raise ValueError('Only bias-free full rotary dropout-free TP1 reference supported')
    if config.get('hidden_act') != 'silu' or config.get('tie_word_embeddings'):
        raise ValueError('Expected untied head and SwiGLU')
    r=config['rope_scaling']
    if r.get('rope_type') != 'llama3' or not (r['factor'] > 0 and r['high_freq_factor'] > r['low_freq_factor'] > 0):
        raise ValueError('Expected valid llama3 scaled RoPE')
    positive_int(r['original_max_position_embeddings'],'original_max_position_embeddings')
    if config['rope_theta'] <= 0:
        raise ValueError('rope_theta must be positive')


def weights(config):
    validate(config)
    # Reuse names/shapes only; Qwen-specific q_norm/k_norm are explicitly absent.
    rows=[w for w in qwen3.base_weights(config) if '.q_norm.' not in w.name and '.k_norm.' not in w.name]
    h,f,l=config['hidden_size'],config['intermediate_size'],config['num_hidden_layers']
    return rows+[Weight('model.layers.{layer}.mlp.'+name+'.weight',shape,l)
                 for name,shape in [('gate_proj',(f,h)),('up_proj',(f,h)),('down_proj',(h,f))]]


def rope_initialization(config):
    """One model construction, not repeated per layer/token/decode step."""
    validate(config);n=config['head_dim']//2;r=config['rope_scaling'];base=config['rope_theta']
    original=[1/(base**(2*i/config['head_dim'])) for i in range(n)]
    lo=r['original_max_position_embeddings']/r['low_freq_factor'];hi=r['original_max_position_embeddings']/r['high_freq_factor']
    freq=[];regions=Counter()
    for inv in original:
        wavelength=2*pi/inv
        if wavelength < hi: regions['unchanged_high_frequency']+=1;v=inv
        elif wavelength > lo: regions['scaled_low_frequency']+=1;v=inv/r['factor']
        else:
            regions['interpolated_medium_frequency']+=1
            smooth=(r['original_max_position_embeddings']/wavelength-r['low_freq_factor'])/(r['high_freq_factor']-r['low_freq_factor'])
            v=(1-smooth)*inv/r['factor']+smooth*inv
        freq.append(v)
    return {'frequency_count':n,'inverse_frequencies':freq,'frequency_regions':dict(regions),
            'operator':Operator('llama3_inv_freq_initialization','initialization',{'inv_freq':[n]},
                scalar_flops=12*n+4,
                special_ops={'pow':n,'compare':3*n,'logical_not':2*n,'logical_and':n,'where_select':2*n,'iota_elements':n,'cast_elements':n},
                activation_write_bytes=4*n,
                notes='Fixed source eager arithmetic: default exponent division+reciprocal2n; wavelength n; scaled branch n; smooth3n; blend5n; two thresholds+high-low+2*pi4. torch.where evaluates full vectors in both branches. Intermediates are not assumed HBM. Original_inv_freq aliases same buffer; initialization excluded from forward totals.').record(),
            'resident_buffer_bytes':4*n,'attention_scaling':1.0,
            'boundary':'Llama3 scaling uses fixed original context and does not recompute by sequence length; not dynamic NTK or YaRN.'}


def build_operators(config, scenario):
    validate(config)
    for field in ('weight_bytes','activation_bytes','kv_bytes','score_bytes'):
        if getattr(scenario,field) not in (1,2,4,8):raise ValueError('Supported byte widths are1,2,4,8')
    # Shared accounting primitives implement GQA/SwiGLU; remove both Qwen head norms.
    ops=[op for op in qwen3.build_operators(config,scenario) if op.name not in ('q_norm','k_norm')]
    b,p,d=1,scenario.tokens,config['head_dim'];a=scenario.activation_bytes
    # Fixed default forward constructs position_ids=cache_position.unsqueeze(0), batch1.
    for i,op in enumerate(ops):
        if op.name=='rope_table':
            ops[i]=Operator('llama3_rope_table','position',{'frequencies':[b,p,d//2],'cos_sin_each':[b,p,d]},
                scalar_flops=b*p*d//2+2*b*p*d,
                special_ops={'sin':b*p*d,'cos':b*p*d,'cast_position_elements':b*p,'cast_cos_sin_elements':2*b*p*d if a!=4 else 0,'concat_copy_elements':b*p*d},
                activation_read_bytes=4*(d//2)+8*b*p,
                activation_write_bytes=2*b*p*d*a,
                notes='Default position_ids has leading size1 and broadcasts across requests; inv_freq @ positions has reduction width1 so one multiply per frequency. Frequency cat duplicates values; sin/cos and scaling-by1 both retained. One table per forward, shared across80 layers; FP32 intermediates on-chip boundary.')
        elif op.name=='apply_rope':
            op.activation_read_bytes= scenario.rows*(config['num_attention_heads']+config['num_key_value_heads'])*d*a+2*b*p*d*a
            op.notes+=' Llama has no Q/K norm; shared default position table counted once per layer.'
        elif op.category=='normalization':
            op.special_ops['cast_elements']=2*op.shapes['input'][0]*op.shapes['input'][1] if a!=4 else 0
    return ops


def calculate_from_inputs(config,scenario,sources):
    validate(config)
    if not sources:raise ValueError('Pinned input provenance is required')
    ops=build_operators(config,scenario);ws=weights(config);l=config['num_hidden_layers'];d=config['head_dim'];kv=config['num_key_value_heads']*d
    param=sum(w.parameters for w in ws);s=scenario;special=Counter()
    for op in ops:special.update({k:v*op.repeats for k,v in op.special_ops.items()})
    total=lambda field:sum(getattr(op,field)*op.repeats for op in ops)
    pertoken=2*l*kv*s.kv_bytes;scores=config['num_attention_heads']*s.rectangular_pairs*s.score_bytes
    return {'schema_version':1,'calculation':'llama70-dense-forward','model':MODEL,'scenario':asdict(s),
        'sources':sources,'input_hashes':{x['file']:x['sha256'] for x in sources},
        'implementation_hashes':{str(Path(path).resolve().relative_to(PROJECT)):hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in (__file__,qwen3.__file__,schema.__file__)},
        'dimensions':{k:config[k] for k in ('num_hidden_layers','hidden_size','intermediate_size','num_attention_heads','num_key_value_heads','head_dim','vocab_size','tie_word_embeddings')},
        'initialization':rope_initialization(config),'weights':[w.record(s.weight_bytes) for w in ws],
        'operators':[op.record() for op in ops],
        'assumptions':['Public DeepSeek-R1-Distill-Llama-70B; not renamed gated Llama3.1 checkpoint.',
            'Bias-free Llama GQA/SwiGLU forward; no Q/K normalization. Logits last/all/none explicit; tokenizer, sampling and CPU preprocessing outside scope.',
            'Equal-length batch, default position_ids=cache_position.unsqueeze(0); one contiguous position table history..history+tokens-1 shared across batch and layers. Explicit per-request position IDs are outside this adapter.',
            'Matrix work uses valid causal pairs; rectangular unfused attention work and FP32 score materialization reported separately. These are analytical operand loads, not a literal eager trace or measured HBM.',
            'Norm casts, RoPE casts, nonlinear functions and mask decisions listed separately; scalar intermediates are on-chip. Views/GQA repeat need not materialize.',
            'KV append assumes paged/in-place writes; old-cache torch.cat copies, allocator/kernel-launch overhead and backend workspace excluded.',
            'Weight/activation/KV byte widths are explicit scenario sensitivity, not proof of checkpoint quantization. Index confirms names only; no tensor headers or weights downloaded.',
            'Llama3 inverse-frequency initialization is separate from each forward; scaling-by1 remains in reference per-forward arithmetic. No latency prediction.'],
        'summary':{'parameters':param,'weight_resident_bytes':param*s.weight_bytes,
            'backbone_projection_ffn_flops':sum(op.matrix_flops*op.repeats for op in ops if op.category=='linear' and op.name!='lm_head'),
            'causal_attention_matrix_flops':4*config['num_attention_heads']*s.pairs*d*l,
            'rectangular_attention_matrix_flops':4*config['num_attention_heads']*s.rectangular_pairs*d*l,
            'matrix_flops':total('matrix_flops'),'scalar_flops':total('scalar_flops'),'special_ops':dict(special),
            'weight_read_once_per_operator_bytes':total('weight_read_bytes'),
            'activation_operand_read_bytes':total('activation_read_bytes'),'activation_operand_write_bytes':total('activation_write_bytes'),
            'kv_bytes_per_token_per_request':pertoken,'kv_resident_before_bytes':s.batch*s.history*pertoken,
            'kv_resident_after_bytes':s.batch*(s.history+s.tokens)*pertoken,'kv_new_write_bytes':s.rows*pertoken,
            'kv_existing_history_unique_payload_bytes':s.batch*s.history*pertoken,
            'kv_attention_unique_payload_bytes':s.batch*(s.history+s.tokens)*pertoken,
            'kv_logical_query_head_operand_bytes':2*config['num_attention_heads']*s.pairs*d*s.kv_bytes*l,
            'attention_score_tensor_per_layer_bytes':scores,'materialized_scores_probabilities_io_all_layers_bytes':4*scores*l,
            'minimum_required_weight_and_kv_bytes':param*s.weight_bytes+s.batch*(s.history+s.tokens)*pertoken}}


def calculate(model,scenario):
    if model != MODEL:raise ValueError('This public70B adapter does not rename gated Llama records')
    sources=provenance(model)
    for source in sources:read_source(source['file'])
    if not any(x['file'].endswith('modeling_rope_utils.py') for x in sources):
        raise ValueError('Pinned modeling_rope_utils.py provenance must be registered for scaled RoPE')
    return calculate_from_inputs(model_config(model),scenario,sources)
