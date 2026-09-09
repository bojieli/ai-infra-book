"""Official hardware records and strict precision matching for resource bounds."""
import json

from .paths import PROJECT
from .sources import records, read_source
from .units import positive_int, positive_number


def catalog() -> dict:
    result = json.loads((PROJECT / "configs/hardware.json").read_text())
    sources = {row.get("id"): row for row in records() if row.get("id")}
    verified = set()
    identifiers = set()
    for device in result["devices"]:
        if device["id"] in identifiers:
            raise ValueError(f"Duplicate hardware ID: {device['id']}")
        identifiers.add(device["id"])
        for identifier in device["source_ids"]:
            if identifier not in sources:
                raise ValueError(f"Hardware source is not locked: {identifier}")
            if identifier not in verified:
                read_source(sources[identifier]["file"])
                verified.add(identifier)
        validate_device(device)
    return result


def validate_device(device: dict) -> None:
    """Validate field-level provenance, units, and unambiguous selectable peaks."""
    def source(field):
        if field["source_id"] not in device["source_ids"] or not field["locator"]:
            raise ValueError(f"Unverified field source for {device['id']}: {field}")

    if device.get("power_evidence"):
        source(device["power_evidence"])
    if device.get("availability"):
        source(device["availability"])
    if device.get("clock") and device["clock"].get("source_id"):
        source(device["clock"])
    for interface in device.get("interconnects", []):
        source(interface)
    memory = device["memory"]
    source(memory)
    for key in ("capacity_evidence", "bandwidth_evidence"):
        if memory.get(key):
            source(memory[key])
    for evidence in device.get("configuration_evidence", []):
        source(evidence)
        gpu_cores = device.get("gpu_cores", device.get("core_counts", {}).get("gpu"))
        if evidence["gpu_cores"] != gpu_cores or evidence["unified_memory_gb"] != memory["nominal_capacity"]:
            raise ValueError("Host configuration evidence must match the selected GPU bin and memory")
        bandwidth = evidence.get("bandwidth_gb_per_second")
        if bandwidth is not None and bandwidth * 10**9 != memory["bandwidth_bytes_per_second"]:
            raise ValueError("Host configuration bandwidth cannot be taken from another GPU bin")
    if memory["capacity_unit"] != "GB":
        raise ValueError("Nominal hardware capacity must retain the documented GB unit")
    for field in ("nominal_capacity", "bandwidth_bytes_per_second"):
        if memory[field] is not None:
            positive_number(memory[field], field)
    if device["spec_scope"] not in ("single_device", "gpu_aggregate", "npu_aggregate"):
        raise ValueError(f"Unknown hardware resource scope: {device['spec_scope']}")
    aggregate_counts = {"gpu_aggregate": "gpu_count", "npu_aggregate": "npu_count"}
    if device["spec_scope"] in aggregate_counts:
        count_field = aggregate_counts[device["spec_scope"]]
        positive_int(device.get(count_field), count_field)
        if device[count_field] < 2:
            raise ValueError("Accelerator aggregate must identify at least two devices")
        other_field = "npu_count" if count_field == "gpu_count" else "gpu_count"
        if other_field in device:
            raise ValueError("Aggregate must not mislabel GPU and NPU counts")
    choices = set()
    for peak in device["peak_rates"]:
        source(peak)
        if peak.get("clock_evidence"):
            source(peak["clock_evidence"])
        for item in peak.get("supporting_evidence", []):
            source(item)
        positive_number(peak["tera_ops_per_second"], "tera_ops_per_second")
        if peak["sparsity"] not in ("dense", "structured", "unspecified"):
            raise ValueError(f"Unknown sparsity convention: {peak['sparsity']}")
        key = tuple(peak[field] for field in (
            "input_precision", "accumulator_precision", "execution_unit", "sparsity"))
        if key in choices:
            raise ValueError(f"Ambiguous hardware peak for {device['id']}: {key}")
        choices.add(key)
        if peak["input_precision"].startswith("INT") and peak["operation_kind"] == "floating_point":
            raise ValueError("Integer TOPS must not be labelled floating-point FLOPS")


