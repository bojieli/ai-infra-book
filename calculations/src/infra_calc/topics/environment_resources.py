"""Reaccount two independent, archived CPU/RSS experiments; never execute them."""
from fractions import Fraction
import hashlib
import json
from statistics import median

from ..paths import PROJECT
from ..sources import provenance


def number(value):
    """Use the recorded decimal values consistently, without claiming clock accuracy."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('Expected a recorded numeric measurement')
    result = Fraction(str(value))
    if result < 0:
        raise ValueError('Measurements must be nonnegative')
    return result


def read_records(dataset):
    lock = json.loads((PROJECT / 'configs/environment-resources.lock.json').read_text())
    if dataset not in lock:
        raise ValueError('Choose controller or processes')
    records = lock[dataset]
    prefix = 'sources/environment-resources/' + dataset + '/'
    files = {}
    for record in records:
        data = (PROJECT / record['file']).read_bytes()
        if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
            raise ValueError('Environment resource checksum mismatch: ' + record['file'])
        files[record['file'].removeprefix(prefix)] = data
    manifest = json.loads(files['manifest.json'])['files']
    for name, data in files.items():
        if name != 'manifest.json' and (len(data) != manifest[name]['bytes'] or
                hashlib.sha256(data).hexdigest() != manifest[name]['sha256']):
            raise ValueError('Source differs from original experiment manifest')
    environment = json.loads(files['results/environment.json'])
    if hashlib.sha256(files['run.py']).hexdigest() != environment['source_sha256']:
        raise ValueError('Measured executable source identity differs')
    return files, records


def sampled_rss(points):
    """Trapezoids between observed timestamps only; never fill unsampled tails."""
    if len(points) < 2 or any(a[0] >= b[0] for a, b in zip(points, points[1:])):
        raise ValueError('Need strictly ordered RSS samples')
    integral = sum(((b[0] - a[0]) * (a[1] + b[1]) / 2 for a, b in zip(points, points[1:])), Fraction())
    return dict(sample_count=len(points), sampled_rss_peak_bytes=max(x[1] for x in points),
                sampled_rss_byte_seconds=float(integral),
                sampled_rss_byte_seconds_recorded_decimal_exact=str(integral),
                rss_sample_window_seconds=float(points[-1][0] - points[0][0]),
                max_sample_gap_seconds=float(max(b[0] - a[0] for a, b in zip(points, points[1:]))))


def finite_lifetimes(intervals, window_start, window_end):
    """Finite completed-cohort occupancy identity, not a steady-state forecast."""
    if not intervals or window_end <= window_start:
        raise ValueError('Positive window and a complete cohort required')
    events = {}
    for start, end in intervals:
        if not window_start <= start <= end <= window_end:
            raise ValueError('Lifetime outside the observation window')
        events[start] = events.get(start, 0) + 1
        events[end] = events.get(end, 0) - 1
    active = peak = 0
    area = Fraction()
    previous = window_start
    for at, change in sorted(events.items()):
        area += active * (at - previous)
        active += change
        peak = max(peak, active)
        if active < 0:
            raise ValueError('Invalid lifecycle event ordering')
        previous = at
    duration_sum = sum((end - start for start, end in intervals), Fraction())
    if active != 0 or area != duration_sum:
        raise ValueError('Completed cohort does not conserve occupied seconds')
    window = window_end - window_start
    rate = Fraction(len(intervals)) / window
    mean_lifetime = duration_sum / len(intervals)
    return dict(cohort_size=len(intervals), peak_observed_lifecycle_count=peak,
                lifecycle_seconds_sum=float(area), mean_lifetime_seconds=float(mean_lifetime),
                observed_completions_per_second=float(rate), average_lifecycle_count=float(area / window),
                average_count_recorded_decimal_exact=str(area / window),
                throughput_times_mean_lifetime_recorded_decimal_exact=str(rate * mean_lifetime),
                finite_cohort_identity_verified=area / window == rate * mean_lifetime)


def controller(files):
    environment = json.loads(files['results/environment.json'])
    if not any('/' + environment['config']['model'].split('/')[-1] + '/' in s['url']
               for s in provenance('qwen3-8b')):
        raise ValueError('Controller model revision differs from the official config')
    rounds = [json.loads(line) for line in files['results/rounds.jsonl'].splitlines()]
    raw_samples = json.loads(files['results/resource-samples.json'])['samples']
    final = json.loads(files['results/final.json'])
    if final['final_code'] != files['results/workspace/intervals.py'].decode():
        raise ValueError('Final task artifact differs')
    if not rounds:
        raise ValueError('Missing model/tool rounds')
    rows = []
    previous = Fraction()
    for index, row in enumerate(rounds):
        start, end, tool_start, tool_end = [number(row[k]) for k in
                                          ('model_start_s', 'model_end_s', 'tool_start_s', 'tool_end_s')]
        if row['turn'] != index or not previous <= start <= end <= tool_start <= tool_end:
            raise ValueError('Model/tool rounds are not a serial measured path')
        if index and (row['messages'][:-2] != rounds[index - 1]['messages'] or
                      row['messages'][-2]['content'] != rounds[index - 1]['output_text'] or
                      row['messages'][-1]['content'] != 'Tool result: ' + json.dumps(rounds[index - 1]['tool_result'])):
            raise ValueError('Agent message history is not continuous')
        rows.append(dict(turn=index, tool=row['action']['tool'],
                         model_wall_seconds=float(end - start), tool_wall_seconds=float(tool_end - tool_start),
                         model_controller_cpu_seconds=float(number(row['model_parent_cpu_s'])),
                         tool_controller_cpu_seconds=float(number(row['tool_parent_cpu_s'])),
                         reaped_tool_cpu_seconds=float(number(row['tool_child_cpu_s'])),
                         scheduler_queue_wait_seconds=None))
        previous = tool_end
    elapsed = number(final['elapsed_s'])
    if previous > elapsed:
        raise ValueError('Loop duration excludes a recorded stage')
    points = []
    old_user = old_system = Fraction()
    for sample in raw_samples:
        at, user, system = [number(sample[k]) for k in ('t_s', 'cpu_user_s', 'cpu_system_s')]
        if at > elapsed or user < old_user or system < old_system or sample['phase'] not in ('model', 'tool', 'control'):
            raise ValueError('Invalid controller sample scope or CPU order')
        rss = number(sample['rss_kib']) * 1024
        if rss.denominator != 1:
            raise ValueError('RSS bytes must be integral')
        points.append((at, int(rss)))
        old_user, old_system = user, system
    stats = sampled_rss(points)
    # Boundary CPU and sampled CPU describe different observation windows.
    phases = []
    for phase in ('model', 'tool', 'control'):
        subset = [r['rss_kib'] * 1024 for r in raw_samples if r['phase'] == phase]
        phases.append(dict(phase=phase, samples=len(subset),
                           sampled_rss_min_bytes=min(subset) if subset else None,
                           sampled_rss_max_bytes=max(subset) if subset else None))
    validation = json.loads(final['validation']['stdout'])
    expected_flags = [c['actual'] == c['expected'] and c['unchanged'] for c in validation['cases']]
    if ([c['passed'] for c in validation['cases']] != expected_flags or
            validation['passed'] != all(expected_flags) or final['validation']['returncode'] != 0):
        raise ValueError('Recorded quality verdict contradicts the independent case predicates')
    model_wall = sum((number(r['model_end_s']) - number(r['model_start_s']) for r in rounds), Fraction())
    tool_wall = sum((number(r['tool_end_s']) - number(r['tool_start_s']) for r in rounds), Fraction())
    cpu = lambda key: sum((number(row[key]) for row in rounds), Fraction())
    sample_cpu = (number(raw_samples[-1]['cpu_user_s']) + number(raw_samples[-1]['cpu_system_s'])
                  - number(raw_samples[0]['cpu_user_s']) - number(raw_samples[0]['cpu_system_s']))
    summary = dict(dataset='controller', rounds=len(rounds), observation_window_seconds=float(elapsed),
                   model_wall_seconds=float(model_wall), tool_wall_seconds=float(tool_wall),
                   other_loop_wall_seconds=float(elapsed - model_wall - tool_wall),
                   model_controller_cpu_seconds=float(cpu('model_parent_cpu_s')),
                   tool_controller_cpu_seconds=float(cpu('tool_parent_cpu_s')),
                   reaped_tool_cpu_seconds=float(cpu('tool_child_cpu_s')),
                   sampled_controller_cpu_delta_seconds=float(sample_cpu),
                   sampled_controller_cpu_average_cores=float(sample_cpu / (points[-1][0] - points[0][0])),
                   rss_unobserved_prefix_seconds=float(points[0][0]),
                   rss_unobserved_suffix_seconds=float(elapsed - points[-1][0]),
                   agent_reported_finished=final['agent_finished'], quality_passed=validation['passed'],
                   visible_cases_passed=sum(expected_flags), visible_cases=len(expected_flags),
                   whole_environment_memory_bytes=None, scheduler_queue_wait_seconds=None,
                   environment_arrival_rate_per_second=None, **stats)
    return summary, dict(environment_rounds=rows, environment_controller_phases=phases)


def processes(files, condition):
    order = json.loads(files['results/order.json'])
    if len(order) != 9:
        raise ValueError('Expected the complete nine-run experiment order')
    # Independent once-through digest; archived worker uses 250000 updates of 256 B.
    digest = hashlib.sha256(b'x' * (250000 * 256)).hexdigest()
    rows, workers = [], []
    identities = set()
    for index, planned in enumerate(order):
        case = json.loads(files[f'results/case{index}.json'])
        if case['index'] != index or any(case[k] != planned[k] for k in ('trial', 'mode', 'arrival')):
            raise ValueError('Run does not match sealed randomized order')
        identity = (case['trial'], case['mode'], case['arrival'])
        if identity in identities:
            raise ValueError('Duplicate trial condition')
        identities.add(identity)
        label = case['mode'] + '-' + case['arrival']
        start, end = number(case['start']), number(case['end'])
        launch = {str(r['pid']): r for r in case['launch']}
        if len(launch) != 4 or set(launch) != set(case['completed']):
            raise ValueError('Four launched and completed process identities must agree')
        lifetime, pending, cpu_values, initialization, execution, exit_observation = [], [], [], [], [], []
        selected = condition == 'all' or condition == label
        for pid, completed in case['completed'].items():
            worker = json.loads(completed['stdout'])
            if completed['returncode'] != 0 or completed['stderr'] or worker['pid'] != int(pid):
                raise ValueError('Worker did not complete with its recorded identity')
            if worker['memory_check'] != 16384 or worker['digest'] != (None if case['mode'] == 'wait' else digest):
                raise ValueError('Worker output or touched-memory check differs')
            scheduled, at = number(launch[pid]['scheduled']), number(launch[pid]['at'])
            ws, ready, we, reaped = (number(worker['start']), number(worker['ready']),
                                      number(worker['end']), number(completed['reaped']))
            if not start <= scheduled <= at <= ws <= ready <= we <= reaped <= end:
                raise ValueError('Process timestamp boundaries are inconsistent')
            lifetime.append((at, reaped)); pending.append((scheduled, at))
            total_cpu, work_cpu = number(worker['cpu_total']), number(worker['cpu_work'])
            if work_cpu > total_cpu:
                raise ValueError('Worker CPU subinterval exceeds process CPU')
            cpu_values.append(total_cpu)
            initialization.append(ready - ws); execution.append(we - ready); exit_observation.append(reaped - we)
            if selected:
                workers.append(dict(run=index, pid=int(pid), condition=label, trial=case['trial'],
                                    scheduled_submission_seconds=float(scheduled - start),
                                    actual_launch_seconds=float(at - start),
                                    planned_submission_delay_seconds=float(at - scheduled),
                                    launch_to_worker_start_seconds=float(ws - at),
                                    initialization_seconds=float(ready - ws), work_wall_seconds=float(we - ready),
                                    end_to_observed_reap_seconds=float(reaped - we),
                                    monitored_lifetime_seconds=float(reaped - at),
                                    recorded_process_cpu_seconds=float(total_cpu), work_cpu_seconds=float(work_cpu),
                                    scheduler_queue_wait_seconds=None))
        points = []
        previous_ticks = {}
        for sample in case['samples']:
            at = number(sample['at'])
            if not start <= at <= end:
                raise ValueError('RSS sample outside the run')
            pids = [str(p['pid']) for p in sample['processes']]
            if len(set(pids)) != len(pids) or not set(pids) <= set(launch):
                raise ValueError('Unknown or duplicate sampled process')
            for process in sample['processes']:
                pid = str(process['pid']); ticks = number(process['cpu_ticks'])
                if ticks < previous_ticks.get(pid, 0):
                    raise ValueError('Process CPU ticks decreased')
                previous_ticks[pid] = ticks
            rss = sum((number(p['rss']) for p in sample['processes']), Fraction())
            if rss.denominator != 1:
                raise ValueError('RSS bytes must be integral')
            points.append((at, int(rss)))
        if selected:
            stats = sampled_rss(points)
            little = finite_lifetimes(lifetime, start, end)
            queue = finite_lifetimes(pending, start, end)
            rows.append(dict(run=index, trial=case['trial'], condition=label,
                             observation_window_seconds=float(end - start),
                             recorded_process_cpu_seconds=float(sum(cpu_values)),
                             observed_cpu_average_cores=float(sum(cpu_values) / (end - start)),
                             initialization_wall_seconds_sum=float(sum(initialization)),
                             work_wall_seconds_sum=float(sum(execution)),
                             end_to_observed_reap_seconds_sum=float(sum(exit_observation)),
                             rss_unobserved_prefix_seconds=float(points[0][0] - start),
                             rss_unobserved_suffix_seconds=float(end - points[-1][0]),
                             planned_submission_delay_seconds_sum=queue['lifecycle_seconds_sum'],
                             average_pending_planned_submissions=queue['average_lifecycle_count'],
                             scheduler_queue_wait_seconds=None, **stats, **little))
    expected = {(trial, mode, arrival) for trial in range(3)
                for mode, arrival in (('wait', 'burst'), ('cpu', 'burst'), ('cpu', 'stagger'))}
    if identities != expected or not rows:
        raise ValueError('Incomplete condition matrix or unknown condition')
    medians = []
    for label in sorted({r['condition'] for r in rows}):
        subset = [r for r in rows if r['condition'] == label]
        metrics = ('observation_window_seconds', 'recorded_process_cpu_seconds', 'sampled_rss_peak_bytes',
                   'sampled_rss_byte_seconds', 'average_lifecycle_count', 'observed_cpu_average_cores')
        medians.append(dict(condition=label, runs=len(subset),
                            **{key: median(r[key] for r in subset) for key in metrics}))
    summary = dict(dataset='processes', condition=condition, verified_runs=9, verified_processes=36,
                   reported_runs=len(rows), reported_processes=len(workers),
                   all_finite_cohort_identities_verified=all(r['finite_cohort_identity_verified'] for r in rows),
                   scheduler_queue_wait_seconds=None, whole_environment_memory_bytes=None,
                   production_arrival_rate_per_second=None, physical_core_utilization=None)
    return summary, dict(environment_process_runs=rows, environment_process_workers=workers,
                          environment_condition_medians=medians)


def calculate(dataset='processes', condition='all'):
    if condition not in ('all', 'wait-burst', 'cpu-burst', 'cpu-stagger') or (dataset == 'controller' and condition != 'all'):
        raise ValueError('Select a recorded process condition; controller supports all only')
    files, sources = read_records(dataset)
    summary, tables = controller(files) if dataset == 'controller' else processes(files, condition)
    return dict(schema_version=1, calculation='environment-resources',
                scenario=dict(dataset=dataset, condition=condition), sources=sources,
                summary=summary, **tables, assumptions=[
                    '本书实验11-1两批真实Linux记录逐文件校验原manifest和独立锁哈希，源码身份绑定environment；CLI仅离线重算，不执行工具、模型或/proc采样。控制器与工具子进程补实验是不同运行，不跨运行相加。',
                    '控制器CPU/RSS仅含控制器与监测、tokenizer、引擎前端；不含活GPU worker或工具子进程RSS。阶段CPU来自process_time边界，回收工具CPU来自RUSAGE_CHILDREN差，样本CPU窗口不同，不要求它们直接相加相等。失败任务照常保留资源量。',
                    '工具补实验9组、每组三轮条件之一和4真实进程；wait是人工sleep，cpu是固定SHA256工作。退出前RUSAGE_SELF总CPU包含启动/导入/分配触页但未涵盖之后打印/退出；不是纯业务CPU或整组所有进程完整CPU。',
                    'RSS只对实际采样点按梯形插值，首样本前与末样本后不补值；峰值只是观测峰值。工具RSS和重复计算共享页，不是PSS/cgroup/整机物理内存；稀疏采样可能漏瞬态。decimal_exact仅保存记录数字的有理算术，不表示时钟或内存测量精确。',
                    '工具生命周期定义为父进程记录launch至观察reaped，包含启动和回收观察延迟；不等于内存真实驻留边界。完整4进程队列用有限窗面积积分核对L=(完成数/窗口)×平均生命周期，所有对象在窗内进入并完成；不从这9组短测量外推稳态Little容量。',
                    '计划提交至实际launch只表示这份脚本的提交延迟，launch至worker_start也包含进程启动，均不能等同OS调度队列等待。真正scheduler queue wait、生产到达率、物理核利用率与完整环境容量没有记录，保留null。',
                    '工具组观察窗含最后监测sleep；CPU核秒除观察墙钟是平均占用核数，不是除以未知核数后的利用率。三次中位数是描述摘要，保留全部run与worker；wait与cpu不同工作，不把其CPU差归因同一优化。',
                    '只有独立CPU工具的实际launch/reaped支持完成队列恒等式；控制器记录没有独立环境队列到达/创建/销毁，未制造环境并发或队列容量。任何真实扩容、预热、暂停恢复与SLO判断均需额外观测。',
                ])
