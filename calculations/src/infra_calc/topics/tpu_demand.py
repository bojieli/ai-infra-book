"""Historical TPU demand anchor and explicitly conditional usage scaling.

The paper supplies a projected doubling at three minutes/day, not the number
of users or servers. Normalize existing capacity to one and retain that limit.
"""
from fractions import Fraction
import hashlib
import json

from ..paths import PROJECT
from ..units import positive_int
from .pd_pool import exact_rate


def evidence():
    rows = json.loads((PROJECT / 'configs/tpu-demand.lock.json').read_text())
    for row in rows:
        data = (PROJECT / row['file']).read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Historical TPU demand source changed: ' + row['file'])
    return rows


def calculate(minutes_per_person_day='3', relative_population='1',
              relative_work_per_audio_second='1', relative_peak_factor='1',
              baseline_server_equivalents=None, effective_capacity_gain=None):
    """Scale the historical demand anchor under a declared linear capacity model.

    Gain applies only to the added voice workload. It is a supplied effective
    workload-capacity ratio, never the paper's 10x cost-performance design goal.
    Optional baseline equivalents are a teaching input, not Google's inventory.
    """
    inputs = locals().copy()
    minutes = exact_rate(minutes_per_person_day, 'minutes_per_person_day', True)
    population = exact_rate(relative_population, 'relative_population', True)
    work = exact_rate(relative_work_per_audio_second, 'relative_work_per_audio_second')
    peak = exact_rate(relative_peak_factor, 'relative_peak_factor')
    if minutes > 24 * 60:
        raise ValueError('Daily per-person voice use cannot exceed 1440 minutes')
    if baseline_server_equivalents is not None:
        positive_int(baseline_server_equivalents, 'baseline_server_equivalents')
    gain = (None if effective_capacity_gain is None else
            exact_rate(effective_capacity_gain, 'effective_capacity_gain'))
    # Normalize existing capacity to 1. The historical projection adds another 1
    # at three minutes/day; all subsequent linearity is an explicit assumption.
    factors = [('usage_minutes', minutes / 3), ('population', population),
               ('work_per_audio_second', work), ('peak_requirement', peak)]
    added = Fraction(1)
    stages = []
    for name, factor in factors:
        before = added
        added *= factor
        stages.append(dict(factor=name, multiplier_exact=str(factor),
                           input_capacity_exact=str(before), output_capacity_exact=str(added)))
    allocations = []
    for name, required in [('conventional_reference', added),
                           ('supplied_effective_gain', None if gain is None else added / gain)]:
        continuous = (None if baseline_server_equivalents is None or required is None else
                      baseline_server_equivalents * required)
        integer = (None if continuous is None else
                   (continuous.numerator + continuous.denominator - 1) // continuous.denominator)
        allocations.append(dict(candidate=name,
            incremental_capacity_in_baseline_units_exact=None if required is None else str(required),
            total_capacity_in_baseline_units_exact=None if required is None else str(1 + required),
            supplied_baseline_server_equivalents=baseline_server_equivalents,
            added_server_equivalents_exact=None if continuous is None else str(continuous),
            added_whole_server_equivalents=integer,
            total_whole_server_equivalents=None if integer is None else baseline_server_equivalents + integer,
            physical_accelerator_count=None, actual_cost=None))
    return dict(schema_version=1, calculation='tpu-demand', model='2013 demand projection in TPU v1 paper',
        scenario=inputs, sources=evidence(), tpu_demand_factors=stages, tpu_capacity_candidates=allocations,
        summary=dict(reference_minutes_per_person_day=3,
            reference_existing_capacity_units=1, reference_projected_total_capacity_units=2,
            requested_minutes_per_person_day_exact=str(minutes),
            incremental_conventional_capacity_exact=str(added),
            total_conventional_capacity_exact=str(1 + added),
            supplied_effective_capacity_gain_exact=None if gain is None else str(gain),
            historical_user_count=None, historical_server_count=None,
            actual_accelerator_count=None, actual_cost=None),
        assumptions=[
            'The archived paper section 2 reports a 2013 projection: three minutes/person/day voice search would require datacenter computation capacity to double. It does not provide user population or server inventory for reproducing an absolute historical count.',
            'Existing computation capacity is normalized to one; the anchor is interpreted as one additional unit of voice demand. Linear usage, population, per-audio work and peak scaling are explicit teaching assumptions, not additional historical observations.',
            'Baseline server equivalents, when supplied, are a homogeneous capacity normalization. Integer rounding allocates added units only once. It is not a placement, hardware inventory, power, latency or accelerator-count prediction.',
            'An optional effective gain affects only the added voice workload, leaving the baseline workload at one unit. The paper\'s 10x cost-performance design target is not an effective throughput multiplier and is never used automatically.',
            'No absolute server count or cost is filled without inputs. Queueing, supply bandwidth, latency targets, cost, development, delivery and heterogeneous host requirements remain outside this demand-only calculation.',
        ])