def select_device(identifier: str) -> dict:
    found = [row for row in catalog()["devices"] if row["id"] == identifier]
    if len(found) != 1:
        raise ValueError(f"Unknown hardware ID: {identifier}")
    return found[0]


def select_peak(device: dict, precision: str, accumulator: str,
                execution_unit: str, sparsity: str) -> dict:
    if precision in (None, "unspecified") or execution_unit in (None, "unspecified"):
        raise ValueError("Unspecified input precision or execution unit cannot be used for Roofline")
    if sparsity not in ("dense", "structured"):
        raise ValueError("Unspecified sparsity cannot be used for Roofline")
    if accumulator == "unspecified":
        raise ValueError("Unspecified accumulator cannot be used for a precision-specific Roofline")
    matches = [row for row in device["peak_rates"] if (
        row["input_precision"], row["accumulator_precision"], row["execution_unit"], row["sparsity"]
    ) == (precision, accumulator, execution_unit, sparsity)]
    if len(matches) != 1:
        raise ValueError(f"No verified peak for {device['id']}: {precision}/{accumulator}/{execution_unit}/{sparsity}. Do not substitute another precision or product.")
    if matches[0]["operation_kind"] != "floating_point":
        raise ValueError("Integer TOPS cannot serve as a FLOPs denominator")
    return matches[0]


def roofline(identifier: str, flops: int, traffic_bytes: int, precision: str = "BF16",
             accumulator: str = "FP32", execution_unit: str = "tensor", sparsity: str = "dense",
             sparse_eligible: bool = False, compute_efficiency: float = 1.0,
             bandwidth_efficiency: float = 1.0) -> dict:
    positive_int(flops, "flops")
    positive_int(traffic_bytes, "traffic_bytes")
    for key, value in (("compute_efficiency", compute_efficiency), ("bandwidth_efficiency", bandwidth_efficiency)):
        positive_number(value, key)
        if value > 1:
            raise ValueError(f"{key} must not exceed 1")
    if sparsity == "structured" and not sparse_eligible:
        raise ValueError("Structured sparse peaks require --sparse-eligible and dense-equivalent work; MoE routing is not hardware sparsity")
    device = select_device(identifier)
    peak = select_peak(device, precision, accumulator, execution_unit, sparsity)
    compute = peak["tera_ops_per_second"] * 10**12 * compute_efficiency
    official_bandwidth = device["memory"]["bandwidth_bytes_per_second"]
    if official_bandwidth is None:
        raise ValueError(f"No verified memory bandwidth for {identifier}; do not infer it from another generation")
    bandwidth = official_bandwidth * bandwidth_efficiency
    compute_time, memory_time = flops / compute, traffic_bytes / bandwidth
    source_ids = device["source_ids"]
    sources = [{key: row[key] for key in ("file", "url", "revision", "sha256")}
               for row in records() if row.get("id") in source_ids]
    return {
        "schema_version": 1, "calculation": "roofline", "model": identifier,
        "scenario": {"flops": flops, "traffic_bytes": traffic_bytes, "input_precision": precision,
                     "accumulator_precision": accumulator, "execution_unit": execution_unit,
                     "sparsity": sparsity, "sparse_eligible": sparse_eligible,
                     "compute_efficiency": compute_efficiency, "bandwidth_efficiency": bandwidth_efficiency},
        "selected_peak": peak, "sources": sources,
        "resource_scope": device["spec_scope"], "gpu_count": device.get("gpu_count", 0 if device["spec_scope"] == "npu_aggregate" else 1),
        "npu_count": device.get("npu_count"),
        "summary": {"arithmetic_intensity_flops_per_byte": flops / traffic_bytes,
                    "ridge_point_flops_per_byte": compute / bandwidth,
                    "compute_service_seconds": compute_time, "memory_service_seconds": memory_time,
                    "resource_time_lower_bound_seconds": max(compute_time, memory_time),
                    "throughput_upper_bound_flops_per_second": min(compute, bandwidth * flops / traffic_bytes)},
        "assumptions": [
            "FLOPs 必须与选定单元、输入／累加精度一致；TF32 不是 IEEE FP32，整数 TOPS 不是 FLOPs。",
            "traffic_bytes 必须对应此显存接口的读写服务量；逐算子操作数或逻辑广播字节不能自动当作 HBM。",
            "structured 使用厂商硬件稀疏条件及 dense-equivalent work；MoE 不满足这一条件。",
            "max 是资源下界，不是逐阶段时间之和或任务预测；提交、依赖、非矩阵工作、共享资源与容量另检。",
            "efficiency 是输入假设；1.0 表示官方峰值，较小值不伪装为已测利用率。",
            "gpu_aggregate/npu_aggregate 时 FLOPs/traffic 必须是整组对应加速器 的总工作/接口服务量；聚合下界不检验逐卡容量、放置、通信或负载均衡。",
        ] + device["notes"],
    }


