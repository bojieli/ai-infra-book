"""Independent input-index/formula checks; run without PyTorch or model weights."""
import copy,hashlib,json,math,unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.schema import Scenario
from infra_calc.models import llama70
ROOT=Path(__file__).resolve().parents[1]
INPUTS=ROOT/'research/f02-70b-inputs'
CONFIG=json.loads((INPUTS/'config.json').read_text())
SOURCES=json.loads((ROOT/'research/llama70-adapter/sources.lock.json').read_text())['sources']

class Llama70Accounting(unittest.TestCase):
    def test_index_names_and_independent_parameter_formula(self):
        ws=llama70.weights(CONFIG);names=set()
        for w in ws:
            for i in range(w.copies):names.add(w.name.format(layer=i))
        index=json.loads((INPUTS/'model.safetensors.index.json').read_text())
        self.assertEqual(names,set(index['weight_map']));self.assertEqual(len(names),723)
        h,f,kv,l,v=8192,28672,1024,80,128256
        total=2*v*h+l*(2*h*h+2*h*kv+3*h*f+2*h)+h
        self.assertEqual(total,70553706496)
        self.assertEqual(sum(w.parameters for w in ws),total)
        self.assertFalse(any('q_norm' in n or 'k_norm' in n for n in names))

    def test_prefill_decode_matrix_closed_formula(self):
        for b,p,s,head in [(1,8192,0,'last'),(3,1,8192,'all'),(2,17,31,'none')]:
            scenario=Scenario(batch=b,tokens=p,history=s,output_head=head)
            result=llama70.calculate_from_inputs(CONFIG,scenario,SOURCES)
            projection=b*p*80*(4*8192**2+4*8192*1024+6*8192*28672)
            attention=4*64*128*80*b*(p*s+p*(p+1)//2)
            head_rows={'none':0,'last':b,'all':b*p}[head]
            output=2*head_rows*8192*128256
            self.assertEqual(result['summary']['matrix_flops'],projection+attention+output)
            self.assertEqual(result['summary']['kv_bytes_per_token_per_request'],327680)
            self.assertEqual(result['summary']['kv_resident_after_bytes'],b*(s+p)*327680)
            self.assertFalse(any(x['name'] in ('q_norm','k_norm') for x in result['operators']))
            self.assertEqual(sum(x['repeats'] for x in result['operators'] if x['category']=='normalization'),161)

    def test_rope_initialization_regions_and_forward_batch_work(self):
        init=llama70.rope_initialization(CONFIG)
        self.assertEqual(sum(init['frequency_regions'].values()),64)
        # Independently reference the piecewise Llama3 formula; no inverse-frequency initialization per forward.
        for i,actual in enumerate(init['inverse_frequencies']):
            inv=500000**(-i/64);wave=math.tau/inv
            if wave>8192:expected=inv/8
            elif wave<2048:expected=inv
            else:expected=inv*((1-(8192/wave-1)/3)/8+(8192/wave-1)/3)
            self.assertAlmostEqual(actual,expected,places=14)
        rows=llama70.build_operators(CONFIG,Scenario(batch=3,tokens=5))
        r=next(x for x in rows if x.name=='llama3_rope_table')
        self.assertEqual(r.repeats,1);self.assertEqual(r.scalar_flops,5*(64+256))
        self.assertEqual(r.special_ops['sin'],5*128)
        self.assertEqual(init['operator']['scalar_flops'],772)
        self.assertFalse(any(x.category=='initialization' for x in rows))

    def test_scalar_sum_by_stage_and_header_modes(self):
        b,p,s=2,11,7;sc=Scenario(batch=b,tokens=p,history=s)
        rows=llama70.build_operators(CONFIG,sc)
        by={x.name:x for x in rows};m=b*p;valid=64*b*(p*s+p*(p+1)//2)
        self.assertEqual(by['input_layernorm'].scalar_flops,m*(4*8192+1))
        self.assertEqual(by['silu_mul'].scalar_flops,4*m*28672)
        self.assertEqual(by['score_scale_mask_softmax'].scalar_flops,4*valid-m*64)
        self.assertEqual(by['apply_rope'].scalar_flops,3*m*(8192+1024))
        self.assertEqual(by['lm_head'].shapes['output'],[b,128256])
        expected=161*m*(4*8192+1)+80*(3*m*(8192+1024)+(4*valid-m*64)+2*m*8192+4*m*28672)+p*(64+256)
        result=llama70.calculate_from_inputs(CONFIG,sc,SOURCES)
        self.assertEqual(result['summary']['scalar_flops'],expected)

    def test_reject_unsupported_shapes_modes_and_empty_provenance(self):
        for key,value in [('model_type','qwen3'),('attention_bias',True),('mlp_bias',True),('pretraining_tp',2)]:
            c=copy.deepcopy(CONFIG);c[key]=value
            with self.assertRaises(ValueError):llama70.validate(c)
        with self.assertRaises(ValueError):llama70.build_operators(CONFIG,Scenario(tokens=1,history=131072))
        with self.assertRaises(ValueError):llama70.calculate_from_inputs(CONFIG,Scenario(),[])
        with self.assertRaises(ValueError):llama70.build_operators(CONFIG,Scenario(weight_bytes=3))

    def test_pinned_source_hashes(self):
        for src in SOURCES:
            data=(ROOT/src['file']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),src['sha256'])
            self.assertEqual(len(data),src['bytes'])

if __name__=='__main__':unittest.main()
