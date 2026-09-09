import sys
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import unittest
from copy import deepcopy
from fractions import Fraction
from infra_calc.topics.reconfiguration import (calculate, intervals, transfer_plan, amortization,
                             deployment_cost, COST_TERMS, RUNTIME_TERMS)
from infra_calc.sources import model_config
from infra_calc.topics import dense_placement, weight_handoff


def scenario(model='qwen3-8b', stp=4, sep=1, ttp=8, tep=1):
    return dict(model=model, source=dict(tp=stp, ep=sep, devices=[f'g{i}' for i in range(stp*sep)]),
        target=dict(tp=ttp, ep=tep, devices=[f'g{i}' for i in range(ttp*tep)]),
        batch=2, history=16, state_identity_verified=True,
        bandwidth=dict(fabric_bytes_per_second=10**9, sender_bytes_per_second=10**8,
                       receiver_bytes_per_second=2*10**8))


class ReconfigurationTests(unittest.TestCase):
    def test_dense_interface_and_gqa_replication(self):
        for tp in (1,4,8,16,32):
            c=model_config('qwen3-8b')
            p=intervals(c, scenario(stp=tp)['source'],2,16,0)
            ref=dense_placement.calculate(tp=tp,batch_per_replica=2,history=15,tokens=1,workspace_bytes=0)
            for i, card in enumerate(ref['placement_cards']):
                for kind, key in [('weight','weight_bytes'),('kv','kv_bytes')]:
                    actual=sum(v['unit_bytes']*(o['stop']-o['start']) for v in p.values() if v['kind']==kind
                               for o in v['owners'] if o['device']==f'g{i}')
                    self.assertEqual(actual,card[key])

    def test_ep_interface_including_uneven(self):
        c=model_config('qwen3-235b-a22b')
        for ep in (1,7,8,16):
            p=intervals(c,scenario(model='qwen3-235b-a22b',stp=1,sep=ep)['source'],1,0,0)
            ref=weight_handoff.calculate(expert_parallel=ep)
            for rank in ref['weight_handoff_ranks']:
                actual=sum(v['unit_bytes']*(o['stop']-o['start']) for v in p.values()
                           for o in v['owners'] if o['device']==f"g{rank['rank']}")
                self.assertEqual(actual,rank['required_weight_bytes'])

    def test_noop_and_device_permutation(self):
        s=scenario(ttp=4)
        r=calculate(s)
        self.assertEqual(r['summary']['network_bytes'],0)
        s['target']['devices'].reverse()
        r=calculate(s)
        self.assertGreater(r['migration_totals']['weight']['network_bytes'],0)
        self.assertGreater(r['migration_totals']['kv']['network_bytes'],0)

    def test_reconstruct_every_destination_coordinate(self):
        # Uneven source partitions and replicated source copies; reconstruct bytes.
        for ns in range(1,8):
            for nt in range(1,8):
                def make(n):
                    owners=[]
                    for i in range(n):
                        a,b=17*i//n,17*(i+1)//n
                        owners.append(dict(device=f'd{i}',start=a,stop=b))
                        owners.append(dict(device=f'replica{i}',start=a,stop=b))
                    return {'x':dict(kind='weight',unit_bytes=3,owners=owners)}
                src,dst=make(ns),make(nt)
                plan=transfer_plan(src,dst)
                for owner in dst['x']['owners']:
                    reconstructed=[]
                    for p in plan:
                        if p['target']==owner['device']:
                            reconstructed.extend(range(p['start']*3,p['stop']*3))
                    self.assertEqual(reconstructed,list(range(owner['start']*3,owner['stop']*3)))
                self.assertEqual(sum(p['bytes'] for p in plan),17*3*2)

    def test_ep_expansion_new_devices_and_conservation(self):
        s=scenario('qwen3-235b-a22b',1,8,1,16)
        r=calculate(s)
        expert_to_new=sum(p['bytes'] for p in r['transfers'] if '.experts.' in p['tensor'] and int(p['target'][1:])>=8)
        expected=weight_handoff.calculate()['summary']['expert_bf16_weight_bytes']//2
        self.assertEqual(expert_to_new,expected)
        c=model_config(s['model'])
        dst=intervals(c,s['target'],2,16,0)
        expected_total=sum(v['unit_bytes']*(o['stop']-o['start']) for v in dst.values() for o in v['owners'])
        self.assertEqual(sum(p['bytes'] for p in r['transfers']),expected_total)
        self.assertEqual(sum(r['sender_bytes'].values()),sum(r['receiver_bytes'].values()))

    def test_bounds_capacity_and_replay(self):
        s=scenario(); r=calculate(s)
        bounds=[Fraction(x) for x in r['transfer_bounds_exact_seconds'].values()]
        self.assertEqual(Fraction(r['summary']['transfer_lower_bound_exact_seconds']),max(bounds))
        self.assertIsNone(r['summary']['declared_serial_switch_seconds_exact'])
        peak=r['placement_cards'][0]['declared_copy_before_release_peak_bytes']
        s['capacity_bytes_by_device']={'g0':peak}
        self.assertTrue(calculate(s)['placement_cards'][0]['fits_declared_peak'])
        s['capacity_bytes_by_device']['g0']-=1
        self.assertFalse(calculate(s)['placement_cards'][0]['fits_declared_peak'])
        s['runtime_seconds']={k:0 for k in RUNTIME_TERMS}
        s['state_policy']='replay'; s['runtime_seconds']['replay_prefill']=5
        replay=calculate(s)
        self.assertEqual(replay['migration_totals']['kv']['network_bytes'],0)
        self.assertIsNone(replay['summary']['declared_serial_switch_seconds_exact'])
        self.assertGreaterEqual(Fraction(replay['summary']['conditional_serial_switch_lower_bound_exact_seconds']),5)
        self.assertEqual(replay['placement_cards'][0]['target_resident_bytes'],r['placement_cards'][0]['target_resident_bytes'])

    def test_amortization_exact_edges(self):
        self.assertEqual(amortization(10,'0.0002')['break_even_steps'],50000)
        self.assertEqual(amortization(10,'0.0002')['strictly_better_steps'],50001)
        self.assertEqual(amortization(1,'0.3')['break_even_steps'],4)
        self.assertIsNone(amortization(1,0)['break_even_steps'])
        self.assertIsNone(amortization(1,-1)['strictly_better_steps'])
        self.assertEqual(amortization(0,1)['break_even_steps'],0)
        self.assertEqual(amortization(None,1)['status'],'missing_input')

    def test_cost_all_attempts_and_missing(self):
        spec=dict(currency='hypothetical_units',terms={k:[] for k in COST_TERMS},slo_valid_completed_requests=2)
        spec['terms']['steady_service']=[dict(quantity=3,rate=2)]
        spec['terms']['failed_attempts']=[dict(quantity=2,rate='0.5')]
        spec['terms']['custom']=[dict(quantity=1,rate=1)]
        r=deployment_cost(spec)
        self.assertEqual(r['full_declared_cost_exact'],'8')
        self.assertEqual(r['cost_per_slo_valid_request_exact'],'4')
        spec['terms']['recovery_and_replay']=None
        self.assertIsNone(deployment_cost(spec)['full_declared_cost_exact'])
        spec['slo_valid_completed_requests']=0
        self.assertIsNone(deployment_cost(spec)['cost_per_slo_valid_request_exact'])

    def test_unknown_fields_preserved_no_mutation(self):
        s=scenario(); s['future']={'unknown':[1,2]}; s['target']['annotation']='keep'
        old=deepcopy(s); r=calculate(s)
        self.assertEqual(s,old); self.assertEqual(r['scenario'],old)
        r['scenario']['future']['unknown'].append(3)
        self.assertEqual(s,old)

    def test_mixed_layout_auxiliary_and_unknown_runtime(self):
        s=scenario('qwen3-30b-a3b',2,4,4,2)
        s['auxiliary_state_bytes']=101
        r=calculate(s)
        self.assertEqual(sum(r['migration_totals']['auxiliary'].values()),101)
        target=intervals(model_config(s['model']),s['target'],2,16,101)
        self.assertEqual(sum(p['bytes'] for p in r['transfers']),
                         sum(v['unit_bytes']*(o['stop']-o['start']) for v in target.values() for o in v['owners']))
        s['runtime_seconds']={k:0 for k in RUNTIME_TERMS}
        s['runtime_seconds']['future_runtime']=None
        self.assertIn('future_runtime',calculate(s)['summary']['missing_runtime_terms'])
        s['target']['pp']=2
        with self.assertRaises(ValueError):calculate(s)

    def test_invalid_scope_and_source_holes(self):
        for change in ({'state_identity_verified':False},{'same_weight_version':False}, {'history':-1}, {'batch':True}, {'state_policy':'magic'}):
            s=scenario(); s.update(change)
            with self.assertRaises(ValueError): calculate(s)
        for tp,ep in ((3,1),(4,2)):
            s=scenario(); s['target']=dict(tp=tp,ep=ep,devices=[f'd{i}' for i in range(tp*ep)])
            with self.assertRaises(ValueError):calculate(s)
        s=scenario(); s['bandwidth']['fabric_bytes_per_second']=0
        with self.assertRaises(ValueError):calculate(s)
        with self.assertRaises(ValueError):
            transfer_plan({'x':dict(unit_bytes=1,owners=[])}, {'x':dict(kind='weight',unit_bytes=1,owners=[dict(device='x',start=0,stop=1)])})

if __name__ == '__main__': unittest.main()