def markdown_catalog(data: dict) -> str:
    lines = ["# 官方硬件输入表（进行中）", "",
             "只使用已锁定官方原件。nominal GB 沿用厂商标签，不能直接视作可分配内存。缺失的 GPU 峰值不以 Neural Engine TOPS 补齐。", "",
             "| ID／型号 | 形态／资源范围 | 名义容量 GB | 显存带宽 GB/s | 官方功率 W（条件见出处） | 规格来源 |",
             "| --- | --- | ---: | ---: | ---: | --- |"]
    locked = {row.get("id"): row for row in records() if row.get("id")}
    for device in data["devices"]:
        memory = device["memory"]
        source = locked[memory["source_id"]]
        bandwidth = memory["bandwidth_bytes_per_second"]
        bandwidth_text = "未知" if bandwidth is None else f"{bandwidth/1e9:g}"
        if device["spec_scope"] == "gpu_aggregate":
            scope = f"{device['gpu_count']} GPU aggregate"
        elif device["spec_scope"] == "npu_aggregate":
            scope = f"{device['npu_count']} NPU aggregate"
        else:
            scope = "single device"
        capacity_evidence = memory.get("capacity_evidence")
        capacity_source_text = ""
        if capacity_evidence:
            capacity_source = locked[capacity_evidence["source_id"]]
            capacity_source_text = f"；容量：[{capacity_evidence['source_id']}]({capacity_source['url']})：{capacity_evidence['locator']}"
        power = device.get("power_watts")
        power_evidence = device.get("power_evidence")
        power_source_text = ""
        if power_evidence:
            power_source = locked[power_evidence["source_id"]]
            power_source_text = f"；功率：[{power_evidence['source_id']}]({power_source['url']})：{power_evidence['locator']}；{power_evidence.get('basis', 'TDP/TGP/可配置上限，非实测')}"
        lines.append(f"| `{device['id']}` — {device['name']} | {device['form_factor']} / {scope} | {memory['nominal_capacity'] if memory['nominal_capacity'] is not None else '未知'} | {bandwidth_text} | {power if power is not None else '未知'} | [{memory['source_id']}]({source['url']})：{memory['locator']}{capacity_source_text}{power_source_text} |")
    lines.extend(["", "以下各行保留输入、累加、执行单元与 sparsity；unspecified 行不参与精度明确的 Roofline。",
                  "累加类型沿用产品表及对应指令的类型契约，不自动保证每一步内部累加的有效精度；有明确限制时在该行来源证据中注明。理论吞吐相同也不证明数值结果等价。", "",
                  "| 型号 ID | 输入 | 累加 | 单元 | 稀疏条件 | Tera-ops/s | 来源／位置与派生依据 |",
                  "| --- | --- | --- | --- | --- | ---: | --- |"])
    for device in data["devices"]:
        for peak in device["peak_rates"]:
            source = locked[peak["source_id"]]
            additional = []
            if peak.get("clock_evidence"):
                clock = peak["clock_evidence"]
                additional.append(f"时钟 {clock.get('gpu_boost_mhz', '未知')}MHz；[{clock['source_id']}]({locked[clock['source_id']]['url']})：{clock['locator']}；{clock.get('boundary', '')}")
            else:
                additional.append("时钟条件：" + peak.get("clock_basis", "未核实"))
            if peak.get("derivation"):
                additional.append(peak["derivation"])
            for item in peak.get("supporting_evidence", []):
                additional.append(f"[{item['source_id']}]({locked[item['source_id']]['url']})：{item['locator']}；{item['claim']}")
            provenance = f"[{peak['source_id']}]({source['url']})：{peak['locator']}"
            if additional:
                provenance += "；" + "；".join(additional)
            lines.append(f"| {device['id']} | {peak['input_precision']} | {peak['accumulator_precision']} | {peak['execution_unit']} | {peak['sparsity']} | {peak['tera_ops_per_second']:g} | {provenance} |")
    lines.extend(["", "型号条件与待核对差异：", ""])
    for device in data["devices"]:
        if device.get("clock"):
            clock = device["clock"]
            lines.append(f"- `{device['id']}` Boost MHz：{clock.get('gpu_boost_mhz', '未知')}；{clock.get('locator', '所查材料未注明')}。Boost不等于持续频率。")
        for interface in device.get("interconnects", []):
            source = locked[interface["source_id"]]
            lines.append(f"- `{device['id']}` {interface['kind']}：{json.dumps({key: value for key, value in interface.items() if key not in ('source_id', 'locator', 'notes')}, ensure_ascii=False)}；[{interface['source_id']}]({source['url']})：{interface['locator']}。")
        for evidence in device.get("configuration_evidence", []):
            source = locked[evidence["source_id"]]
            lines.append(f"- `{device['id']}` 整机适用证据：{evidence['host_model']}，{evidence['gpu_cores']} GPU核／{evidence['unified_memory_gb']}GB；[{evidence['source_id']}]({source['url']})：{evidence['locator']}。其他整机不能仅凭芯片同名外推容量菜单。")
        availability = device.get("availability")
        if availability:
            source = locked[availability["source_id"]]
            lines.append(f"- `{device['id']}` 配置/供应状态（{availability.get('as_of', '日期未核')}）：{availability['status']}；起始日期 {availability.get('available_from') or '未确认'}；窗口 {availability.get('available_window') or '未确认'}；[{availability['source_id']}]({source['url']})：{availability['locator']}。官方配置身份不等于当前现货。")
        for note in device["notes"]:
            lines.append(f"- `{device['id']}`：{note}")
    lines.extend(["", "已审查后保留的未知与版本边界：" + "、".join(data["pending_families"]) + "。", ""])
    return "\n".join(lines)


