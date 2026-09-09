"""Small numeric oracles independent of the counting implementation."""
import math,unittest
from reference_steps import supplement

def recurrent(q,k,v,b,g,initial):
    state=initial;out=[]
    for qi,ki,vi,bi,gi in zip(q,k,v,b,g):
        state*=math.exp(gi)
        delta=(vi-ki*state)*bi
        state+=ki*delta
        out.append(qi*state)
    return out,state

def chunks(q,k,v,b,g,initial,C):
    T=len(q);pad=(-T)%C
    q=q+[0.]*pad;k=k+[0.]*pad;v=v+[0.]*pad;b=b+[0.]*pad;g=g+[0.]*pad
    state=initial;out=[]
    for off in range(0,len(q),C):
        qs,ks,vs,bs,gs=[x[off:off+C] for x in (q,k,v,b,g)]
        cum=[];a=0
        for x in gs:a+=x;cum.append(a)
        decay=[[math.exp(cum[i]-cum[j]) if j<=i else 0. for j in range(C)] for i in range(C)]
        lower=[[bs[i]*ks[i]*ks[j]*decay[i][j] for j in range(C)] for i in range(C)]
        def solve(rhs):
            y=[]
            for i in range(C):y.append(rhs[i]-sum(lower[i][j]*y[j] for j in range(i)))
            return y
        u=solve([bs[i]*vs[i] for i in range(C)])
        w=solve([bs[i]*ks[i]*math.exp(cum[i]) for i in range(C)])
        new=[u[i]-w[i]*state for i in range(C)]
        out.extend(qs[i]*math.exp(cum[i])*state+sum(qs[i]*ks[j]*decay[i][j]*new[j] for j in range(C)) for i in range(C))
        state=state*math.exp(cum[-1])+sum(ks[i]*math.exp(cum[-1]-cum[i])*new[i] for i in range(C))
    return out[:T],state

class ReferenceStepTests(unittest.TestCase):
    def test_chunk_numeric_matches_recurrent_with_tail_and_history(self):
        q=[.2,.7,-.3,.4,.5];k=[.1,-.2,.3,.4,-.1];v=[.8,.9,.2,-.1,.6];b=[.2,.6,.3,.7,.1];g=[-.1,-.2,-.4,-.2,-.3]
        for initial in [0.,.6]:
            expected,state=recurrent(q,k,v,b,g,initial)
            for C in [1,2,4,8]:
                actual,final=chunks(q,k,v,b,g,initial,C)
                for a,e in zip(actual,expected):self.assertAlmostEqual(a,e,places=13)
                self.assertAlmostEqual(final,state,places=13)

    def test_reference_conv_output_slots_hand_counts(self):
        hist=[1]*10+[0]*502
        for T,S,L,O,kept in [(1,0,4,7,4),(4,0,4,7,4),(65,0,65,68,65),(1,8,5,2,1),(3,8,7,10,7)]:
            r=supplement(1,T,S,hist)
            self.assertEqual(r['conv']['input_positions'],L)
            self.assertEqual(r['conv']['conv_output_positions_before_slice'],O)
            self.assertEqual(r['conv']['silu_positions_before_final_crop'],kept)
            actual=next(x for x in r['steps'] if x['name']=='conv.additional_padded_and_discarded_products')['matrix_flops']
            valid=sum(min(4,S+i+1) for i in range(T))
            self.assertEqual(actual,2*12288*(4*O-valid))

    def test_prefill_padding_retains_correct_numeric_causal_output(self):
        x=[2.];w=[1.,2.,3.,4.]
        # update_conv_state left-pads to4; conv1d symmetric padding3,
        # first L outputs retained by causal_conv1d_fn, then final T retained.
        padded=[0.,0.,0.]+x
        z=[0.]*3+padded+[0.]*3
        raw=[sum(z[i+j]*w[j] for j in range(4)) for i in range(len(z)-3)]
        self.assertEqual(len(raw),7)
        self.assertEqual(raw[:4][-1:], [8.])

    def test_rope_three_axis_source_work_once(self):
        r=supplement(2,5,0,[1]*100+[0]*412)
        op=next(x for x in r['steps'] if x['name']=='rope.frequency_outer_product')
        self.assertEqual(op['matrix_flops'],2*3*2*5*32)
        self.assertEqual(op['repeats'],1)

    def test_router_metadata_assignment_and_hit_dependence(self):
        hot=[4]*10+[0]*502;spread=[1]*40+[0]*472
        for hist,hit in [(hot,10),(spread,40)]:
            r=supplement(1,4,0,hist)
            one=next(x for x in r['steps'] if x['name']=='router.one_hot_initialize_scatter')
            wh=next(x for x in r['steps'] if x['name']=='router.where_per_active_expert')
            self.assertEqual(one['integer_operations'],40)
            self.assertEqual(wh['integer_operations'],hit*40)

    def test_record_past_initial_cache_alias_not_last4_copy(self):
        r=supplement(1,1,0,[1]*10+[0]*502,True)
        self.assertEqual(r['conv']['input_positions'],1)
        self.assertNotIn('conv.cache_copy_last4',[x['name'] for x in r['steps']])
        self.assertIn('conv.record_past_assign_alias',[x['name'] for x in r['steps']])
        boundary=next(x for x in r['steps'] if x['name']=='conv.cache_concat_or_initial_pad')
        self.assertEqual(boundary['tensor_input_bytes'],0)
        self.assertEqual(boundary['tensor_output_bytes'],0)
        zero=next(x for x in r['steps'] if x['name']=='conv.cache_initial_zero')
        self.assertEqual(zero['tensor_output_bytes'],2*12288*4)

    def test_causal_mask_constructor_batch_expand(self):
        r=supplement(3,2,5,[1]*60+[0]*452)
        compare=next(x for x in r['steps'] if x['name']=='mask.causal_compare_before_batch_expand')
        convert=next(x for x in r['steps'] if x['name']=='mask.bool_to_BF16_where')
        self.assertEqual(compare['integer_operations'],14)
        self.assertEqual(convert['tensor_output_bytes'],84)

    def test_record_past_conv_length_remains_unknown(self):
        r=supplement(1,1,8,[1]*10+[0]*502,True)
        self.assertIsNone(r['conv']['input_positions'])
        self.assertFalse(r['conv']['record_past_shape_known'])

if __name__=='__main__':unittest.main()
