"""Regenerate currently implemented scenarios, keeping their input manifest visible."""
import hashlib
import re
from pathlib import Path
import json

from . import hardware
from .models import qwen3, forward as model_forward
from .paths import PROJECT
from .report import markdown, operator_csv
from .schema import Scenario
from .sources import verify_sources
from .topics import state, projection, experts, hyper_connections, v4_attention, v4_forward, k3_mla, k3_kda, attn_res, kda_chunk, k3_forward, cache_sequence, resource_basics, memory_concurrency, decode_budget, ring_collective, tree_collective, all_to_all, numa_staging, moe_dedup, capacity_scan, dense_placement, dense_communication, pipeline_schedule, training_matrix, rl_cycle, rl_supply, request_trace, agent_trace, audio_timing, gemm_tiles, row_reduction, bank_mapping, loop_access, fusion_lifetime, quantized_gemm, fusion_numerics, online_softmax, attention_tiles, host_transfer, stream_buffer, graph_execution, optimization_deployment, shape_specialization, runtime_trace, persistent_tasks, request_dag, microbatch_overlap, topology_allocation, collective_paths, periodic_queue, feedback_queue, packet_reorder, collective_tail, connection_states, operation_ordering, completion_reclaim, rpc_trace, remote_state, kv_pages, kv_trace, kv_restore, prefix_value, apc_trace, speculative_round, speculative_sampling, speculative_budget, dflash_work, chunk_history, batch_reuse, iteration_batching, service_replay, gguf_inventory, gguf_layout, kv_codec, weight_offload, kv_quality, pd_af_handoff, pd_pool, expert_locality, grouped_experts, replica_payback, cache_route, router_trace, router_pressure, cache_restart, cache_missing, cache_fault, cache_residency, training_state, gradient_cast, checkpoint_reshard, checkpoint_async, checkpoint_interval, checkpoint_baseline, checkpoint_fault, checkpoint_resume, training_deadline, dense_training_scale, routing_metadata, teacher_cache, weight_handoff, routing_cost, v4_fp8_linear, multimodal_cache, v3_forward, environment_resources, omni_audio, image_generation, video_generation, vision_encoding, retry_paths, vl_request, omni_audio_encoder, nic_budget, omni_vision_encoding, tpu_demand, sequence_dependencies, omni_understanding, environment_lifecycle, ub_scope, training_history, scaling_law, reconfiguration


