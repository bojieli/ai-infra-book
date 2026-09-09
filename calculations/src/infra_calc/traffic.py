"""Count each logical transfer on every declared physical resource in its path.

Repeated resource IDs deliberately count repeated service, e.g. a DRAM write
and read. Aggregate and round-barrier resource bounds are distinct quantities.
"""
from collections import Counter
from .units import positive_int


def account(rounds: list[dict], paths: dict[tuple[int, int], list[str]],
            bandwidths: dict[str, int], startup_ns: int = 0) -> dict:
    positive_int(startup_ns, 'startup_ns', allow_zero=True)
    for name, rate in bandwidths.items():
        positive_int(rate, name + ' bandwidth')
    total = Counter()
    phases = []
    logical = 0
    for number, row in enumerate(rounds):
        current = Counter()
        for edge in row['edges']:
            count = edge['bytes']
            positive_int(count, 'edge bytes', allow_zero=True)
            key = (edge['sender'], edge['receiver'])
            if key not in paths or not paths[key]:
                raise ValueError(f'Missing explicit physical path for {key}')
            logical += count
            for resource in paths[key]:
                if resource not in bandwidths:
                    raise ValueError(f'Missing bandwidth for resource {resource}')
                current[resource] += count
        total.update(current)
        lower = max((count / bandwidths[name] for name, count in current.items()), default=0)
        phases.append(dict(round=number, phase=row.get('phase'), resource_bytes=dict(current),
                           resource_lower_seconds=lower,
                           barrier_lower_with_startup_seconds=lower + (startup_ns / 1e9 if any(current.values()) else 0)))
    resources = [dict(resource=name, bytes=count, bandwidth_bytes_per_second=bandwidths[name],
                      service_seconds=count / bandwidths[name]) for name, count in sorted(total.items())]
    return dict(logical_send_bytes=logical, resources=resources, rounds=phases,
                aggregate_resource_lower_seconds=max((row['service_seconds'] for row in resources), default=0),
                sum_round_resource_lower_seconds=sum(row['resource_lower_seconds'] for row in phases),
                barrier_lower_with_startup_seconds=sum(row['barrier_lower_with_startup_seconds'] for row in phases))