def audit_catalog(data: dict) -> dict:
    """Expose recording gaps without treating absent values as unpublished facts.

    This structural audit complements the human reading of each official source.
    A source pointer proves traceability, not that the extracted claim is correct.
    """
    rows = []
    for device in data["devices"]:
        memory = device["memory"]
        fields = []
        for name, value, evidence in (
            ("memory_capacity", memory["nominal_capacity"], memory.get("capacity_evidence", memory)),
            ("memory_bandwidth", memory["bandwidth_bytes_per_second"], memory.get("bandwidth_evidence", memory)),
            ("reported_power", device.get("power_watts"), device.get("power_evidence", {})),
        ):
            has_pointer = bool(evidence.get("source_id") and evidence.get("locator"))
            fields.append({
                "field": name, "value": value,
                "recording_status": ("value_and_source_pointer" if value is not None and has_pointer
                                     else "value_without_field_source" if value is not None
                                     else "value_not_recorded"),
                "source_id": evidence.get("source_id"), "locator": evidence.get("locator"),
                "official_disclosure_status": "not_determined_by_structural_audit",
            })
        peaks = []
        for index, peak in enumerate(device["peak_rates"]):
            missing = [key for key in ("input_precision", "accumulator_precision",
                                      "execution_unit", "sparsity")
                       if peak.get(key) in (None, "unspecified")]
            reasons = ["unspecified_" + key for key in missing]
            if peak["operation_kind"] != "floating_point":
                reasons.append("not_floating_point")
            peaks.append({
                "index": index,
                "input_precision": peak["input_precision"],
                "accumulator_precision": peak["accumulator_precision"],
                "execution_unit": peak["execution_unit"], "sparsity": peak["sparsity"],
                "flops_denominator_eligible": not reasons,
                "exclusion_reasons": reasons,
                "source_id": peak["source_id"], "locator": peak["locator"],
                "clock_basis": peak.get("clock_basis"),
                "clock_evidence": peak.get("clock_evidence"),
                "supporting_evidence": peak.get("supporting_evidence", []),
            })
        rows.append({"id": device["id"], "vendor": device["vendor"],
                     "resource_scope": device["spec_scope"], "fields": fields,
                     "clock": device.get("clock"), "interconnects": device.get("interconnects", []),
                     "availability": device.get("availability"),
                     "configuration_evidence": device.get("configuration_evidence", []),
                     "peaks": peaks, "notes_requiring_source_review": device["notes"],
                     "source_claim_review": "not_performed_by_structural_audit"})
    return {
        "schema_version": 1, "calculation": "hardware_recording_audit",
        "scope": "Structural recording and eligibility audit; not official-source claim acceptance",
        "devices": rows,
        "summary": {
            "devices": len(rows), "peak_records": sum(len(row["peaks"]) for row in rows),
            "eligible_floating_point_peaks": sum(p["flops_denominator_eligible"] for row in rows for p in row["peaks"]),
            "values_without_field_source": sum(f["recording_status"] == "value_without_field_source" for row in rows for f in row["fields"]),
            "unrecorded_values": sum(f["recording_status"] == "value_not_recorded" for row in rows for f in row["fields"]),
        },
        "pending_families": data["pending_families"],
        "limitations": [
            "Missing values do not prove official non-disclosure or device non-support.",
            "Selectable floating-point peaks still require matching workload precision, execution unit, scope and sparse eligibility.",
            "A field source pointer does not automatically verify the value, resolve conflicting revisions, or establish availability.",
            "Power, clock, interconnect, on-chip resources and release/availability require their own source review; this report does not exhaust H01–H07.",
        ],
    }