def input_hashes() -> list[dict]:
    paths = [PROJECT / "calc.py", *sorted((PROJECT / "scenarios").glob("reconfiguration-*.json")), *(PROJECT / row["file"] for row in json.loads((PROJECT / "configs/scaling-law.lock.json").read_text())), *sorted((PROJECT / "scenarios").glob("scaling-law-*.json")), *(PROJECT / row["file"] for row in json.loads((PROJECT / "configs/training-history.lock.json").read_text())), *(PROJECT / row["file"] for row in json.loads((PROJECT / "configs/ub-scope.lock.json").read_text())), *(PROJECT / row["file"] for row in json.loads((PROJECT / "configs/environment-lifecycle.lock.json").read_text())), *(PROJECT / row["file"] for row in json.loads((PROJECT / "configs/tpu-demand.lock.json").read_text())), *(PROJECT / row["file"] for row in json.loads((PROJECT / "configs/nic-history.lock.json").read_text())), *(PROJECT / row["file"] for row in json.loads((PROJECT / "configs/vision-encoding.lock.json").read_text())), *sorted(p for folder in ("sources/image-generation", "research/generative-audio-analysis", "research/generative-video-analysis", "research/generative-media-candidates") for p in (PROJECT / folder).rglob("*") if p.is_file()), *sorted(p for p in (PROJECT / "sources/environment-resources").rglob("*") if p.is_file()), *sorted((PROJECT / "sources/multimodal-cache").glob("*")), *sorted(p for p in (PROJECT / "sources/checkpoint-resume").rglob("*") if p.is_file()), *sorted(p for p in (PROJECT / "sources/checkpoint-fault").rglob("*") if p.is_file()), *sorted(p for p in (PROJECT / "sources/checkpoint-baseline").rglob("*") if p.is_file()), *sorted((PROJECT / "sources/training-state").glob("*")), *sorted(path for path in (PROJECT / "sources/cache-fault").rglob("*") if path.is_file()), *sorted(path for path in (PROJECT / "sources/cache-missing").rglob("*") if path.is_file()), *sorted(path for path in (PROJECT / "sources/cache-restart").rglob("*") if path.is_file()), *sorted(path for path in (PROJECT / "sources/router-pressure").rglob("*") if path.is_file()), *sorted(path for path in (PROJECT / "sources/router-trace").rglob("*") if path.is_file()), *sorted(path for path in (PROJECT / "sources/kv-quality").rglob("*") if path.is_file()), *sorted(path for path in (PROJECT / "sources/gguf-headers").rglob("*") if path.is_file()), *sorted(path for path in (PROJECT / "sources/gguf-qwen235").rglob("*") if path.is_file()), *sorted(path for path in (PROJECT / "sources/service-replay").rglob("*") if path.is_file()), *sorted(path for path in (PROJECT / "sources/chunk-history").rglob("*") if path.is_file()), *sorted(path for path in (PROJECT / "sources/dflash-qwen3-8b").glob("*") if path.is_file()), PROJECT / "scenarios/book.json", *sorted((PROJECT / "configs").glob("*.json")),
             *sorted((PROJECT / "src/infra_calc").rglob("*.py")),
             *sorted((PROJECT / "sources/agent-traces").glob("*/*")),
             *sorted((PROJECT / "sources/cpu-loops").glob("*")),
             *sorted((PROJECT / "sources/runtime-traces").glob("*")),
             *sorted(path for path in (PROJECT / "sources/rpc-traces").rglob("*") if path.is_file()),
             *sorted(path for path in (PROJECT / "sources/kv-traces").rglob("*") if path.is_file()),
             *sorted(path for path in (PROJECT / "sources/apc-traces").rglob("*") if path.is_file()),
             *sorted((PROJECT / "sources/collective-paths").glob("*"))]
    return [{"file": str(path.relative_to(PROJECT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in paths]


def verify_results(include_figures=True) -> dict:
    verify_sources()
    manifest = json.loads((PROJECT / "results/manifest.json").read_text())
    if manifest.get("inputs") != input_hashes():
        raise ValueError("Calculator, source lock, hardware or scenario inputs changed; run reproduce")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("Result manifest must contain a nonempty artifact list")
    names = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict) or not isinstance(artifact.get("file"), str):
            raise ValueError("Invalid result artifact record")
        name = artifact["file"]
        relative = Path(name)
        if name != relative.as_posix() or relative.is_absolute() or ".." in relative.parts or len(relative.parts) < 2 or relative.parts[0] != "results":
            raise ValueError("Result artifact must be a relative path inside results")
        if name in names or not isinstance(artifact.get("sha256"), str) or re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"]) is None:
            raise ValueError("Duplicate or invalid result artifact record")
        names.add(name)
    required = {"results/README.md", "results/hardware.md",
                "results/hardware-audit.json", "results/hardware-audit.md"}
    if not required.issubset(names):
        raise ValueError("Result manifest lacks required core artifacts")
    for artifact in artifacts:
        if hashlib.sha256((PROJECT / artifact["file"]).read_bytes()).hexdigest() != artifact["sha256"]:
            raise ValueError(f"Generated result changed: {artifact['file']}; run reproduce")
    figures = {}
    if include_figures:
        from .specialization_plot import verify
        figures = verify()
        from .collective_plot import verify as verify_collective_figures
        figures["verified_figures"] += verify_collective_figures()["verified_figures"]
        from .vl_plot import verify as verify_vl_figures
        figures["verified_figures"] += verify_vl_figures()["verified_figures"]
    return {"verified_artifacts": len(manifest["artifacts"]), **figures, "scope": manifest["scope"]}


def run() -> dict:
    verify_sources()
    scenario_path = PROJECT / "scenarios/book.json"
    scenarios = json.loads(scenario_path.read_text())
    output = PROJECT / "results"
    output.mkdir(exist_ok=True)
    artifacts = []
    forward_rows, state_rows, projection_rows, expert_rows = [], [], [], []

    def save(name: str, result: dict):
        for extension, text in (("json", json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"),
                                ("md", markdown(result))):
            path = output / (name + "." + extension)
            path.write_text(text)
            artifacts.append(str(path.relative_to(PROJECT)))
        if "operators" in result:
            path = output / (name + ".csv")
            path.write_text(operator_csv(result))
            artifacts.append(str(path.relative_to(PROJECT)))

    for row in scenarios["forward"]:
        result = model_forward(row["model"], Scenario(**{key: value for key, value in row.items() if key not in ("id", "model", "routing", "counts")}), row.get("routing", "balanced"), row.get("counts"))
        save(row["id"], result)
        forward_rows.append((row["id"], result))
    for row in scenarios.get('experts', []):
        result = experts.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        expert_rows.append((row['id'], result))
    hc_rows = []
    for row in scenarios.get('hyper_connections', []):
        result = hyper_connections.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        hc_rows.append((row['id'], result))
    attention_rows = []
    for row in scenarios.get('v4_attention', []):
        result = v4_attention.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        attention_rows.append((row['id'], result))
    v4_rows = []
    for row in scenarios.get('v4_forward', []):
        result = v4_forward.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        v4_rows.append((row['id'], result))
    k3_rows = []
    for row in scenarios.get('k3_forward', []):
        result = k3_forward.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        k3_rows.append((row['id'], result))
    mla_rows = []
    for row in scenarios.get('k3_mla', []):
        result = k3_mla.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        mla_rows.append((row['id'], result))
    kda_rows = []
    for row in scenarios.get('k3_kda', []):
        result = k3_kda.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        kda_rows.append((row['id'], result))
    residual_rows = []
    for row in scenarios.get('attn_res', []):
        result = attn_res.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        residual_rows.append((row['id'], result))
    chunk_rows = []
    for row in scenarios.get('kda_chunk', []):
        result = kda_chunk.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        chunk_rows.append((row['id'], result))
    omni_vision_rows = []
    for row in scenarios.get('omni_vision_encoding', []):
        result = omni_vision_encoding.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        omni_vision_rows.append((row['id'], result))
    understanding_rows = []
    for row in scenarios.get('omni_understanding', []):
        result = omni_understanding.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        understanding_rows.append((row['id'], result))
    dependency_rows = []
    for row in scenarios.get('sequence_dependencies', []):
        result = sequence_dependencies.calculate()
        save(row['id'], result)
        dependency_rows.append((row['id'], result))
    tpu_rows = []
    for row in scenarios.get('tpu_demand', []):
        result = tpu_demand.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        tpu_rows.append((row['id'], result))
    nic_rows = []
    for row in scenarios.get('nic_budget', []):
        result = nic_budget.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        nic_rows.append((row['id'], result))
    input_audio_rows = []
    for row in scenarios.get('omni_audio_encoder', []):
        result = omni_audio_encoder.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        input_audio_rows.append((row['id'], result))
    vl_rows = []
    for row in scenarios.get('vl_request', []):
        result = vl_request.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        vl_rows.append((row['id'], result))
    retry_rows = []
    for row in scenarios.get('retry_paths', []):
        result = retry_paths.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        retry_rows.append((row['id'], result))
    vision_rows = []
    for row in scenarios.get('vision_encoding', []):
        result = vision_encoding.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        vision_rows.append((row['id'], result))
    omni_audio_rows = []
    for row in scenarios.get('omni_audio', []):
        result = omni_audio.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        omni_audio_rows.append((row['id'], result))
    image_rows = []
    for row in scenarios.get('image_generation', []):
        result = image_generation.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        image_rows.append((row['id'], result))
    video_rows = []
    for row in scenarios.get('video_generation', []):
        result = video_generation.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        video_rows.append((row['id'], result))
    v3_rows = []
    for row in scenarios.get('v3_forward', []):
        result = v3_forward.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        v3_rows.append((row['id'], result))
    reconfiguration_rows = []
    for row in scenarios.get('reconfiguration', []):
        result = reconfiguration.calculate(row['inputs'])
        save(row['id'], result)
        reconfiguration_rows.append((row['id'], result))
    scaling_rows = []
    for row in scenarios.get('scaling_law', []):
        result = scaling_law.calculate(json.loads((PROJECT / row['inputs_file']).read_text()))
        save(row['id'], result)
        scaling_rows.append((row['id'], result))
    training_history_rows = []
    for row in scenarios.get('training_history', []):
        result = training_history.calculate(**row.get('inputs', {}))
        save(row['id'], result)
        training_history_rows.append((row['id'], result))
    ub_rows = []
    for row in scenarios.get('ub_scope', []):
        result = ub_scope.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        ub_rows.append((row['id'], result))
    lifecycle_rows = []
    for row in scenarios.get('environment_lifecycle', []):
        result = environment_lifecycle.calculate(**row.get('inputs', {}))
        save(row['id'], result)
        lifecycle_rows.append((row['id'], result))
    environment_rows = []
    for row in scenarios.get('environment_resources', []):
        result = environment_resources.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        environment_rows.append((row['id'], result))
    multimodal_rows = []
    for row in scenarios.get('multimodal_cache', []):
        result = multimodal_cache.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        multimodal_rows.append((row['id'], result))
    v4_fp8_rows = []
    for row in scenarios.get('v4_fp8_linear', []):
        result = v4_fp8_linear.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        v4_fp8_rows.append((row['id'], result))
    routing_cost_rows = []
    for row in scenarios.get('routing_cost', []):
        result = routing_cost.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        routing_cost_rows.append((row['id'], result))
    weight_handoff_rows = []
    for row in scenarios.get('weight_handoff', []):
        result = weight_handoff.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        weight_handoff_rows.append((row['id'], result))
    teacher_cache_rows = []
    for row in scenarios.get('teacher_cache', []):
        result = teacher_cache.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        teacher_cache_rows.append((row['id'], result))
    routing_metadata_rows = []
    for row in scenarios.get('routing_metadata', []):
        result = routing_metadata.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        routing_metadata_rows.append((row['id'],result))
    dense_scale_rows = []
    for row in scenarios.get('dense_training_scale', []):
        result = dense_training_scale.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        dense_scale_rows.append((row['id'],result))
    deadline_rows = []
    for row in scenarios.get('training_deadline', []):
        result = training_deadline.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        deadline_rows.append((row['id'],result))
    resume_rows = []
    for row in scenarios.get('checkpoint_resume', []):
        result = checkpoint_resume.calculate()
        save(row['id'],result)
        resume_rows.append((row['id'],result))
    checkpoint_fault_rows = []
    for row in scenarios.get('checkpoint_fault', []):
        result = checkpoint_fault.calculate()
        save(row['id'],result)
        checkpoint_fault_rows.append((row['id'],result))
    checkpoint_baseline_rows = []
    for row in scenarios.get('checkpoint_baseline', []):
        result = checkpoint_baseline.calculate()
        save(row['id'],result)
        checkpoint_baseline_rows.append((row['id'],result))
    interval_rows = []
    for row in scenarios.get('checkpoint_interval', []):
        result = checkpoint_interval.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        interval_rows.append((row['id'],result))
    async_rows = []
    for row in scenarios.get('checkpoint_async', []):
        result = checkpoint_async.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        async_rows.append((row['id'],result))
    checkpoint_rows = []
    for row in scenarios.get('checkpoint_reshard', []):
        result = checkpoint_reshard.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        checkpoint_rows.append((row['id'],result))
    gradient_cast_rows = []
    for row in scenarios.get('gradient_cast', []):
        result = gradient_cast.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        gradient_cast_rows.append((row['id'],result))
    training_state_rows = []
    for row in scenarios.get('training_state', []):
        result = training_state.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        training_state_rows.append((row['id'],result))
    residency_rows = []
    for row in scenarios.get('cache_residency', []):
        result = cache_residency.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        residency_rows.append((row['id'],result))
    fault_rows = []
    for row in scenarios.get('cache_fault', []):
        result = cache_fault.calculate()
        save(row['id'],result)
        fault_rows.append((row['id'],result))
    missing_rows = []
    for row in scenarios.get('cache_missing', []):
        result = cache_missing.calculate()
        save(row['id'],result)
        missing_rows.append((row['id'],result))
    restart_rows = []
    for row in scenarios.get('cache_restart', []):
        result = cache_restart.calculate()
        save(row['id'],result)
        restart_rows.append((row['id'],result))
    pressure_rows = []
    for row in scenarios.get('router_pressure', []):
        result = router_pressure.calculate()
        save(row['id'],result)
        pressure_rows.append((row['id'],result))
    router_trace_rows = []
    for row in scenarios.get('router_trace', []):
        result = router_trace.calculate(row['policy'])
        save(row['id'],result)
        router_trace_rows.append((row['id'],result))
    cache_route_rows = []
    for row in scenarios.get('cache_route', []):
        result = cache_route.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        cache_route_rows.append((row['id'],result))
    replica_payback_rows = []
    for row in scenarios.get('replica_payback', []):
        result = replica_payback.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        replica_payback_rows.append((row['id'],result))
    grouped_rows = []
    for row in scenarios.get('grouped_experts', []):
        result = grouped_experts.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        grouped_rows.append((row['id'],result))
    locality_rows = []
    for row in scenarios.get('expert_locality', []):
        result = expert_locality.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        locality_rows.append((row['id'],result))
    pd_pool_rows = []
    for row in scenarios.get('pd_pool', []):
        result = pd_pool.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        pd_pool_rows.append((row['id'],result))
    handoff_rows = []
    for row in scenarios.get('pd_af_handoff', []):
        result = pd_af_handoff.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        handoff_rows.append((row['id'],result))
    quality_rows = []
    for row in scenarios.get('kv_quality', []):
        result = kv_quality.calculate(row['run'])
        save(row['id'],result)
        quality_rows.append((row['id'],result))
    offload_rows = []
    for row in scenarios.get('weight_offload', []):
        result = weight_offload.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        offload_rows.append((row['id'],result))
    codec_rows = []
    for row in scenarios.get('kv_codec', []):
        result = kv_codec.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        codec_rows.append((row['id'],result))
    gguf_layout_rows = []
    for row in scenarios.get('gguf_layout', []):
        result = gguf_layout.calculate(row['variant'])
        save(row['id'],result)
        gguf_layout_rows.append((row['id'],result))
    gguf_rows = []
    for row in scenarios.get('gguf_inventory', []):
        result = gguf_inventory.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        gguf_rows.append((row['id'],result))
    service_rows = []
    for row in scenarios.get('service_replay', []):
        result = service_replay.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        service_rows.append((row['id'],result))
    iteration_rows = []
    for row in scenarios.get('iteration_batching', []):
        result = iteration_batching.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        iteration_rows.append((row['id'],result))
    batch_reuse_rows = []
    for row in scenarios.get('batch_reuse', []):
        result = batch_reuse.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        batch_reuse_rows.append((row['id'],result))
    chunk_history_rows = []
    for row in scenarios.get('chunk_history', []):
        result = chunk_history.calculate()
        save(row['id'],result)
        chunk_history_rows.append((row['id'],result))
    dflash_rows = []
    for row in scenarios.get('dflash_work', []):
        result = dflash_work.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        dflash_rows.append((row['id'],result))
    budget_policy_rows = []
    for row in scenarios.get('speculative_budget', []):
        result = speculative_budget.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        budget_policy_rows.append((row['id'],result))
    sampling_rows = []
    for row in scenarios.get('speculative_sampling', []):
        result = speculative_sampling.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        sampling_rows.append((row['id'],result))
    speculative_rows = []
    for row in scenarios.get('speculative_round', []):
        result = speculative_round.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        speculative_rows.append((row['id'],result))
    apc_rows = []
    for row in scenarios.get('apc_trace', []):
        result = apc_trace.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        apc_rows.append((row['id'],result))
    prefix_rows = []
    for row in scenarios.get('prefix_value', []):
        result = prefix_value.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        prefix_rows.append((row['id'],result))
    restore_rows = []
    for row in scenarios.get('kv_restore', []):
        result = kv_restore.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        restore_rows.append((row['id'],result))
    kv_trace_rows = []
    for row in scenarios.get('kv_trace', []):
        result = kv_trace.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        kv_trace_rows.append((row['id'],result))
    page_rows = []
    for row in scenarios.get('kv_pages', []):
        result = kv_pages.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        page_rows.append((row['id'],result))
    remote_rows = []
    for row in scenarios.get('remote_state', []):
        result = remote_state.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        remote_rows.append((row['id'],result))
    rpc_rows = []
    for row in scenarios.get('rpc_trace', []):
        result = rpc_trace.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        rpc_rows.append((row['id'],result))
    reclaim_rows = []
    for row in scenarios.get('completion_reclaim', []):
        result = completion_reclaim.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        reclaim_rows.append((row['id'],result))
    ordering_rows = []
    for row in scenarios.get('operation_ordering', []):
        result = operation_ordering.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        ordering_rows.append((row['id'],result))
    connection_rows = []
    for row in scenarios.get('connection_states', []):
        result = connection_states.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        connection_rows.append((row['id'],result))
    tail_rows = []
    for row in scenarios.get('collective_tail', []):
        result = collective_tail.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        tail_rows.append((row['id'],result))
    packet_rows = []
    for row in scenarios.get('packet_reorder', []):
        result = packet_reorder.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        packet_rows.append((row['id'],result))
    feedback_rows = []
    for row in scenarios.get('feedback_queue', []):
        result = feedback_queue.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        feedback_rows.append((row['id'],result))
    queue_rows = []
    for row in scenarios.get('periodic_queue', []):
        result = periodic_queue.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        queue_rows.append((row['id'],result))
    path_rows = []
    for row in scenarios.get('collective_paths', []):
        result = collective_paths.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        path_rows.append((row['id'],result))
    allocation_rows = []
    for row in scenarios.get('topology_allocation', []):
        result = topology_allocation.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        allocation_rows.append((row['id'],result))
    overlap_rows = []
    for row in scenarios.get('microbatch_overlap', []):
        result = microbatch_overlap.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        overlap_rows.append((row['id'],result))
    dag_rows = []
    for row in scenarios.get('request_dag', []):
        result = request_dag.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        dag_rows.append((row['id'],result))
    persistent_rows = []
    for row in scenarios.get('persistent_tasks', []):
        result = persistent_tasks.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        persistent_rows.append((row['id'],result))
    runtime_rows = []
    for row in scenarios.get('runtime_trace', []):
        result = runtime_trace.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        runtime_rows.append((row['id'],result))
    specialization_rows = []
    for row in scenarios.get('shape_specialization', []):
        result = shape_specialization.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        specialization_rows.append((row['id'],result))
    deployment_rows = []
    for row in scenarios.get('optimization_deployment', []):
        result = optimization_deployment.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        deployment_rows.append((row['id'],result))
    graph_rows = []
    for row in scenarios.get('graph_execution', []):
        result = graph_execution.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        graph_rows.append((row['id'],result))
    fifo_rows = []
    for row in scenarios.get('stream_buffer', []):
        result = stream_buffer.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        fifo_rows.append((row['id'],result))
    host_rows = []
    for row in scenarios.get('host_transfer', []):
        result = host_transfer.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        host_rows.append((row['id'],result))
    attention_tile_rows = []
    for row in scenarios.get('attention_tiles', []):
        result = attention_tiles.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        attention_tile_rows.append((row['id'],result))
    softmax_rows = []
    for row in scenarios.get('online_softmax', []):
        result = online_softmax.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        softmax_rows.append((row['id'],result))
    numeric_rows = []
    for row in scenarios.get('fusion_numerics', []):
        result = fusion_numerics.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        numeric_rows.append((row['id'],result))
    quant_rows = []
    for row in scenarios.get('quantized_gemm', []):
        result = quantized_gemm.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        quant_rows.append((row['id'],result))
    fusion_rows = []
    for row in scenarios.get('fusion_lifetime', []):
        result = fusion_lifetime.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        fusion_rows.append((row['id'],result))
    loop_rows = []
    for row in scenarios.get('loop_access', []):
        result = loop_access.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        loop_rows.append((row['id'],result))
    bank_rows = []
    for row in scenarios.get('bank_mapping', []):
        result = bank_mapping.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        bank_rows.append((row['id'],result))
    reduction_rows = []
    for row in scenarios.get('row_reduction', []):
        result = row_reduction.calculate(**{key:value for key,value in row.items() if key != 'id'})
        save(row['id'],result)
        reduction_rows.append((row['id'],result))
    tile_rows = []
    for row in scenarios.get('gemm_tiles', []):
        result = gemm_tiles.calculate(**{key: value for key,value in row.items() if key != 'id'})
        save(row['id'], result)
        tile_rows.append((row['id'], result))
    audio_rows = []
    for row in scenarios.get('audio_timing', []):
        result = audio_timing.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        audio_rows.append((row['id'], result))
    agent_rows = []
    for row in scenarios.get('agent_trace', []):
        result = agent_trace.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        agent_rows.append((row['id'], result))
    trace_rows = []
    for row in scenarios.get('request_trace', []):
        result = request_trace.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        trace_rows.append((row['id'], result))
    supply_rows = []
    for row in scenarios.get('rl_supply', []):
        result = rl_supply.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        supply_rows.append((row['id'], result))
    rl_rows = []
    for row in scenarios.get('rl_cycle', []):
        result = rl_cycle.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        rl_rows.append((row['id'], result))
    training_rows = []
    for row in scenarios.get('training_matrix', []):
        result = training_matrix.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        training_rows.append((row['id'], result))
    pipeline_rows = []
    for row in scenarios.get('pipeline_schedule', []):
        result = pipeline_schedule.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        pipeline_rows.append((row['id'], result))
    communication_rows = []
    for row in scenarios.get('dense_communication', []):
        result = dense_communication.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        communication_rows.append((row['id'], result))
    placement_rows = []
    for row in scenarios.get('dense_placement', []):
        result = dense_placement.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        placement_rows.append((row['id'], result))
    capacity_rows = []
    for row in scenarios.get('capacity_scan', []):
        result = capacity_scan.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        capacity_rows.append((row['id'], result))
    dedup_rows = []
    for row in scenarios.get('moe_dedup', []):
        result = moe_dedup.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        dedup_rows.append((row['id'], result))
    staging_rows = []
    for row in scenarios.get('numa_staging', []):
        result = numa_staging.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        staging_rows.append((row['id'], result))
    exchange_rows = []
    for row in scenarios.get('all_to_all', []):
        result = all_to_all.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        exchange_rows.append((row['id'], result))
    tree_rows = []
    for row in scenarios.get('tree_collective', []):
        result = tree_collective.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        tree_rows.append((row['id'], result))
    ring_rows = []
    for row in scenarios.get('ring_collective', []):
        result = ring_collective.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        ring_rows.append((row['id'], result))
    budget_rows = []
    for row in scenarios.get('decode_budget', []):
        result = decode_budget.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        budget_rows.append((row['id'], result))
    window_rows = []
    for row in scenarios.get('memory_concurrency', []):
        result = memory_concurrency.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        window_rows.append((row['id'], result))
    basics_rows = []
    for row in scenarios.get('resource_basics', []):
        result = resource_basics.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        basics_rows.append((row['id'], result))
    sequence_rows = []
    for row in scenarios.get('cache_sequence', []):
        result = cache_sequence.calculate(**{key: value for key, value in row.items() if key != 'id'})
        save(row['id'], result)
        sequence_rows.append((row['id'], result))
    for row in scenarios["states"]:
        result = state.calculate(**row)
        name = f"state-{row['model']}-n{row['length']}-b{row.get('batch', 1)}-{row.get('mla_path', 'native')}"
        save(name, result)
        state_rows.append((name, result))
    for row in scenarios["generation"]:
        save(f"generation-{row['model']}-s{row['history']}-g{row['steps']}", qwen3.generation(**row))
    for row in scenarios.get("projection_bounds", []):
        result = projection.calculate(**{key: value for key, value in row.items() if key != "id"})
        save(row["id"], result)
        projection_rows.append((row["id"], result))
    (output / "hardware.md").write_text(hardware.markdown_catalog(hardware.catalog()))
    artifacts.append("results/hardware.md")
    hardware_audit = hardware.audit_catalog(hardware.catalog())
    (output / "hardware-audit.json").write_text(json.dumps(hardware_audit, ensure_ascii=False, indent=2) + "\n")
    (output / "hardware-audit.md").write_text(hardware.markdown_audit(hardware_audit))
    artifacts.extend(["results/hardware-audit.json", "results/hardware-audit.md"])


    lines = ["# 已实现计算的结果索引", "", "由 `python3 calculations/calc.py reproduce` 生成；全书未完成项见 [计划](../PLAN.md)。", "",
             "所有值是固定输入的分析结果。矩阵 FLOPs 包含选定输出头，不把特殊函数折算为矩阵吞吐。", "",
             "| 场景 | 矩阵 TFLOPs | 权重 GiB | KV 结束时 GiB | 新写 KV GiB |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for name, result in forward_rows:
        summary = result["summary"]
        lines.append(f"| [{name}]({name}.md) | {summary['matrix_flops']/1e12:.9f} | {summary['weight_resident_bytes']/2**30:.9f} | {summary['kv_resident_after_bytes']/2**30:.9f} | {summary['kv_new_write_bytes']/2**30:.9f} |")
    lines.extend(["", "MoE 路由是显式场景输入；专家权重载荷按每层访问的专家并集计，不能当作实测 HBM。每专家矩阵见各场景明细。", "",
                  "| 场景 | 每层分派数 | 每层专家并集 | 专家矩阵 TFLOPs | 专家权重载荷 GiB |",
                  "| --- | ---: | ---: | ---: | ---: |"])
    for name, result in forward_rows:
        summary = result['summary']
        if 'expert_union_per_layer' in summary:
            lines.append(f"| [{name}]({name}.md) | {summary['expert_assignments_per_layer']} | {summary['expert_union_per_layer']} | {summary['routed_expert_matrix_flops']/1e12:.9f} | {summary['routed_expert_unique_weight_payload_bytes']/2**30:.9f} |")
    lines.extend(['', 'V4／K3 的 FFN 矩阵台账单列，尚非完整前向。统一 2-byte 对照载荷不代表实际混合量化格式。', '',
                  '| 场景 | FFN 矩阵 TFLOPs | routed TFLOPs | shared TFLOPs | latent TFLOPs | dense 首层 TFLOPs |',
                  '| --- | ---: | ---: | ---: | ---: | ---: |'])
    for name, result in expert_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['ffn_matrix_flops']/1e12:.9f} | {s['routed_matrix_flops']/1e12:.9f} | {s['shared_matrix_flops']/1e12:.9f} | {s['latent_matrix_flops']/1e12:.9f} | {s['dense_matrix_flops']/1e12:.9f} |")
    lines.extend(['', 'V4 mHC 独立子账（不含注意力／专家／词表头）：', '',
                  '| 场景 | 混合投影 GFLOPs | 普通算术 GFLOPs | mHC FP32 参数 MiB |',
                  '| --- | ---: | ---: | ---: |'])
    for name, result in hc_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['matrix_flops']/1e9:.6f} | {s['scalar_flops']/1e9:.6f} | {s['hc_fp32_parameter_bytes']/2**20:.6f} |")
    lines.extend(['', 'V4 注意力矩阵子账：投影、有效 QK/PV 与参考实现矩形索引点积分别计量。', '',
                  '| 场景 | 投影 TFLOPs | 有效 QK/PV TFLOPs | 参考索引 TFLOPs |',
                  '| --- | ---: | ---: | ---: |'])
    for name, result in attention_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['projection_matrix_flops']/1e12:.6f} | {s['effective_qk_pv_matrix_flops']/1e12:.6f} | {s['reference_index_matrix_flops']/1e12:.6f} |")
    lines.extend(['', 'V4 基础前向汇总：完整混合存储／访存仍未知，coverage 列明缺项；矩阵总数不可直接当时延。', '',
                  '| 场景 | 有效注意力口径 TFLOPs | 已知稀疏／专家 tile 口径 TFLOPs | 基础逻辑参数 |',
                  '| --- | ---: | ---: | ---: |'])
    for name, result in v4_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['matrix_flops_effective_attention']/1e12:.6f} | {s['matrix_flops_with_reference_sparse_and_expert_tiles']/1e12:.6f} | {s['logical_parameters_excluding_mtp_and_quant_scales']:,} |")
    lines.extend(['', 'Kimi K3 文本前向：有效因果 MLA，递推或块式 KDA 数学口径；实际量化／后端工作仍见 coverage。', '',
                  '| 场景 | 矩阵 TFLOPs | 逻辑文本参数 | 持久状态 MiB |', '| --- | ---: | ---: | ---: |'])
    for name, result in k3_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['matrix_flops']/1e12:.6f} | {s['logical_text_parameters']:,} | {s['state_resident_after_bytes']/2**20:.6f} |")
    lines.extend(['', 'Kimi K3 MLA 两路径：compact 为代数替代方案，expanded 为固定 HF 缓存路径。', '',
                  '| 场景 | 投影 TFLOPs | 有效注意力 TFLOPs | MLA 缓存 MiB |', '| --- | ---: | ---: | ---: |'])
    for name, result in mla_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['projection_matrix_flops']/1e12:.6f} | {s['valid_attention_matrix_flops']/1e12:.6f} | {s['kv_resident_after_bytes']/2**20:.6f} |")
    lines.extend(['', 'Kimi K3 KDA：投影和递推数学基线，T>1 不是实际 chunk kernel 工作。', '',
                  '| 场景 | 投影 TFLOPs | 递推等普通算术 GFLOPs | FP32 状态 MiB |', '| --- | ---: | ---: | ---: |'])
    for name, result in kda_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['projection_matrix_flops']/1e12:.6f} | {s['recurrent_and_other_scalar_flops']/1e9:.6f} | {s['recurrent_state_fp32_bytes']/2**20:.6f} |")
    lines.extend(['', 'Kimi K3 AttnRes：块堆栈仅在一次 forward 内随深度保留，不是跨 token KV。', '',
                  '| 场景 | 加权矩阵 GFLOPs | 普通算术 GFLOPs | 最后块堆栈 MiB |', '| --- | ---: | ---: | ---: |'])
    for name, result in residual_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['weighted_sum_matrix_flops']/1e9:.6f} | {(s['mixing_scalar_flops']+s['prefix_accumulation_scalar_flops'])/1e9:.6f} | {s['final_saved_block_stack_bytes']/2**20:.6f} |")
    lines.extend(['', 'KDA chunk 的已确认存活子集：不含所有输入／工作区，不是完整峰值。', '',
                  '| 场景 | 每层 chunk state MiB | 已知存活子集最大 MiB |', '| --- | ---: | ---: |'])
    for name, result in chunk_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['per_layer_chunk_state_bytes']/2**20:.6f} | {s['known_live_subset_max_bytes']/2**20:.6f} |")
    lines.extend(['', '整段生成缓存：历史逻辑读取／追加写入／最终容量分别计量，非实际 HBM。', '',
                  '| 场景 | 累计旧历史读取 GiB | 累计追加 GiB | 最终持久状态 GiB |', '| --- | ---: | ---: | ---: |'])
    for name, result in sequence_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['decode_prior_history_read_payload_bytes']/2**30:.6f} | {s['decode_append_write_bytes']/2**30:.6f} | {s['final_persistent_state_bytes']/2**30:.6f} |")
    lines.extend(['', '第 1 章教学单位与容量：不是某个真实 checkpoint 的部署证明。', '',
                  '| 场景 | 权重 GB | 权重 GiB | 总容量够 | 每卡预算够 | 串行传输模型 ms |',
                  '| --- | ---: | ---: | --- | --- | ---: |'])
    for name, result in basics_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['weight_payload_GB']:.6f} | {s['weight_payload_GiB']:.6f} | {s['aggregate_capacity_sufficient']} | {s['every_card_fits_declared_budget']} | {s['modeled_serial_transfer_seconds']*1000:.6f} |")
    lines.extend(['', '独立访存窗口：同一 Qwen KV 载荷，接口／延迟／事务并发均为声明的教学条件。', '',
                  '| 场景 | 所需事务数 | 吞吐上界 GB/s | KV 服务下界 ms |', '| --- | ---: | ---: | ---: |'])
    for name, result in window_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['required_transactions']} | {s['effective_bandwidth_upper_bytes_per_second']/1e9:.6f} | {s['window_constrained_service_lower_seconds']*1000:.6f} |")
    lines.extend(['', '70B 初步解码预算：声明存储位宽与 BF16 计算分开，容量失败不输出可运行下界。', '',
                  '| 场景 | 计算服务 ms | 内存服务 ms | 声明预算可容纳 | 交叉 batch |', '| --- | ---: | ---: | --- | ---: |'])
    for name, result in budget_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['compute_service_seconds']*1000:.6f} | {s['memory_service_seconds']*1000:.6f} | {s['fits_declared_budget']} | {s['compute_memory_crossover_batch']} |")
    lines.extend(['', 'Qwen Dense ring：独立有向边、串行 2L 次归约的教学预算。', '',
                  '| 场景 | 每 rank 消息 bytes | 每 rank 发送 bytes | 每次 μs | 2L 次 ms |', '| --- | ---: | ---: | ---: | ---: |'])
    for name, result in ring_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['message_bytes_per_rank']} | {s['all_reduce_send_bytes_per_rank']} | {s['all_reduce_modeled_seconds']*1e6:.6f} | {s['dense_tp_serial_collective_seconds']*1000:.6f} |")
    lines.extend(['', '未分段 binomial tree：与 ring 同输入，独立比较轮次、最忙 rank 与关键路径。', '',
                  '| 场景 | 轮次 | 全网发送 bytes | 最多 rank 发送 bytes | 每次 μs |', '| --- | ---: | ---: | ---: | ---: |'])
    for name, result in tree_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['all_reduce_rounds']} | {s['all_reduce_network_send_bytes']} | {s['maximum_rank_send_bytes']} | {s['all_reduce_modeled_seconds']*1e6:.6f} |")
    lines.extend(['', 'MoE assignment all-to-all：无目的端去重，源—目的计数明确。', '',
                  '| 场景 | Dispatch bytes | 最大 rank 接收 bytes | Dispatch μs |', '| --- | ---: | ---: | ---: |'])
    for name, result in exchange_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['dispatch_network_send_bytes']} | {s['dispatch_maximum_receive_bytes']} | {s['dispatch_pairwise_modeled_seconds']*1e6:.6f} |")
    lines.extend(['', 'PCIe／NUMA 中转：逻辑消息不变，逐物理资源载荷随放置变化。', '',
                  '| 场景 | 逻辑发送 MiB | 聚合资源下界 ms | 逐轮资源下界之和 ms |', '| --- | ---: | ---: | ---: |'])
    for name, result in staging_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['logical_send_bytes']/2**20:.6f} | {s['aggregate_resource_lower_seconds']*1000:.6f} | {s['sum_round_resource_lower_seconds']*1000:.6f} |")
    lines.extend(['', 'MoE 目的端去重：显式 token 路由决定复用，不从汇总直方图猜测。', '',
                  '| 场景 | 原 dispatch bytes | 去重 dispatch bytes | 原 combine bytes | 目的端合并返回 bytes |', '| --- | ---: | ---: | ---: | ---: |'])
    for name, result in dedup_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['per_assignment_dispatch_bytes']} | {s['deduplicated_dispatch_bytes']} | {s['per_assignment_combine_bytes']} | {s['destination_combined_return_bytes']} |")
    lines.extend(['', '实际权重形状的单设备容量扫描：低位宽是声明的存储方案，非实际部署保证。', '',
                  '| 场景 | BF16 权重 GiB | 8-bit 方案 GiB | 4-bit 方案 GiB | 每请求 KV GiB |', '| --- | ---: | ---: | ---: | ---: |'])
    for name, result in capacity_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['bf16_weight_bytes']/2**30:.6f} | {s['eight_bit_scheme_bytes']/2**30:.6f} | {s['four_bit_scheme_bytes']/2**30:.6f} | {s['bf16_kv_bytes_per_request']/2**30:.6f} |")
    lines.extend(['', 'Dense 逐卡 TP/PP/DP：参数复制、KV 头身份和首尾阶段单独处理。', '',
                  '| 场景 | 卡数 | 物理权重 GiB | 最大单卡驻留 GiB | 全卡声明预算够放 |', '| --- | ---: | ---: | ---: | --- |'])
    for name, result in placement_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['cards']} | {s['physical_weight_bytes']/2**30:.6f} | {s['maximum_card_resident_bytes']/2**30:.6f} | {s['all_cards_fit_declared_budget']} |")
    lines.extend(['', 'Dense 完整基础通信路径：嵌入、层输出、PP、最后 logits、token 回传；非完整迭代时延。', '',
                  '| 场景 | 每副本发送 bytes | 启动 ms | 带宽 ms | 串行通信模型 ms |', '| --- | ---: | ---: | ---: | ---: |'])
    for name, result in communication_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['network_send_bytes_per_replica']} | {s['startup_seconds']*1000:.6f} | {s['bandwidth_seconds']*1000:.6f} | {s['serial_communication_path_seconds']*1000:.6f} |")
    lines.extend(['', 'FIFO 生成流水：耗时为显式输入，反馈依赖与边界缓冲分别调度。', '',
                  '| 场景 | 首完成 ms | 全部完成 ms | 边界缓冲存活峰值 bytes |', '| --- | ---: | ---: | ---: |'])
    for name, result in pipeline_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['first_completion_ns']/1e6:.6f} | {s['finish_ns']/1e6:.6f} | {s['declared_boundary_buffer_peak_bytes']} |")
    lines.extend(['', 'Dense 训练矩阵子账：有效因果工作、6ND 与监督 mask 分列。', '',
                  '| 场景 | 训练矩阵 TFLOPs | 6ND TFLOPs | 输出头行数 | 参数状态 GiB |', '| --- | ---: | ---: | ---: | ---: |'])
    for name, result in training_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['training_matrix_flops']/1e12:.6f} | {s['six_nd_flops']/1e12:.6f} | {s['executed_head_rows']} | {s['unsharded_parameter_state_bytes']/2**30:.6f} |")
    lines.extend(['', 'RL 同一候选／有效样本批次：矩阵工作与权重交接，非完整周期时延。', '',
                  '| 场景 | 候选 | 接受 | 周期矩阵 TFLOPs | 每有效样本 TFLOPs |', '| --- | ---: | ---: | ---: | ---: |'])
    for name, result in rl_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['generated_samples']} | {s['accepted_samples']} | {s['cycle_matrix_flops']/1e12:.6f} | {s['matrix_flops_per_accepted_sample']/1e12:.6f} |")
    lines.extend(['', 'RL 显式供给情景：共享池需求相加，流水上界不保证可实现。', '',
                  '| 场景 | 串行组件 s | 理想流水间隔下界 s | 限制池 |', '| --- | ---: | ---: | --- |'])
    for name, result in supply_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['serial_component_batch_seconds']:.6f} | {s['ideal_pipeline_interval_lower_seconds']:.6f} | {s['limiting_pools']} |")
    lines.extend(['', '成对请求轨迹：服务时长显式输入，FIFO 等待与 KV 存活复算。', '',
                  '| 场景 | 平均输入 | 平均输出 | p95 延迟 ms | KV 峰值 MiB |', '| --- | ---: | ---: | ---: | ---: |'])
    for name, result in trace_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['mean_prompt_tokens']} | {s['mean_output_tokens']} | {s['p95_latency_ns']/1e6:.6f} | {s['kv_peak_bytes']/2**20:.6f} |")
    lines.extend(['', '真实 Agent 轨迹复算：模型墙钟与条件式替换，保留任务质量差异。', '',
                  '| 场景 | 轮数 | 实际总秒数 | 替换后条件秒数 | 原任务检查通过数 |', '| --- | ---: | ---: | ---: | ---: |'])
    for name, result in agent_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['turns']} | {s['measured_elapsed_seconds']:.6f} | {s['counterfactual_elapsed_seconds']:.6f} | {s['value_and_input_passed']}/{s['evaluation_cases']} |")
    lines.extend(['', '实时音频教学时序：固定截止、实际停顿、抖动缓冲与静音响应分列。', '',
                  '| 场景 | 首次播放 ms | 截止未到块数 | 新增停顿 ms | ready queue bytes |', '| --- | ---: | ---: | ---: | ---: |'])
    for name, result in audio_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['first_playback_from_time_zero_ns']/1e6:.6f} | {s['deadline_misses']} | {s['total_playback_stall_ns']/1e6:.6f} | {s['baseline_ready_queue_peak_bytes']} |")
    lines.extend(['', 'Qwen 单支投影分块：候选内最小接口流量，不是 HBM 测量或性能最优。', '',
                  '| 场景 | 可行候选 | 选中 m/k/n | 下一层 bytes |', '| --- | ---: | --- | ---: |'])
    for name, result in tile_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['feasible_candidates']} | {s['best_enumerated_tile']} | {s['best_enumerated_next_level_bytes']} |")
    lines.extend(['', 'RMSNorm 分片归约：额外输入重读、partial／inverse 与组数，非加速保证。', '',
                  '| 场景 | D | partial bytes | 额外接口 bytes |', '| --- | ---: | ---: | ---: |'])
    for name,result in reduction_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['width']} | {s['partial_buffer_bytes']} | {s['additional_interface_bytes']} |")
    lines.extend(['', '标量 bank 服务：padding／广播只在声明的请求与端口模型下比较。', '',
                  '| 场景 | 分配 bytes | 请求 bytes | 服务轮数 |', '| --- | ---: | ---: | ---: |'])
    for name,result in bank_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['allocated_tile_bytes']} | {s['lane_requested_bytes']} | {s['service_rounds']} |")
    lines.extend(['', '小矩阵 C 源码数组访问：匹配原实验记录，编译器／缓存流量不推断。', '',
                  '| 场景 | FLOPs | 候选 | 匹配实测候选 |', '| --- | ---: | ---: | ---: |'])
    for name,result in loop_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['mathematical_flops']} | {s['candidates']} | {s['candidates_with_recorded_samples']} |")
    lines.extend(['', '点式融合链：完整中间张量物化与生命周期，实际局部scratch另计。', '',
                  '| 场景 | 分开接口 bytes | 融合接口 bytes | 分开张量峰值 bytes | 融合张量峰值 bytes |', '| --- | ---: | ---: | ---: | ---: |'])
    for name,result in fusion_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['separate_interface_bytes']} | {s['fused_interface_bytes']} | {s['separate_tensor_peak_bytes']} | {s['fused_tensor_peak_bytes']} |")
    lines.extend(['', '量化融入专家 GEMM：宽输入重读与前缀尺度语义分开。', '',
                  '| 场景 | 独立量化 MiB | 全行尺度融合 MiB | 前缀尺度融合 MiB |', '| --- | ---: | ---: | ---: |'])
    for name,result in quant_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['separate_main_bytes']/2**20:.6f} | {s['full_scale_fused_main_bytes']/2**20:.6f} | {s['prefix_scale_fused_main_bytes']/2**20:.6f} |")
    lines.extend(['', '融合数值反例：精确FP8舍入与不可恢复的局部状态。', '',
                  '| 场景 | 整行输出 | 前缀输出 | 精确差值 | FP16后相等 |', '| --- | --- | --- | --- | --- |'])
    for name,result in numeric_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['full_row_exact']} | {s['prefix_exact']} | {s['exact_difference']} | {s['equal_after_fp16']} |")
    lines.extend(['', '在线Softmax状态：顺序／树形合并与错误等权平均对照。', '',
                  '| 场景 | 直接输出 | 顺序误差 | 等权平均误差 |', '| --- | --- | ---: | ---: |'])
    for name,result in softmax_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['direct_output']} | {s['sequential_max_abs_error']} | {s['naive_mean_max_abs_error']} |")
    lines.extend(['', '单头注意力分块：显式容量排布、KV扫描、因果边界与循环缩放。', '',
                  '| 场景 | 有效矩阵 FLOPs | 可行候选 | 候选最少接口 bytes |', '| --- | ---: | ---: | ---: |'])
    for name,result in attention_tile_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['valid_matrix_flops']} | {s['feasible_candidates']} | {s['best_enumerated_interface_bytes']} |")
    lines.extend(['', 'VL请求阶段连接：视觉编码、语言prefill、增长历史decode。', '', '| 场景 | 总矩阵FLOPs | prompt位置 | decode调用 | 最后KV bytes |', '| --- | ---: | ---: | ---: | ---: |'])
    for name, result in vl_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['total_matrix_flops']} | {s['prompt_positions']} | {s['decode_forward_calls']} | {s['final_kv_bytes']} |")
    lines.extend(['', '有限重试路径：所有尝试费用与质量/时限分母。', '', '| 场景 | 成功概率 | 质量且按时概率 | 每质量成功费用 |', '| --- | --- | --- | --- |'])
    for name, result in retry_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['success_probability_exact']} | {s['quality_and_deadline_probability_exact']} | {s['cost_per_quality_success_exact']} |")
    lines.extend(['', '视觉编码单独计量：patch、视觉block、merger/DeepStack，不含语言prefill。', '', '| 场景 | 每图矩阵FLOPs | 本请求矩阵FLOPs | 编码次数 |', '| --- | ---: | ---: | ---: |'])
    for name, result in vision_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['matrix_flops_per_image']} | {s['matrix_flops_per_request']} | {s['encoder_executions_per_request']} |")
    lines.extend(['', '生成模型阶段矩阵：执行次数由时间轴/码本/去噪循环明确计入，缺项不冒充总量。', '', '| 场景 | 范围 | 已计矩阵FLOPs |', '| --- | --- | ---: |'])
    for rows, key, scope in ((omni_audio_rows, 'accounted_transformer_and_bridge_matrix_flops', '音频Transformer与桥接'), (image_rows, 'denoising_matrix_flops', '图像去噪DiT'), (video_rows, 'matrix_core_flops', '视频matrix-core')):
        for name, result in rows:
            lines.append(f"| [{name}]({name}.md) | {scope} | {result['summary'][key]} |")
    lines.extend(['', 'DeepSeek V3基础逻辑前向：expanded MLA参考路径。', '', '| 场景 | 参数 | 矩阵FLOPs | 驻留KV bytes |', '| --- | ---: | ---: | ---: |'])
    for name, result in v3_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['logical_base_parameters']} | {s['matrix_flops']} | {s['kv_resident_after_bytes']} |")
    lines.extend(['', '真实环境资源：CPU/RSS采样和完整观察窗生命周期。', '', '| 场景 | 数据集 | 报告组/轮数 | 真实OS队列等待 |', '| --- | --- | ---: | --- |'])
    for name, result in environment_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['dataset']} | {s.get('reported_runs', s.get('rounds'))} | {s['scheduler_queue_wait_seconds']} |")
    lines.extend(['', 'Qwen3-VL完整EC、KV与声明资源池上界。', '', '| 场景 | 每图EC bytes | 每图KV bytes | 请求/s上界 |', '| --- | ---: | ---: | --- |'])
    for name, result in multimodal_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['complete_encoder_bytes_per_image']} | {s['visual_kv_bytes_per_image']} | {s['best_known_bound_requests_per_second_exact']} |")
    lines.extend(['', 'V4非routed FP8 Linear：官方tile与scale复算。', '', '| 场景 | 有效矩阵FLOPs | tile矩阵FLOPs | scale FLOPs |', '| --- | ---: | ---: | ---: |'])
    for name, result in v4_fp8_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['valid_matrix_flops']} | {s['padded_tile_matrix_flops']} | {s['logical_scale_flops']} |")
    lines.extend(['', '假想服务缓存费用与质量/时限联合完成率。', '', '| 场景 | 费用交点 | B费用更低 | B满足联合90%目标 |', '| --- | --- | --- | --- |'])
    for name, result in routing_cost_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['cost_crossover_b_hit_fraction_exact']} | {s['b_cheaper_per_quality_success']} | {s['b_meets_joint_target']} |")
    lines.extend(['', '权重交接：完整参数、EP所有权、单播出口及分阶段容量。', '', '| 场景 | 全权重 bytes | 最大rank权重 bytes | 选择性出口 bytes |', '| --- | ---: | ---: | ---: |'])
    for name, result in weight_handoff_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['total_bf16_weight_bytes']} | {s['largest_rank_weight_bytes']} | {s['selective_unicast_egress_bytes']} |")
    lines.extend(['', '教师最终hidden与全logits缓存：完整词表与重投影成本。', '', '| 场景 | hidden bytes | logits bytes | 单次head FLOPs |', '| --- | ---: | ---: | ---: |'])
    for name, result in teacher_cache_rows:
        s = result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['hidden_cache_bytes']} | {s['full_logits_cache_bytes']} | {s['one_head_gemm_flops']} |")
    lines.extend(['', 'Routing Replay元数据：官方专家几何、ID编码与显式身份字段预算。', '',
                  '| 场景 | MoE层 | top-k | ID bytes | 含声明元数据bytes | 供给有余量 |', '| --- | ---: | ---: | ---: | ---: | --- |'])
    for name,result in routing_metadata_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['moe_layers']} | {s['top_k']} | {s['routed_id_bytes']} | {s['complete_declared_payload_bytes']} | {s['transport_has_strict_slack']} |")
    lines.extend(['', '名义Dense 6ND：固定数据与按参数增长的数据预算分开。', '',
                  '| 场景 | 规则 | 设备配置 | 时间行数 | 参数界行数 |', '| --- | --- | ---: | ---: | ---: |'])
    for name,result in dense_scale_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['scaling_rule']} | {s['device_configurations']} | {s['evaluated_rows']} | {s['evaluated_parameter_bounds']} |")
    lines.extend(['', '训练期限：官方逐矩阵工作与BF16/FP32 dense设备峰值，必要下界非部署保证。', '',
                  '| 场景 | task矩阵 FLOPs | 持久状态 bytes | 可用训练秒 | 缺少可选峰值的型号 |', '| --- | ---: | ---: | ---: | --- |'])
    for name,result in deadline_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['task_training_matrix_flops']} | {s['persistent_state_bytes']} | {s['available_training_seconds']} | {s['missing_hardware_profiles']} |")
    lines.extend(['', '实际DCP重分片恢复：完整逻辑载荷、容器与下一步更新分列。', '',
                  '| 场景 | 逻辑 bytes | 实际文件 bytes | metadata bytes | 恢复rank数 |', '| --- | ---: | ---: | ---: | ---: |'])
    for name,result in resume_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['unique_logical_state_bytes']} | {s['actual_checkpoint_file_bytes']} | {s['metadata_bytes']} | {s['restored_ranks']} |")
    lines.extend(['', '实际DCP提交前终止：已写数据不等于可恢复，未完成时间保留null。', '',
                  '| 场景 | 已提交 | 未提交 | 未提交数据 bytes | 恢复cursor | 待重做更新数 |', '| --- | ---: | ---: | ---: | ---: | ---: |'])
    for name,result in checkpoint_fault_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['completed_commits']} | {s['incomplete_commits']} | {s['incomplete_data_bytes']} | {s['fallback_recovered_cursor']} | {s['completed_updates_after_recovery_point']} |")
    lines.extend(['', '实际CPU保存基线：配对差值与全窗口，非Qwen性能。', '',
                  '| 场景 | 运行数 | 已核验恢复数 | 异步−无保存窗口中位差 s | 异步−无保存训练中位差 s |', '| --- | ---: | ---: | ---: | ---: |'])
    for name,result in checkpoint_baseline_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['runs']} | {s['restored_checkpoints']} | {s['median_paired_async_minus_none_window_seconds']} | {s['median_paired_async_minus_none_training_seconds']} |")
    lines.extend(['', '保存周期：一阶近似与指定Poisson重试模型分开，故障率为教学输入。', '',
                  '| 场景 | 保存c秒 | 作业MTBF秒 | 一阶最优tau秒 | Poisson最优tau秒 |', '| --- | --- | --- | --- | --- |'])
    for name,result in interval_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['blocking_save_cost_exact_seconds']} | {s['job_mtbf_exact_seconds']} | {s['first_order_optimal_useful_interval_seconds']} | {s['poisson_optimal_useful_interval_seconds']} |")
    lines.extend(['', '异步检查点：有限缓冲、背压和完整持久化，教学时序。', '',
                  '| 场景 | 载荷 bytes | upload s | 活跃缓冲峰值 bytes | 故障可恢复capture s |', '| --- | ---: | --- | ---: | --- |'])
    for name,result in async_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['payload_bytes']} | {s['upload_service_exact_seconds']} | {s['snapshot_buffer_live_peak_bytes']} | {s['recovery_capture_exact_seconds']} |")
    lines.extend(['', '检查点逻辑重分片：各目标范围与文件偏移，无真实存储IO计时。', '',
                  '| 场景 | 逻辑checkpoint bytes | 请求读取 bytes | 源文件数 | 连续读取范围数 |', '| --- | ---: | ---: | ---: | ---: |'])
    for name,result in checkpoint_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['logical_checkpoint_bytes']} | {s['requested_read_bytes']} | {s['source_file_count']} | {s['planned_read_ranges']} |")
    lines.extend(['', '梯度转换位置：单张量顺序路径与同时存活缓冲，吞吐是教学输入。', '',
                  '| 场景 | BF16 bytes | FP32 bytes | 等时链路 bytes/s | 容量内最快 |', '| --- | ---: | ---: | ---: | --- |'])
    for name,result in gradient_cast_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['bf16_bytes']} | {s['fp32_bytes']} | {s['equal_time_link_bytes_per_second_exact']} | {s['fastest_fitting_buffers']} |")
    lines.extend(['', '全参数Adam／ZeRO持久状态：精度与分片布局显式输入，未证明训练峰值可行。', '',
                  '| 场景 | 总参数 | 未分片 bytes | stage3每rank bytes | 所列分配可容纳stage |', '| --- | ---: | ---: | ---: | --- |'])
    for name,result in training_state_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['parameters']} | {s['unsharded_persistent_bytes']} | {s['minimum_persistent_bytes_per_rank']} | {s['stages_fitting_specified_allocations']} |")
    lines.extend(['', '多级不可变页驻留：同层并集、跨层副本与容量预算，区间为教学输入。', '',
                  '| 场景 | 峰值实体 bytes | 实体 byte-seconds | 跨层副本 byte-seconds | 容量可行 |', '| --- | ---: | ---: | ---: | --- |'])
    for name,result in residency_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['all_tier_peak_physical_bytes']} | {s['all_tier_physical_byte_seconds_exact']} | {s['cross_tier_copy_byte_seconds_exact']} | {s['all_tiers_capacity_feasible']} |")
    lines.extend(['', '实际坏页预取策略：成功回退、未完成观察和存储状态分列。', '',
                  '| 场景 | 策略数 | 完成请求 | 未完成观察 |', '| --- | ---: | ---: | ---: |'])
    for name,result in fault_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['policies']} | {s['completed_requests']} | {s['censored_requests']} |")
    lines.extend(['', '实际缺页恢复：连续前缀、重算及BF16逐位差异分列。', '',
                  '| 场景 | 条件数 | 请求数 | 输出与参考一致 |', '| --- | ---: | ---: | --- |'])
    for name,result in missing_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['cases']} | {s['requests']} | {s['outputs_match_reference']} |")
    lines.extend(['', '实际KV正常重启：文件载荷、读取和可复用前缀分账，非物理磁盘IO。', '',
                  '| 场景 | 文件数 | 库存bytes | get文件bytes | 可复用bytes |', '| --- | ---: | ---: | ---: | ---: |'])
    for name,result in restart_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['verified_payload_files']} | {s['stored_payload_bytes']} | {s['consumer_read_file_bytes']} | {s['consumer_reusable_bytes']} |")
    lines.extend(['', '真实队列压力：目标节省与整组完成增加分列，三轮配对差值。', '',
                  '| 场景 | 目标节省秒中位 | 整组增加秒中位 | 生成调用 |', '| --- | ---: | ---: | ---: |'])
    for name,result in pressure_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['target_saved_seconds_paired_median']} | {s['pair_added_seconds_paired_median']} | {s['actual_generation_calls']} |")
    lines.extend(['', '真实原生路由回放：模型响应命中与worker日志身份，固定单token串行请求。', '',
                  '| 场景 | 缓存token | 输入token | 命中请求 | 中位客户端秒 | 逻辑节省FLOPs |', '| --- | ---: | ---: | ---: | ---: | ---: |'])
    for name,result in router_trace_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['cached_tokens']} | {s['prompt_tokens']} | {s['hit_requests']} | {s['client_median_s']} | {s['saved_matrix_flops']} |")
    lines.extend(['', '缓存路由：同一请求的队列／就绪依赖和两点失效概率。', '',
                  '| 场景 | 前缀bytes | A期望ns | A p99 ns | A达标概率 | 已确认有效时最快路径 |', '| --- | ---: | --- | --- | --- | --- |'])
    for name,result in cache_route_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['prefix_state_bytes']} | {s['a_expected_ns_exact']} | {s['a_p99_ns_exact']} | {s['a_slo_pass_probability_exact']} | {s['fastest_known_valid_path']} |")
    lines.extend(['', '专家复制回本：同一批次重复、串行冷复制与逐rank增量容量。', '',
                  '| 场景 | 复制bytes | setup ns | 每批节省ns | 可行严格回本批数 | 选定部署 |', '| --- | ---: | --- | --- | --- | --- |'])
    for name,result in replica_payback_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['replica_weight_bytes']} | {s['serialized_copy_setup_ns_exact']} | {s['per_batch_saving_ns_exact']} | {s['feasible_strict_payback_batches']} | {s['selected_deployment']} |")
    lines.extend(['', 'Grouped专家矩阵：独立tile补齐与每rank工作，不是实测kernel时长。', '',
                  '| 场景 | 有效FLOPs | 完全补齐FLOPs | padding倍数 | 最忙rank补齐FLOPs |', '| --- | ---: | ---: | --- | ---: |'])
    for name,result in grouped_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['valid_matrix_flops']} | {s['padded_matrix_flops']} | {s['padding_work_ratio_exact']} | {s['max_rank_padded_flops']} |")
    lines.extend(['', '专家就地执行：单层非驻留专家，理想权重复用与教学服务能力。', '',
                  '| 场景 | 不同专家 | token—专家任务 | 权重bytes | 激活往返bytes | CPU ns | 搬权重GPU ns |', '| --- | ---: | ---: | ---: | ---: | --- | --- |'])
    for name,result in locality_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['remote_active_experts']} | {s['remote_token_expert_tasks']} | {s['remote_distinct_weight_bytes']} | {s['per_assignment_activation_roundtrip_bytes']} | {s['cpu_service_ns_exact']} | {s['weight_copy_service_ns_exact']} |")
    lines.extend(['', 'PD整数配比：有效阶段token/s转为同一请求单位，非设备峰值或SLO。', '',
                  '| 场景 | P新token | D调用 | 最佳PD请求/s | 共置请求/s | KV交接bytes/请求 |', '| --- | ---: | ---: | --- | --- | ---: |'])
    for name,result in pd_pool_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['new_prefill_tokens_per_request']} | {s['decode_calls_per_request']} | {s['best_pd_bound_requests_per_second_exact']} | {s['colocated_bound_requests_per_second_exact']} | {s['pd_transfer_bytes_per_request']} |")
    lines.extend(['', 'PD／AF串行交接：载荷、方向次数与双端staging分列，不含计算和排队。', '',
                  '| 场景 | PD bytes | AF bytes | AF方向次数 | PD ns | AF ns |', '| --- | ---: | ---: | ---: | --- | --- |'])
    for name,result in handoff_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['pd_snapshot_bytes']} | {s['af_total_bytes']} | {s['af_directional_messages']} | {s['pd_serialized_ns_exact']} | {s['af_serialized_ns_exact']} |")
    lines.extend(['', '实际KV池与自然检索质量：八任务重复执行，Q精度控制分列。', '',
                  '| 场景 | 自然正确／执行 | token槽 | 实际唯一storage bytes |', '| --- | --- | ---: | ---: |'])
    for name,result in quality_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['natural_correct']}/{s['natural_executions']} | {s['token_slots']} | {s['storage_bytes']} |")
    lines.extend(['', 'FFN卸载容量／流量与安全缓冲复用。', '',
                  '| 场景 | 净省GPU bytes | 每forward H2D bytes | 完成ns | 暴露等待ns |', '| --- | ---: | ---: | --- | --- |'])
    for name,result in offload_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['net_gpu_weight_bytes_saved']} | {s['per_forward_h2d_bytes']} | {s['scheduled_finish_ns_exact']} | {s['exposed_wait_ns_exact']} |")
    lines.extend(['', 'KV块格式与转换子账：存储位宽不代表执行精度。', '',
                  '| 场景 | BF16历史bytes | 每新增位置BF16 bytes |', '| --- | ---: | ---: |'])
    for name,result in codec_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['bf16_history_bytes']} | {s['bf16_next_token_append_bytes']} |")
    lines.extend(['', '实际GGUF头：混合张量类型与块尺度／文件开销分账。', '',
                  '| 场景 | 张量载荷bytes | 块尺度元数据bytes（载荷内） | 文件头和padding bytes |', '| --- | ---: | ---: | ---: |'])
    for name,result in gguf_layout_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['tensor_payload_bytes']} | {s['quantization_scale_metadata_bytes']} | {s['file_header_and_padding_bytes']} |")
    lines.extend(['', '实际GGUF分片与声明内存预算：不等同实际驻留。', '',
                  '| 场景 | 扣预留后bytes | 独立BF16 KV bytes/请求 |', '| --- | ---: | ---: |'])
    for name,result in gguf_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['declared_available_bytes']} | {s['bf16_kv_bytes_per_independent_request']} |")
    lines.extend(['', '真实请求回放：相同请求的联合计时达标与观测窗。', '',
                  '| 场景 | 达标／总请求 | 总窗口秒 | timing goodput请求/秒 |', '| --- | --- | ---: | ---: |'])
    for name,result in service_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['joint_timing_passed']}/{s['requests']} | {s['summed_observation_window_s']} | {s['timing_goodput_requests_per_s']} |")
    lines.extend(['', '固定／连续／分块调度：同一请求与官方工作，教学成本。', '',
                  '| 场景 | 迭代 | 完成ns | 最大ITL ns | 峰值KV bytes | 矩阵FLOPs |', '| --- | ---: | ---: | --- | ---: | ---: |'])
    for name,result in iteration_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['iterations']} | {s['finish_ns']} | {s['max_itl_ns']} | {s['peak_live_kv_bytes']} | {s['total_matrix_flops']} |")
    lines.extend(['', 'Dense batch权重复用与KV交叉点：BF16/FP32 dense峰值。', '',
                  '| 场景 | 声明容量最大batch | 旧KV达到权重batch | 计算／带宽交叉batch |', '| --- | ---: | --- | --- |'])
    for name,result in batch_reuse_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['declared_capacity_max_batch']} | {s['kv_history_equals_weights_batch']} | {s['compute_memory_crossover_batch']} |")
    lines.extend(['', '固定512-token块的真实区间与官方工作。', '',
                  '| 场景 | 首块中位ms | 末块中位ms | 配对比例中位 | backbone工作比例 |', '| --- | ---: | ---: | ---: | --- |'])
    for name,result in chunk_history_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['first_median_ms']} | {s['last_median_ms']} | {s['paired_last_first_median']} | {s['backbone_matrix_ratio_exact']} |")
    lines.extend(['', '官方DFlash草稿：独立权重、共享目标头、非因果块工作。', '',
                  '| 场景 | 草稿矩阵FLOPs | 目标验证FLOPs | 新特征bytes | 草稿KV峰值bytes |', '| --- | ---: | ---: | ---: | ---: |'])
    for name,result in dflash_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['draft_matrix_flops']} | {s['target_verify_matrix_flops']} | {s['new_target_feature_bytes']} | {s['draft_kv_peak_bytes']} |")
    lines.extend(['', '有限输出草稿预算：首次准备、末轮截断与逐状态选择。', '',
                  '| 场景 | 输出数 | 首次动作 | 最优期望ns | 相对普通decode速度比 |', '| --- | ---: | --- | --- | --- |'])
    for name,result in budget_policy_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['output_tokens']} | {s['first_action']} | {s['optimal_expected_ns_exact']} | {s['expected_speedup_exact']} |")
    lines.extend(['', '投机采样概率：精确枚举拒绝修正与错误重采样。', '',
                  '| 场景 | 接受概率 | 正确输出总变差 | 错误输出总变差 |', '| --- | --- | --- | --- |'])
    for name,result in sampling_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['acceptance_exact']} | {s['total_variation_exact']} | {s['wrong_total_variation_exact']} |")
    lines.extend(['', '投机轮次收支：接受草稿、额外交付与KV回滚。', '',
                  '| 场景 | 草稿接受率 | 平均交付 | 每交付token ns | 匹配速度比 |', '| --- | --- | --- | --- | --- |'])
    for name,result in speculative_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['draft_acceptance_fraction_exact']} | {s['mean_delivered_tokens_exact']} | {s['time_per_delivered_token_exact_ns']} | {s['matched_time_speedup_exact']} |")
    lines.extend(['', '真实Agent APC回放：实际命中和官方矩阵工作分列。', '',
                  '| 场景 | 命中token | 请求命中占比 | token加权命中 | 省下矩阵 FLOPs |', '| --- | ---: | --- | --- | ---: |'])
    for name,result in apc_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['cached_tokens']} | {s['request_hit_fraction_exact']} | {s['token_weighted_hit_fraction_exact']} | {s['saved_matrix_flops']} |")
    lines.extend(['', '独立前缀静态选择：预期省下矩阵工作与不可分容量。', '',
                  '| 场景 | 精确选择 | 贪心选择 | 精确占用 bytes | 多省 FLOPs |', '| --- | --- | --- | ---: | ---: |'])
    for name,result in prefix_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['optimal_selected']} | {s['density_greedy_selected']} | {s['optimal_resident_bytes']} | {s['optimal_minus_greedy_flops_exact']} |")
    lines.extend(['', 'KV保留／换出／重算：恢复等待和容量释放窗口。', '',
                  '| 场景 | KV bytes | 重算矩阵 FLOPs | 换出取回等待 ns | 重算等待 ns |', '| --- | ---: | ---: | ---: | ---: |'])
    for name,result in restore_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['kv_snapshot_bytes']} | {s['replay_backbone_matrix_flops']} | {s['offload_return_stall_exact_ns']} | {s['recompute_stall_ns']} |")
    lines.extend(['', '真实KV块记录：保留块、抢占与取消释放。', '',
                  '| 场景 | 池块数 | 请求峰值块 | 抢占数 | 调度位置 |', '| --- | ---: | ---: | ---: | ---: |'])
    for name,result in kv_trace_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['total_blocks']} | {s['peak_request_blocks']} | {s['preemption_count']} | {s['scheduled_token_positions']} |")
    lines.extend(['', 'KV分页与分支：逻辑、唯一有效和分配字节分别计量。', '',
                  '| 场景 | 页 bytes | 最终分配 bytes | 最终空位 bytes | COW有效复制 bytes |', '| --- | ---: | ---: | ---: | ---: |'])
    for name,result in page_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['page_bytes']} | {s['final_allocated_page_bytes']} | {s['final_unused_page_bytes']} | {s['total_copied_valid_bytes']} |")
    lines.extend(['', '不变KV快照复用：远程访问与搬回本地，含容量门槛。', '',
                  '| 场景 | 快照 bytes | 远程总 ns | 搬回总 ns | 可放入 | 选择 |', '| --- | ---: | ---: | ---: | --- | --- |'])
    for name,result in remote_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['snapshot_payload_bytes']} | {s['direct_total_exact_ns']} | {s['staged_total_exact_ns']} | {s['staged_fits_local_capacity']} | {s['selected_policy']} |")
    lines.extend(['', '封存RPC实测：客户端CPU、应用字节及同轮配对差。', '',
                  '| 场景 | JSON CPU ns | binary CPU ns | 配对节省中位 ns | 正差次数/20 |', '| --- | ---: | ---: | ---: | ---: |'])
    for name,result in rpc_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['json_client_cpu_median_ns']} | {s['binary_client_cpu_median_ns']} | {s['json_to_binary_paired_median_saved_ns']} | {s['json_to_binary_positive_pairs']} |")
    lines.extend(['', '有限credit与完成消费：传输完成和资源回收分列。', '',
                  '| 场景 | 传输全完 ns | 全回收 ns | 未消费峰值 | 最长提交等待 ns |', '| --- | ---: | ---: | ---: | ---: |'])
    for name,result in reclaim_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['all_transfers_complete_ns']} | {s['all_slots_reclaimed_ns']} | {s['peak_unconsumed_completions']} | {s['max_submission_delay_ns']} |")
    lines.extend(['', '必要发布依赖与独立事务：另含投机旧数据见证。', '',
                  '| 场景 | 全串行 ns | 必要依赖 ns | 独立完成 ns | 旧响应有效 |', '| --- | ---: | ---: | ---: | --- |'])
    for name,result in ordering_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['strict_all_done_ns']} | {s['dependency_all_done_ns']} | {s['dependency_independent_done_ns']} | {s['stale_response_valid']} |")
    lines.extend(['', '本地活跃关系与共享传输状态：显式隔离和容量假设。', '',
                  '| 场景 | 活跃关系 | 独立传输数 | 共享传输数 | 共享总 bytes |', '| --- | ---: | ---: | ---: | ---: |'])
    for name,result in connection_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['active_relations']} | {s['coupled_transport_count']} | {s['shared_transport_count']} | {s['shared_total_bytes']} |")
    lines.extend(['', '就绪偏差与完成分布：显式有限记录的配对反事实。', '',
                  '| 场景 | 原平均 ns | 交换加速平均 ns | 原 p99 ns |', '| --- | ---: | ---: | ---: |'])
    for name,result in tail_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['baseline_mean_exact_ns']} | {s['faster_exchange_mean_exact_ns']} | {s['baseline_p99_exact_ns']} |")
    lines.extend(['', '多路径乱序及显式丢失恢复：按序交付、保留payload和重传字节。', '',
                  '| 场景 | 完成 ns | 乱序保留峰值 bytes | 重传 bytes |', '| --- | ---: | ---: | ---: |'])
    for name,result in packet_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['completion_exact_ns']} | {s['peak_retained_reorder_bytes']} | {s['retransmitted_bytes']} |")
    lines.extend(['', '反馈期间有限缓冲：到达、服务、丢弃及残留守恒。', '',
                  '| 场景 | 峰值积压 bytes | 丢弃 bytes | 窗口结束积压 bytes |', '| --- | ---: | ---: | ---: |'])
    for name,result in feedback_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['peak_queue_bytes']} | {s['dropped_bytes']} | {s['final_queue_bytes']} |")
    lines.extend(['', '周期通信需求：流体队列、错峰及漂移，非反馈网络仿真。', '',
                  '| 场景 | 峰值需求 bytes/s | 队列峰值 bytes | 兼容度 | 末尾队列 bytes |', '| --- | ---: | ---: | ---: | ---: |'])
    for name,result in queue_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['peak_offered_bytes_per_second']} | {s['peak_queue_bytes']} | {s['compatibility']} | {s['final_queue_bytes']} |")
    lines.extend(['', '物理有向环前三轮：消息数与每条链路载荷分别枚举。', '',
                  '| 场景 | 枚举消息数 | 递归物理 bytes | Swing物理 bytes |', '| --- | ---: | ---: | ---: |'])
    for name,result in path_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['enumerated_messages']} | {s['recursive_physical_link_bytes']} | {s['swing_physical_link_bytes']} |")
    lines.extend(['', '周期位置分配、割集与重构：容量／速率／使用寿命分别检验。', '',
                  '| 场景 | 消息 bytes | 原路径 us | 新路径 us | 严格回本次数 |', '| --- | ---: | ---: | ---: | ---: |'])
    for name,result in allocation_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['message_bytes']} | {s['before_ns']/1000:.6f} | {s['after_ns']/1000:.6f} | {s['strictly_faster_calls']} |")
    lines.extend(['', '两微批切分与争用：数学工作不变，逻辑读取与联合窗口单列。', '',
                  '| 场景 | 原batch ms | 拆分串行 ms | 理想重叠 ms | 含争用完成 ms |', '| --- | ---: | ---: | ---: | ---: |'])
    for name,result in overlap_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['full_finish_ns']/10**6:.6f} | {s['split_serial_finish_ns']/10**6:.6f} | {s['ideal_finish_ns']/10**6:.6f} | {s['paired_finish_ns']/10**6:.6f} |")
    lines.extend(['', '请求依赖图：时长替换后重新调度资源并检查关键路径转移。', '',
                  '| 场景 | 原请求 ns | 改后请求 ns | 改后关键路径 |', '| --- | ---: | ---: | --- |'])
    for name,result in dag_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['baseline_finish_ns']} | {s['modified_finish_ns']} | {' → '.join(s['modified_critical_path'])} |")
    lines.extend(['', '按块就绪的设备任务：独立worker与显式分派／发布开销。', '',
                  '| 场景 | 设备任务数 | 屏障 us | 按块就绪 us | 中间存活 bytes |', '| --- | ---: | ---: | ---: | ---: |'])
    for name,result in persistent_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['persistent_device_tasks']} | {s['barrier_finish_ns']/1000:.6f} | {s['persistent_finish_ns']/1000:.6f} | {s['persistent_intermediate_live_peak_bytes']} |")
    lines.extend(['', '原始FFN运行记录：无分析器计时与Nsight事件分别核算。', '',
                  '| 场景 | 计时方案 | 时间线区间 | 单链真实矩阵 FLOPs |', '| --- | ---: | ---: | ---: |'])
    for name,result in runtime_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['timing_cases']} | {s['trace_ranges']} | {s['real_matrix_flops_per_chain']} |")
    lines.extend(['', '形状特化：同一频数组，准备缓存与分桶补齐重新核算。', '',
                  '| 场景 | 每组调用数 | 真实矩阵 FLOPs | 含准备最优策略 |', '| --- | ---: | ---: | --- |'])
    for name,result in specialization_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['cohort_calls']} | {s['cohort_real_matrix_flops']} | {s['selected_policy']} |")
    lines.extend(['', '候选分数与部署：频数、失败回退和额外准备分别计入。', '',
                  '| 场景 | 最佳统一候选 | 分派平均 ns | 摊平调用数 | 严格收益调用数 |', '| --- | --- | ---: | ---: | ---: |'])
    for name,result in deployment_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['best_uniform']} | {s['mixed_mean_ns']} | {s['break_even_calls']} | {s['strictly_faster_calls']} |")
    lines.extend(['', '图边界成本：教学串行预算，稳态与实例寿命分别选择。', '',
                  '| 场景 | 额外复制 bytes | FFN padding FLOPs | 稳态路径 | 寿命路径 |', '| --- | ---: | ---: | --- | --- |'])
    for name,result in graph_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['extra_copy_interface_bytes']} | {s['padding_ffn_matrix_flops']} | {s['minimum_serial_steady_external_input_path']} | {s['minimum_lifetime_external_input_path']} |")
    lines.extend(['', 'FIFO与独立重排槽：原进度容量及背压后的最后取走时刻。', '',
                  '| 场景 | 原进度需 bytes | 可维持 | 背压最后取走格 |', '| --- | ---: | --- | ---: |'])
    for name,result in fifo_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['original_handoff_required_bytes']} | {s['original_progress_fits']} | {s['bounded_last_take_tick']} |")
    lines.extend(['', '主机准备／H2D／消费：双端槽复用与精确有理数时序。', '',
                  '| 场景 | H2D bytes | 串行 ms | 槽约束完成 ms |', '| --- | ---: | ---: | ---: |'])
    for name,result in host_rows:
        s=result['summary']
        lines.append(f"| [{name}]({name}.md) | {s['total_h2d_bytes']} | {s['serial_seconds']*1000:.6f} | {s['scheduled_finish_seconds']*1000:.6f} |")
    lines.extend(["", "状态与选中历史载荷单列。K3 的 recurrent 读写不包含在历史载荷中；V4 resident 含压缩器固定槽。", "",
                  "| 模型／场景 | 当前状态 MiB | 选中历史载荷 MiB |", "| --- | ---: | ---: |"])
    for name, result in state_rows:
        summary = result["summary"]
        lines.append(f"| [{name}]({name}.md) | {summary['resident_bytes']/2**20:.6f} | {summary['selected_history_payload_bytes']/2**20:.6f} |")
    lines.extend(["", "真实 Q 投影：单层、BF16 输入／输出、FP32 累加、dense、冷内存服务量下界。未知算力仅给内存服务时间，不能称完整 Roofline 或模型时延。", "",
                  "| 场景 | M×K×N | AI FLOPs/byte | 计算服务 μs | 内存服务 μs | Roofline 下界 μs |",
                  "| --- | --- | ---: | ---: | ---: | ---: |"])
    for name, result in projection_rows:
        summary, shapes = result["summary"], result["shapes"]
        def microseconds(key):
            value = summary[key]
            return "未知" if value is None else f"{value * 1e6:.6f}"
        lines.append(f"| [{name}]({name}.md) | {shapes['A'][0]}×{shapes['A'][1]}×{shapes['Y'][1]} | {summary['arithmetic_intensity_flops_per_byte']:.6f} | {microseconds('compute_service_seconds')} | {microseconds('memory_service_seconds')} | {microseconds('roofline_lower_bound_seconds')} |")
    lines.extend(['', '环境创建、克隆与预热：', ''])
    for name, result in lifecycle_rows:
        lines.append(f"- [{name}]({name}.md)：声明容量/创建路径/预热期望及独立本地记录，实际云端创建时间未测。")
    lines.extend(['', 'UB现代教学组织对照：容量与串行通信分列，非历史参数复原。', ''])
    for name, result in ub_rows:
        lines.append(f"- [{name}]({name}.md)：{result['scope_crossover']['communication_only_preference']}（仅通信比较，须另查容量）")
    lines.extend(['', '公开训练投入与条件预算：', ''])
    for name, result in training_history_rows:
        lines.append(f"- [{name}]({name}.md)：{result['summary']['models']}模型公开字段；代理工作、阶段观测与声明成本分列。")
    lines.extend(['', 'Scaling-law教学拟合与生命周期预算：', ''])
    for name, result in scaling_rows:
        lines.append(f"- [{name}]({name}.md)：预测验证损失下的候选最优N={result['summary']['optimal_candidate_N']}；非实际任务质量排名。")
    lines.extend(['', 'TP/EP迁移子账：资源下界、声明串行时间和容量分别检查；不代表完整部署验收。', ''])
    for name, result in reconfiguration_rows:
        s = result['summary']
        lines.append(f"- [{name}]({name}.md)：网络 {s['network_bytes']} bytes；传输下界 {s['transfer_lower_bound_exact_seconds']} s；声明串行切换 {s['declared_serial_switch_seconds_exact']} s；容量 {s['all_declared_capacities_fit']}。")
    lines.extend(["", "[官方硬件规格表](hardware.md)记录每项精度、累加格式、稀疏条件与仍待核实的字段。", ""])
    (output / "README.md").write_text("\n".join(lines))
    artifacts.append("results/README.md")
    manifest = {
        "schema_version": 1,
        "scope": "implemented scenarios only; not evidence of whole-book completion",
        "scenario_sha256": hashlib.sha256(scenario_path.read_bytes()).hexdigest(),
        "inputs": input_hashes(),
        "artifacts": [{"file": name, "sha256": hashlib.sha256((PROJECT / name).read_bytes()).hexdigest()} for name in artifacts],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return {"forward_scenarios": len(forward_rows), "state_scenarios": len(state_rows),
            "projection_scenarios": len(projection_rows), "expert_scenarios": len(expert_rows),
            "hyper_connection_scenarios": len(hc_rows), "attention_scenarios": len(attention_rows),
            "v4_forward_scenarios": len(v4_rows), "mla_scenarios": len(mla_rows),
            "kda_scenarios": len(kda_rows), "attn_res_scenarios": len(residual_rows),
            "reconfiguration_scenarios": len(reconfiguration_rows), "scaling_law_scenarios": len(scaling_rows), "training_history_scenarios": len(training_history_rows), "ub_scope_scenarios": len(ub_rows), "environment_lifecycle_scenarios": len(lifecycle_rows), "omni_vision_encoding_scenarios": len(omni_vision_rows), "omni_understanding_scenarios": len(understanding_rows), "sequence_dependency_scenarios": len(dependency_rows), "tpu_demand_scenarios": len(tpu_rows), "nic_budget_scenarios": len(nic_rows), "omni_audio_encoder_scenarios": len(input_audio_rows), "vl_request_scenarios": len(vl_rows), "retry_paths_scenarios": len(retry_rows), "vision_encoding_scenarios": len(vision_rows), "omni_audio_scenarios": len(omni_audio_rows), "image_generation_scenarios": len(image_rows), "video_generation_scenarios": len(video_rows), "v3_forward_scenarios": len(v3_rows), "environment_resources_scenarios": len(environment_rows), "multimodal_cache_scenarios": len(multimodal_rows), "v4_fp8_linear_scenarios": len(v4_fp8_rows), "routing_cost_scenarios": len(routing_cost_rows), "weight_handoff_scenarios": len(weight_handoff_rows), "teacher_cache_scenarios": len(teacher_cache_rows), "routing_metadata_scenarios": len(routing_metadata_rows), "dense_training_scale_scenarios": len(dense_scale_rows), "training_deadline_scenarios": len(deadline_rows), "checkpoint_resume_scenarios": len(resume_rows), "checkpoint_fault_scenarios": len(checkpoint_fault_rows), "checkpoint_baseline_scenarios": len(checkpoint_baseline_rows), "checkpoint_interval_scenarios": len(interval_rows), "checkpoint_async_scenarios": len(async_rows), "checkpoint_reshard_scenarios": len(checkpoint_rows), "gradient_cast_scenarios": len(gradient_cast_rows), "training_state_scenarios": len(training_state_rows), "cache_residency_scenarios": len(residency_rows), "cache_fault_scenarios": len(fault_rows), "cache_missing_scenarios": len(missing_rows), "cache_restart_scenarios": len(restart_rows), "router_pressure_scenarios": len(pressure_rows), "router_trace_scenarios": len(router_trace_rows), "cache_route_scenarios": len(cache_route_rows), "replica_payback_scenarios": len(replica_payback_rows), "grouped_expert_scenarios": len(grouped_rows), "expert_locality_scenarios": len(locality_rows), "pd_pool_scenarios": len(pd_pool_rows), "pd_af_handoff_scenarios": len(handoff_rows), "kv_quality_scenarios": len(quality_rows), "weight_offload_scenarios": len(offload_rows), "kv_codec_scenarios": len(codec_rows), "gguf_layout_scenarios": len(gguf_layout_rows), "gguf_inventory_scenarios": len(gguf_rows), "service_replay_scenarios": len(service_rows), "iteration_batching_scenarios": len(iteration_rows), "batch_reuse_scenarios": len(batch_reuse_rows), "chunk_history_scenarios": len(chunk_history_rows), "dflash_work_scenarios": len(dflash_rows), "speculative_budget_scenarios": len(budget_policy_rows), "speculative_sampling_scenarios": len(sampling_rows), "speculative_round_scenarios": len(speculative_rows), "apc_trace_scenarios": len(apc_rows), "prefix_value_scenarios": len(prefix_rows), "kv_restore_scenarios": len(restore_rows), "kv_trace_scenarios": len(kv_trace_rows), "kv_page_scenarios": len(page_rows), "remote_state_scenarios": len(remote_rows), "rpc_trace_scenarios": len(rpc_rows), "completion_reclaim_scenarios": len(reclaim_rows), "operation_ordering_scenarios": len(ordering_rows), "connection_state_scenarios": len(connection_rows), "collective_tail_scenarios": len(tail_rows), "packet_reorder_scenarios": len(packet_rows), "feedback_queue_scenarios": len(feedback_rows), "periodic_queue_scenarios": len(queue_rows), "collective_path_scenarios": len(path_rows), "topology_allocation_scenarios": len(allocation_rows), "microbatch_overlap_scenarios": len(overlap_rows), "request_dag_scenarios": len(dag_rows), "persistent_task_scenarios": len(persistent_rows), "runtime_trace_scenarios": len(runtime_rows), "shape_specialization_scenarios": len(specialization_rows), "optimization_deployment_scenarios": len(deployment_rows), "graph_execution_scenarios": len(graph_rows), "stream_buffer_scenarios": len(fifo_rows), "host_transfer_scenarios": len(host_rows), "attention_tile_scenarios": len(attention_tile_rows), "online_softmax_scenarios": len(softmax_rows), "fusion_numerics_scenarios": len(numeric_rows), "quantized_gemm_scenarios": len(quant_rows), "fusion_lifetime_scenarios": len(fusion_rows), "loop_access_scenarios": len(loop_rows), "bank_mapping_scenarios": len(bank_rows), "row_reduction_scenarios": len(reduction_rows), "gemm_tile_scenarios": len(tile_rows), "audio_timing_scenarios": len(audio_rows), "agent_trace_scenarios": len(agent_rows), "request_trace_scenarios": len(trace_rows), "rl_supply_scenarios": len(supply_rows), "rl_cycle_scenarios": len(rl_rows), "training_matrix_scenarios": len(training_rows), "pipeline_schedule_scenarios": len(pipeline_rows), "dense_communication_scenarios": len(communication_rows), "dense_placement_scenarios": len(placement_rows), "capacity_scan_scenarios": len(capacity_rows), "moe_dedup_scenarios": len(dedup_rows), "numa_staging_scenarios": len(staging_rows), "all_to_all_scenarios": len(exchange_rows), "tree_collective_scenarios": len(tree_rows), "ring_collective_scenarios": len(ring_rows), "decode_budget_scenarios": len(budget_rows), "memory_concurrency_scenarios": len(window_rows), "resource_basics_scenarios": len(basics_rows), "cache_sequence_scenarios": len(sequence_rows), "k3_forward_scenarios": len(k3_rows), "kda_chunk_scenarios": len(chunk_rows), "artifacts": len(artifacts)}
