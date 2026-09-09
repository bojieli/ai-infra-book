"""Build a merge-only research artifact from transcribed official Table3-1.

Does not edit shared config or sources. Validate against the project's current
contract and verify the existing official PDF lock before producing the patch.
"""
import hashlib
import json
import sys
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'src'))
from infra_calc.hardware import validate_device, select_peak
SID='ascend-950-official'
TABLE={
 'PR':dict(cores=[32,28],vector=[64,56],
           cube={'MXFP4':[1730,1513],'FP8/MXFP8/HiF8':[865,756],'INT8':[865,756],'FP16/BF16':[432,378],'TF32':[216,189]},
           vector_rates={'FP16/BF16':[54,47],'FP32':[27,23],'INT8':[54,47],'INT16':[27,23],'INT32':[13,11],'INT64':[6,5]},
           total={'MXFP4':[1784,1561],'FP8/MXFP8/HiF8':[919,804],'INT8':[919,804],'FP16/BF16':[486,425],'TF32':[243,212]},
           memory=[128,112],bandwidth=['1.6','1.4']),
 'DT':dict(cores=[36,32,28],vector=[72,64,56],
           cube={'MXFP4':[1946,1730,1513],'FP8/MXFP8/HiF8':[973,865,756],'INT8':[973,865,756],'FP16/BF16':[486,432,378],'TF32':[243,216,189]},
           vector_rates={'FP16/BF16':[60,54,47],'FP32':[30,27,23],'INT8':[60,54,47],'INT16':[30,27,23],'INT32':[15,13,11],'INT64':[7,6,5]},
           total={'MXFP4':[2007,1784,1561],'FP8/MXFP8/HiF8':[1034,919,804],'INT8':[1034,919,804],'FP16/BF16':[547,486,425],'TF32':[273,243,212]},
           memory=[144,96],bandwidth=['4'])}


def build():
    source=next(r for r in json.loads((PROJECT/'configs/sources.lock.json').read_text())['sources'] if r.get('id')==SID)
    data=(PROJECT/source['file']).read_bytes()
    if hashlib.sha256(data).hexdigest()!=source['sha256'] or len(data)!=source['bytes']:
        raise ValueError('Official950PDF differs from current lock')
    devices=[]
    for family,t in TABLE.items():
        for index,cores in enumerate(t['cores']):
            peaks=[]
            for unit,key in [('cube','cube'),('vector','vector_rates'),('cube_plus_vector','total')]:
                for group,values in t[key].items():
                    for precision in group.split('/'):
                        kind='integer' if precision.startswith('INT') else 'floating_point'
                        peaks.append(dict(input_precision=precision,accumulator_precision='unspecified',execution_unit=unit,
                                          sparsity='unspecified',tera_ops_per_second=values[index],operation_kind=kind,
                                          source_id=SID,locator=f'Table3-1, physicalpp13-14:950{family}; {unit}; {group}; slash position{index+1} aligned with core-count column',
                                          reported='/'.join(map(str,values))+(' TOPS' if kind=='integer' else ' TFLOPS'),
                                          derivation='Select the corresponding same-family compute-column ordinal; no frequency scaling or recomputation from rounded component rates',
                                          clock_basis='Official theoretical capability; no table-bound operating clock or power supplied'))
            d=dict(id=f'ascend-950{family.lower()}-{cores}cube-capability',name=f'Ascend 950{family} {cores} Cube / {t["vector"][index]} Vector capability profile',
                   vendor='Huawei',architecture='Ascend950 third-generation AI core',form_factor='Single-chip compute capability profile; not a board, orderableSKU or verified memory/core combination',
                   spec_scope='single_device',record_kind='chip_capability_profile',configuration_status='official_compute_capability_column_only_not_orderable_SKU_mapping',
                   source_ids=[SID],core_evidence=dict(source_id=SID,locator='Table3-1, physicalp13, Cube/Vector core-count rows',cube_cores=cores,vector_cores=t['vector'][index],column_index=index),
                   memory=dict(nominal_capacity=None,capacity_unit='GB',bandwidth_bytes_per_second=None,source_id=SID,locator='Table3-1, physicalp14, Memory options; no complete profile-to-board mapping',
                               capacity_note='Compute profile only. Family memory options are recorded separately and not assigned to this core profile.'),
                   family_memory_options=dict(source_id=SID,locator='Table3-1, physicalp14: family Memory rows',nominal_capacity_GB_options=t['memory'],reported_bandwidth_TB_per_second_options=t['bandwidth'],cross_product_validated=False,profile_assignment=None),
                   power_watts=None,peak_rates=peaks,
                   field_status=dict(core_and_compute_column='verified_table_ordinal',memory_and_orderable_card_mapping='not_verified',accumulator='not_disclosed_in_checked_table',sparsity='not_disclosed_in_checked_table',clock_and_power='not_bound_to_compute_table'),
                   notes=['只记录官方芯片计算能力列，不是订货SKU、不是真实板卡，也不证明某容量与该核数同时交付。实际Atlas350板卡112GB/1.4TB/s另有独立记录。',
                          '单芯片scope用于描述能力范围；form_factor及record_kind明确capability profile，不能把这个ID显示为已交付加速卡。',
                          'Cube、Vector与相加宣传值分列；cube_plus_vector不能当单个GEMM的峰值。原始显示值各自取整，禁止由分项相加覆盖总数。',
                          'TF32不改成IEEE FP32；FP8/MXFP8/HiF8/MXFP4各保留格式名；INT8/16/32/64均为整数TOPS。',
                          '表3-1未给累加/稀疏/绑定频率功率；A3白皮书dense证据不移植到950，所有本记录峰值仍被精度明确的Roofline拒绝。'])
            validate_device(d)
            assert len(peaks)==23
            try:select_peak(d,'FP16','FP32','cube','dense')
            except ValueError:pass
            else:raise AssertionError('Undisclosed sparse/accumulator must not become selectable')
            devices.append(d)
    # Independent known cell/rounding checks, not sums used as replacements.
    dt36=devices[2]
    values={(r['execution_unit'],r['input_precision']):r['tera_ops_per_second'] for r in dt36['peak_rates']}
    assert values['cube_plus_vector','BF16']==547
    assert values['cube','BF16']+values['vector','BF16']==546
    assert values['vector','INT64']==7
    assert devices[-1]['peak_rates'][0]['tera_ops_per_second']==1513
    return dict(schema_version=1,devices_to_append=devices,device_updates=[],sources_to_append=[],existing_source_ids_required=[SID],
                verified_source=source,scope='Five compute capability profiles; existing max-spec composites and real Atlas350 board remain separate',
                validation=dict(devices=5,peak_records=115,records_per_profile=23,official_pdf_sha256=source['sha256'],precision_specific_roofline_rejected_profiles=5))


if __name__=='__main__':
    result=build();target=Path(__file__).with_name('hardware-950-profiles-patch.json')
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result['validation']))
