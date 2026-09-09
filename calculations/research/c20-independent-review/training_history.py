"""C20: archived historical inputs, proxy work, conditional time and scenario costs.

No network, hardware peak, MFU, price, or undisclosed training input is inferred.
The project argument is the calculations directory (lock paths are relative to it).
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path


def _number(value, name, *, positive=False, integer=False):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(f'{name} must be an exact integer or rational string, or null')
    try:
        number = Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError(f'Invalid {name}') from error
    if number < 0 or (positive and number == 0) or (integer and number.denominator != 1):
        raise ValueError(f'Invalid {name}')
    return number


def _exact(value):
    return None if value is None else str(value)


def _product(a, b):
    # Even zero times an unknown stays unknown: missing inputs are not zero.
    return None if a is None or b is None else a * b


def verify_archives(project, lock):
    """Verify each file, including PDF/text pairs with the same source ID."""
    checked = []
    for record in lock:
        data = (Path(project) / record['file']).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != record['sha256'] or len(data) != record['bytes']:
            raise ValueError(f"Archived source mismatch: {record['file']}")
        checked.append({**deepcopy(record), 'verified_sha256': digest,
                        'verified_bytes': len(data)})
    return checked


def _model(row):
    n = _number(row.get('parameter_proxy'), 'parameter_proxy', positive=True, integer=True)
    d = _number(row.get('training_tokens'), 'training_tokens', positive=True, integer=True)
    hours = _number(row.get('gpu_hours'), 'gpu_hours')
    count = _number(row.get('gpu_count'), 'gpu_count', positive=True, integer=True)
    reported = _number(row.get('reported_training_flops'), 'reported_training_flops', positive=True)
    kind = row.get('parameter_proxy_kind')
    if n is not None and kind not in ('nominal_dense_proxy', 'active_parameter_proxy'):
        raise ValueError('6ND requires an explicitly nominal dense or active parameter proxy')
    role = row.get('gpu_count_role')
    if role not in (None, 'reported_configuration', 'reported_maximum'):
        raise ValueError(f'Unsupported GPU count role: {role}')
    work = None if n is None or d is None else 6 * n * d
    days = None if hours is None or count is None or role is None else hours / count / 24
    maximum = role == 'reported_maximum'
    return dict(
        input=deepcopy(row),
        tokens_per_parameter_exact=_exact(None if n is None or d is None else d / n),
        proxy_flops=None if work is None else int(work),
        proxy_kind=kind,
        proxy_to_reported_flops_ratio_exact=_exact(None if work is None or reported is None else work / reported),
        duration=dict(
            conditional_constant_count_days_exact=_exact(days),
            conditional_constant_count_days=None if days is None else float(days),
            conditional_calendar_lower_bound_days_exact=_exact(days if maximum else None),
            calendar_lower_bound_days_exact=_exact(days if maximum and row.get('gpu_hours_count_scope_match') is True else None),
            gpu_hours_count_scope_match=row.get('gpu_hours_count_scope_match'),
            measured_calendar_days=None,
            interpretation=('unknown' if days is None else
                            'lower_bound_using_reported_maximum' if maximum else
                            'conditional_on_constant_reported_configuration'),
            assumption='GPU hours and count cover the same scope; constant count for the conditional duration. A maximum only bounds elapsed time from below.'),
        mfu=None,
        parameter_context=dict(total_reported=row.get('total_parameters_reported'),
                               active_reported=row.get('active_parameters_reported'),
                               note='Reported rounded parameter labels; active proxy is not weight capacity.'),
    )


def _stage(report):
    additive = 'parts' in report
    if additive == ('alternatives' in report):
        raise ValueError('Stage report must have exactly one of parts or alternatives')
    values = report['parts' if additive else 'alternatives']
    if not isinstance(values, dict) or not values:
        raise ValueError('Nonempty stage values required')
    hours = [_number(v, 'stage GPU hours') for v in values.values()]
    total = sum(hours, Fraction()) if additive and all(v is not None for v in hours) else None
    reported = _number(report.get('reported_total'), 'reported_total')
    return dict(input=deepcopy(report), aggregation='additive' if additive else 'alternatives',
                summed_gpu_hours_exact=_exact(total),
                reported_total_matches=None if total is None or reported is None else total == reported)


def _lifecycle(spec, rows):
    """One declared training row plus a caller's service usage and unit price.

    These are scoped scenario subtotals, never a claimed complete historical cost.
    Currency and service_unit must be explicit; no currency/unit conversions occur.
    """
    identifier = spec['model']
    if identifier not in rows:
        raise ValueError(f'Unknown lifecycle model: {identifier}')
    for label in ('currency', 'service_unit', 'scope'):
        if not isinstance(spec.get(label), str) or not spec[label].strip():
            raise ValueError(f'Lifecycle {label} must be explicit')
    price = _number(spec.get('training_price_per_gpu_hour'), 'training_price_per_gpu_hour')
    usage = _number(spec.get('service_usage'), 'service_usage')
    unit_price = _number(spec.get('service_price_per_unit'), 'service_price_per_unit')
    other = _number(spec.get('other_cost'), 'other_cost')
    hours = _number(rows[identifier]['input'].get('gpu_hours'), 'gpu_hours')
    training = _product(hours, price)
    service = _product(usage, unit_price)
    total = None if any(v is None for v in (training, service, other)) else training + service + other
    return dict(input=deepcopy(spec), training_gpu_hours_exact=_exact(hours),
                training_cost_exact=_exact(training), service_cost_exact=_exact(service),
                scoped_lifecycle_cost_exact=_exact(total),
                interpretation='caller_supplied_cost_scenario_for_selected_training_row_and_service_usage')


def _duration_scenario(spec, rows):
    identifier = spec['model']
    if identifier not in rows:
        raise ValueError(f'Unknown duration model: {identifier}')
    low = _number(spec.get('min_constant_gpu_count'), 'min_constant_gpu_count', positive=True, integer=True)
    high = _number(spec.get('max_constant_gpu_count'), 'max_constant_gpu_count', positive=True, integer=True)
    if low is None or high is None or low > high:
        raise ValueError('An ordered positive constant-count interval is required')
    hours = _number(rows[identifier]['input'].get('gpu_hours'), 'gpu_hours')
    return dict(input=deepcopy(spec),
                conditional_days_min_exact=_exact(None if hours is None else hours / high / 24),
                conditional_days_max_exact=_exact(None if hours is None else hours / low / 24),
                assumption='Caller-supplied constant-count scenarios for the reported GPU-hour scope, not measured calendar dates.')


def calculate(project=None, comparisons=None, duration_scenarios=None, lifecycle=None):
    """Return the infra_calc schema envelope with preserved catalog and evidence.

    In-package default uses infra_calc.paths.PROJECT. Standalone callers must pass
    project explicitly. Unknown catalog fields are copied without interpretation.
    """
    if project is None:
        from infra_calc.paths import PROJECT
        project = PROJECT
    project = Path(project)
    catalog_bytes = (project / 'configs/training-history.json').read_bytes()
    lock_bytes = (project / 'configs/training-history.lock.json').read_bytes()
    catalog, lock = json.loads(catalog_bytes), json.loads(lock_bytes)
    sources = verify_archives(project, lock)
    source_ids = {s['id'] for s in sources}
    if not source_ids:
        raise ValueError('Source lock must not be empty')
    models = catalog['models']
    if len({r['id'] for r in models}) != len(models):
        raise ValueError('Duplicate model ID')
    for record in [*models, *catalog.get('stage_reports', []), *catalog.get('reported_performance', [])]:
        if record.get('source_id') not in source_ids:
            raise ValueError('Catalog record has no verified source')
        for field, identifier in record.get('field_source_ids', {}).items():
            if identifier not in source_ids:
                raise ValueError(f'Field {field} has no verified source')
    rows = {r['id']: _model(r) for r in models}
    growth = []
    for spec in comparisons or []:
        base, target = spec['baseline'], spec['target']
        if base not in rows or target not in rows:
            raise ValueError('Unknown comparison model')
        result = dict(input=deepcopy(spec))
        for key in ('parameter_proxy', 'training_tokens'):
            a = _number(rows[base]['input'].get(key), key, positive=True)
            b = _number(rows[target]['input'].get(key), key, positive=True)
            result[key + '_growth_exact'] = _exact(None if a is None or b is None else b / a)
        a, b = rows[base]['proxy_flops'], rows[target]['proxy_flops']
        result['proxy_flops_growth_exact'] = _exact(None if a is None or b is None else Fraction(b, a))
        result['interpretation'] = 'Descriptive proxy ratio; scope, architecture and quality are not controlled.'
        growth.append(result)
    return dict(
        schema_version=1, calculation='training-history', model='historical-training-catalog',
        scenario=dict(comparisons=deepcopy(comparisons or []),
                      duration_scenarios=deepcopy(duration_scenarios or []), lifecycle=deepcopy(lifecycle or [])),
        catalog=deepcopy(catalog), sources=sources,
        input_sha256=dict(catalog=hashlib.sha256(catalog_bytes).hexdigest(),
                          lock=hashlib.sha256(lock_bytes).hexdigest()),
        training_history_rows=list(rows.values()),
        stage_reports=[_stage(r) for r in catalog.get('stage_reports', [])],
        reported_performance=deepcopy(catalog.get('reported_performance', [])),
        comparisons=growth,
        duration_scenarios=[_duration_scenario(s, rows) for s in duration_scenarios or []],
        lifecycle=[_lifecycle(s, rows) for s in lifecycle or []],
        summary=dict(models=len(rows), verified_archives=len(sources)),
        assumptions=[
            '6ND is only the declared nominal dense or active-parameter proxy; attention, MTP, recomputation, precision and nonmatrix work are not fully accounted for.',
            'D/N uses the same proxy N, not an inferred total MoE parameter count. Undisclosed inputs remain null.',
            'GPU hours across A100, H100 and H800 are not normalized compute or efficiency comparisons. MFU remains null; no hardware peaks or prices are inferred.',
            'Reported configurations require a constant-count assumption; reported maxima give conditional lower bounds only when GPU hours and count refer to the same scope. Source-scope identity must be affirmed before an unconditional calendar lower bound is populated; neither is a measured date.',
            'mfu=null means no full-run MFU computed here. reported_performance preserves source stage observations separately; no single observation represents full training.',
            'DeepSeek-V3 final stages exclude earlier research. Qwen3 Table 21 branches are alternatives and never become pretraining GPU hours.',
            'Lifecycle costs require caller prices, usage, units, currency and scope. Missing other_cost stays null; use explicit zero only when intentionally excluded. No quality equivalence or scaling law fit is inferred.',
        ])