def markdown_audit(data: dict) -> str:
    statuses = {"value_and_source_pointer": "值及来源位置已登记",
                "value_without_field_source": "有值，缺独立来源位置",
                "value_not_recorded": "未录值，原因须人工审查"}
    lines = ["# 硬件字段登记与计算准入审查", "",
             "本表检查登记结构，不自动完成官方资料验收。未录值不代表官方未披露；已登记来源也不等于已解决版本冲突。", "",
             "| 型号 | 容量 | 带宽 | 功率 | 可选浮点峰值／总峰值 |", "| --- | --- | --- | --- | ---: |"]
    for row in data["devices"]:
        state = [statuses[field["recording_status"]] for field in row["fields"]]
        count = sum(p["flops_denominator_eligible"] for p in row["peaks"])
        lines.append(f"| {row['id']} | {' | '.join(state)} | {count}/{len(row['peaks'])} |")
    lines.extend(["", "浮点准入要求已知输入／累加／执行单元／稀疏条件；整数 TOPS 保留为整数记录，不用作 FLOPs 分母。结构化稀疏仍需工作负载满足相应条件。", "",
                  "逐条缺项、峰值拒绝原因和待审注释见同名 JSON。功率、时钟、互联、片上资源和上市状态须引用独立人工验收记录，本结构审计不替代其结论。", ""])
    return "\n".join(lines)
