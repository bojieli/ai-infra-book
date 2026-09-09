"""Packet-count mixtures and historical simple-forwarding CPU budgets."""
from fractions import Fraction
import hashlib
import json
from ..paths import PROJECT
from ..units import positive_int
from .pd_pool import exact_rate


def evidence():
    rows=json.loads((PROJECT/'configs/nic-history.lock.json').read_text())
    for row in rows:
        data=(PROJECT/row['file']).read_bytes()
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise ValueError('Historical NIC source changed: '+row['file'])
    return rows


def calculate(link_bits_per_second=40_000_000_000, link_utilization='1',
              packet_mix=None, wire_overhead_bytes=20, encapsulation_bytes=0,
              baseline_packets_per_core_second=None, cpu_target_utilization='1',
              retained_host_work='1', pcie=None):
    """Fill a declared fraction of the wire with a packet-count distribution.

    Baseline service is 10/20 Mpps per CPU core in the archived thesis, not
    complete virtualization. Multipliers and retained work are explicit what-ifs.
    Optional PCIe requires caller-supplied bytes/packet, service, and latency.
    """
    inputs=locals().copy()
    positive_int(link_bits_per_second,'link_bits_per_second')
    positive_int(wire_overhead_bytes,'wire_overhead_bytes',allow_zero=True)
    positive_int(encapsulation_bytes,'encapsulation_bytes',allow_zero=True)
    utilization=exact_rate(link_utilization,'link_utilization',True)
    target=exact_rate(cpu_target_utilization,'cpu_target_utilization')
    retained=exact_rate(retained_host_work,'retained_host_work',True)
    if utilization>1 or target>1 or retained>1:
        raise ValueError('Utilizations and retained work must not exceed one')
    mix=packet_mix if packet_mix is not None else [dict(frame_bytes=64,packet_share='1')]
    rates=baseline_packets_per_core_second if baseline_packets_per_core_second is not None else [10_000_000,20_000_000]
    if not isinstance(mix,list) or not mix or not isinstance(rates,list) or not rates:
        raise ValueError('Packet mixture and baseline rates must be nonempty lists')
    rows=[]
    for item in mix:
        if not isinstance(item,dict) or set(item)-{'frame_bytes','packet_share','work_multiplier'}:
            raise ValueError('Packet entries accept frame_bytes, packet_share, work_multiplier')
        if 'frame_bytes' not in item or 'packet_share' not in item:
            raise ValueError('Each packet class requires frame_bytes and packet_share')
        frame=item['frame_bytes'];positive_int(frame,'frame_bytes')
        if frame<64:raise ValueError('Ethernet frame budget must be at least 64 bytes including FCS')
        share=exact_rate(item['packet_share'],'packet_share',True)
        work=exact_rate(item.get('work_multiplier','1'),'work_multiplier',True)
        rows.append(dict(frame_bytes=frame,wire_bytes=frame+encapsulation_bytes+wire_overhead_bytes,
                         packet_share_exact=str(share),work_multiplier_exact=str(work)))
    if sum(Fraction(r['packet_share_exact']) for r in rows)!=1:
        raise ValueError('Shares are fractions of packet count and must sum exactly to one')
    mean_wire=sum(Fraction(r['packet_share_exact'])*r['wire_bytes'] for r in rows)
    mean_frame=sum(Fraction(r['packet_share_exact'])*r['frame_bytes'] for r in rows)
    mean_work=sum(Fraction(r['packet_share_exact'])*Fraction(r['work_multiplier_exact']) for r in rows)
    pps=Fraction(link_bits_per_second,8)*utilization/mean_wire
    for row in rows:
        row['packets_per_second_exact']=str(pps*Fraction(row['packet_share_exact']))
    cpus=[]
    for baseline in rates:
        rate=exact_rate(baseline,'baseline_packets_per_core_second')
        busy=pps*mean_work*retained/rate
        provisioned=busy/target
        cpus.append(dict(baseline_packets_per_core_second_exact=str(rate),
                         busy_core_seconds_per_second_exact=str(busy),
                         required_core_equivalents_exact=str(provisioned),
                         dedicated_integer_cores=(provisioned.numerator+provisioned.denominator-1)//provisioned.denominator))
    bus=None
    if pcie is not None:
        expected={'bytes_per_packet','effective_bytes_per_second','transactions_per_packet','mean_transaction_seconds','inflight_slots'}
        if not isinstance(pcie,dict) or set(pcie)!=expected:
            raise ValueError('PCIe needs explicit bytes, service, transaction count, latency and slots')
        size=exact_rate(pcie['bytes_per_packet'],'bytes_per_packet')
        service=exact_rate(pcie['effective_bytes_per_second'],'effective_bytes_per_second')
        transactions=exact_rate(pcie['transactions_per_packet'],'transactions_per_packet')
        latency=exact_rate(pcie['mean_transaction_seconds'],'mean_transaction_seconds')
        slots=pcie['inflight_slots'];positive_int(slots,'inflight_slots')
        required_slots=pps*transactions*latency
        bound=min(service/size,Fraction(slots)/(transactions*latency))
        bus=dict(demand_bytes_per_second_exact=str(pps*size),
                 required_mean_inflight_exact=str(required_slots),
                 required_integer_slots=(required_slots.numerator+required_slots.denominator-1)//required_slots.denominator,
                 bandwidth_packet_bound_exact=str(service/size),
                 inflight_packet_bound_exact=str(Fraction(slots)/(transactions*latency)),
                 necessary_packet_bound_exact=str(bound),offered_rate_fits_necessary_bounds=pps<=bound,
                 scope='Caller supplied effective service; excludes unprovided protocol traffic and queueing')
    return dict(schema_version=1,calculation='nic-budget',model='historical simple forwarding',scenario=inputs,
                sources=evidence(),nic_packet_classes=rows,nic_cpu_candidates=cpus,pcie_budget=bus,
                summary=dict(mean_wire_bytes_per_packet_exact=str(mean_wire),
                             mean_work_multiplier_exact=str(mean_work),
                             packets_per_second_exact=str(pps),
                             original_frame_bytes_per_second_exact=str(pps*mean_frame),
                             wire_bytes_per_second_exact=str(pps*mean_wire),
                             retained_host_work_exact=str(retained),
                             dedicated_cpu_cores=[r['dedicated_integer_cores'] for r in cpus],
                             complete_virtualization_cpu_cores=None),
                assumptions=[
                    'Historical thesis §4.2.1 reports 40 Gbps approximately 60 Mpps and simple forwarding 10–20 Mpps/core. This is the historical baseline, not a modern CPU benchmark or complete virtualization measurement.',
                    'Default wire budget is a declared 64-byte Ethernet frame including FCS plus 8-byte preamble/SFD and 12-byte interpacket gap. Frame bytes are not application payload; encapsulation adds wire bytes before packet-rate conversion.',
                    'Mixture shares are by packet count. Rate divides wire bytes/s by weighted mean wire occupancy, not a weighted mean of each class full-line packet rate. Fragmentation and MTU changes are not inferred.',
                    'Work multipliers, target utilization and retained host work are declared comparisons. Busy core-seconds differ from allocated integer cores; linear multicore scaling is assumed, not established.',
                    'Offload reduces only the declared host packet work. PCIe and in-flight constraints, when supplied, remain even if retained host work is zero; hardware processing, full host work, costs and SLOs are unknown.',
                    'PCIe byte and concurrency limits are necessary resource bounds for one declared shared service, not sufficient throughput guarantees. No advertised link rate is silently used as effective payload service.',
                ])
