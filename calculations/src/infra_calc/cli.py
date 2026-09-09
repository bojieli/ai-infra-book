"""Reader-facing CLI. Default calculations are offline and require no GPU."""
import argparse
import json
from pathlib import Path
import sys

from .models import qwen3, forward as model_forward
from .report import markdown, operator_csv
from .schema import Scenario
from .sources import fetch_sources, records, verify_sources, model_config
from .topics import state, projection, experts, hyper_connections, v4_attention, v4_forward, k3_mla, k3_kda, attn_res, kda_chunk, k3_forward, cache_sequence, resource_basics, memory_concurrency, decode_budget, ring_collective, tree_collective, all_to_all, numa_staging, moe_dedup, capacity_scan, dense_placement, dense_communication, pipeline_schedule, training_matrix, rl_cycle, rl_supply, request_trace, agent_trace, audio_timing, gemm_tiles, row_reduction, bank_mapping, loop_access, fusion_lifetime, quantized_gemm, fusion_numerics, online_softmax, attention_tiles, host_transfer, stream_buffer, graph_execution, optimization_deployment, shape_specialization, runtime_trace, persistent_tasks, request_dag, microbatch_overlap, topology_allocation, collective_paths, periodic_queue, feedback_queue, packet_reorder, collective_tail, connection_states, operation_ordering, completion_reclaim, rpc_trace, remote_state, kv_pages, kv_trace, kv_restore, prefix_value, apc_trace, speculative_round, speculative_sampling, speculative_budget, dflash_work, chunk_history, batch_reuse, iteration_batching, service_replay, gguf_inventory, gguf_layout, kv_codec, weight_offload, kv_quality, pd_af_handoff, pd_pool, expert_locality, grouped_experts, replica_payback, cache_route, router_trace, router_pressure, cache_restart, cache_missing, cache_fault, cache_residency, training_state, gradient_cast, checkpoint_reshard, checkpoint_async, checkpoint_interval, checkpoint_baseline, checkpoint_fault, checkpoint_resume, training_deadline, dense_training_scale, routing_metadata, teacher_cache, weight_handoff, routing_cost, v4_fp8_linear, multimodal_cache, v3_forward, environment_resources, omni_audio, image_generation, video_generation, vision_encoding, retry_paths, vl_request, omni_audio_encoder, nic_budget, omni_vision_encoding, tpu_demand, sequence_dependencies, omni_understanding, environment_lifecycle, ub_scope, training_history, scaling_law, reconfiguration
from .topics import qwen235_placement
from .topics import dense_quantized_placement
from .topics import request_model_comparison
from .topics import fish_wave_export
from .topics import strategy_record_cost
from .topics import training_nonmatrix
from .topics import real_scaling_fit
from .topics import stage_resource_bounds
from .topics import v4_compressor_online
from .topics import training_input_supply
from .topics import qwen235_execution
from .topics import qwen235_expert_granularity
from .topics import architecture_tile_work
from .topics import trace_resource_bridge
from .topics import request_hardware_bridge
from .topics import v4_mtp_forward
from .topics import trace_cache_lifecycle
from .topics import qwen36_forward, qwen36_capacity, memory_pool_access
from .topics import supernode_cohort_cost
from .topics import hierarchical_gradient
from .topics import image_request_budget
from .topics import image_request_streaming
from .topics import connection_window
from .topics import connection_sequence
from .topics import growing_remote_kv
from .topics import paired_projection_cost
from .topics import matrix_vector_handoff
from .topics import v4_copy_coordinates
from .topics import attention_input_pipeline
from .topics import fa4_resource_balance
from .topics import storage_generation_comparison
from .topics import granularity_selection
from .topics import omni_audio_preprocess
from .topics import v4_optimizer
from .topics import v4_moe_training
from .topics import vision_preprocess
from .topics import training_pipeline_gemm_state
from .topics import training_pipeline_schedule
from .topics import real_scaling_lifecycle, v4_training_primitives, v4_hc_training, v4_attention_training, v4_attention_projections, v4_compressor_training, v4_compressor_overlap
from .topics import v4_prefix_continuation
from .topics import flux_vae_decode, architecture_variants
from .topics import workload_profiles
from .topics import qwen35_forward
from . import hardware


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    sub = command.add_subparsers(dest="command", required=True)
    from .paths import PROJECT
    migration = sub.add_parser('reconfiguration', help='Declared TP/EP weight and snapshot migration ledger')
    migration.add_argument('--inputs', type=Path, default=PROJECT / 'scenarios/reconfiguration-example.json')
    migration.add_argument('--format', choices=('json', 'md'), default='json')
    migration.add_argument('--output', type=Path)
    sub.add_parser("models", help="List downloaded models and current calculation support")
    sub.add_parser("verify-sources", help="Check every source SHA256")
    fetch = sub.add_parser("fetch", help="Re-download a pinned source group, preserving checksum; no dependency expansion")
    fetch.add_argument("--model", help="Exact source group; omit for all groups (not transitive model dependencies)")
    forward = sub.add_parser("forward", help="Qwen3 Dense/MoE per-operator accounting")
    forward.add_argument("--model", default="qwen3-8b")
    forward.add_argument("--batch", type=int, default=1)
    forward.add_argument("--history", type=int, default=0, help="Existing KV tokens per request")
    forward.add_argument("--tokens", type=int, default=8192, help="New tokens per request in this forward")
    forward.add_argument("--output-head", choices=("last", "all", "none"), default="last")
    forward.add_argument("--score-bytes", type=int, default=4)
    forward.add_argument("--routing", choices=("balanced", "concentrated"), default="balanced")
    forward.add_argument("--routing-counts", type=Path, help="JSON list of per-expert token counts, same histogram at every layer")
    forward.add_argument("--format", choices=("json", "md", "csv"), default="json")
    forward.add_argument("--output", type=Path)
    omni_vision = sub.add_parser('omni-vision-encoding', help='Omni image/video grids to Thinker features')
    omni_vision.add_argument('--inputs', type=Path)
    omni_vision.add_argument('--format', choices=('json','md'), default='json')
    omni_vision.add_argument('--output', type=Path)
    understanding = sub.add_parser('omni-understanding', help='Media encoders through Thinker prefill and decode')
    understanding.add_argument('--inputs', type=Path)
    understanding.add_argument('--format', choices=('json','md'), default='json')
    understanding.add_argument('--output', type=Path)
    sequence = sub.add_parser('sequence-dependencies', help='Fixed four-token RNN/Transformer graph and cache equality')
    sequence.add_argument('--format', choices=('json','md'), default='json')
    sequence.add_argument('--output', type=Path)
    tpu = sub.add_parser('tpu-demand', help='Historical voice-use demand anchor with explicit assumptions')
    tpu.add_argument('--inputs', type=Path)
    tpu.add_argument('--format', choices=('json','md'), default='json')
    tpu.add_argument('--output', type=Path)
    nic = sub.add_parser('nic-budget', help='Historical packet forwarding CPU and declared PCIe budgets')
    nic.add_argument('--inputs', type=Path)
    nic.add_argument('--format', choices=('json','md'), default='json')
    nic.add_argument('--output', type=Path)
    input_audio = sub.add_parser('omni-audio-encoder', help='Input mel chunks to Omni Thinker embeddings')
    input_audio.add_argument('--inputs', type=Path)
    input_audio.add_argument('--format', choices=('json','md'), default='json')
    input_audio.add_argument('--output', type=Path)
    vl = sub.add_parser('vl-request', help='Vision encoding plus language prefill and exact growing decode')
    vl.add_argument('--inputs', type=Path)
    vl.add_argument('--format', choices=('json','md'), default='json')
    vl.add_argument('--output', type=Path)
    retry = sub.add_parser('retry-paths', help='Finite conditional retry DAG resource and quality costs')
    retry.add_argument('--inputs', type=Path)
    retry.add_argument('--format', choices=('json','md'), default='json')
    retry.add_argument('--output', type=Path)
    vision = sub.add_parser('vision-encoding', help='Official Qwen3-VL image encoder separate from language prefill')
    vision.add_argument('--inputs', type=Path)
    vision.add_argument('--format', choices=('json','md'), default='json')
    vision.add_argument('--output', type=Path)
    audio_rows = sub.add_parser('omni-audio', help='Pinned omni-audio stage matrix and loop accounting')
    audio_rows.add_argument('--inputs', type=Path)
    audio_rows.add_argument('--format', choices=('json','md'), default='json')
    audio_rows.add_argument('--output', type=Path)
    image_rows = sub.add_parser('image-generation', help='Pinned image-generation stage matrix and loop accounting')
    image_rows.add_argument('--inputs', type=Path)
    image_rows.add_argument('--format', choices=('json','md'), default='json')
    image_rows.add_argument('--output', type=Path)
    video_rows = sub.add_parser('video-generation', help='Pinned video-generation stage matrix and loop accounting')
    video_rows.add_argument('--inputs', type=Path)
    video_rows.add_argument('--format', choices=('json','md'), default='json')
    video_rows.add_argument('--output', type=Path)
    for topic_name, help_text in (("flux-vae-decode", "FLUX VAE decoder operators and tensor lifetime budget"),
                               ("architecture-variants", "Official Qwen baseline and declared parameter-budget variants")):
        topic = sub.add_parser(topic_name, help=help_text)
        topic.add_argument("--inputs", type=Path)
        topic.add_argument("--format", choices=("json", "md", "csv") if topic_name == "flux-vae-decode" else ("json", "md"), default="json")
        topic.add_argument("--output", type=Path)
    prefix = sub.add_parser("v4-prefix-continuation", help="Sequential full-base V4 calls after restored prefix state")
    prefix.add_argument("--inputs", type=Path)
    prefix.add_argument("--format", choices=("json", "md"), default="json")
    prefix.add_argument("--output", type=Path)
    placement235 = sub.add_parser("qwen235-placement", help="Qwen235 eight-rank ownership and conditional grouped-storage capacity")
    placement235.add_argument("--inputs", type=Path)
    placement235.add_argument("--format", choices=("json", "md"), default="json")
    placement235.add_argument("--output", type=Path)
    dense_lowbit = sub.add_parser("dense-quantized-placement", help="Local-shard grouped storage and conditional capacity for three Dense models")
    dense_lowbit.add_argument("--inputs", type=Path)
    dense_lowbit.add_argument("--format", choices=("json", "md"), default="json")
    dense_lowbit.add_argument("--output", type=Path)
    request_compare = sub.add_parser("request-model-comparison", help="Four models under common restored prefix, input and output lengths")
    request_compare.add_argument("--inputs", type=Path)
    request_compare.add_argument("--format", choices=("json", "md"), default="json")
    request_compare.add_argument("--output", type=Path)
    fish_export = sub.add_parser("fish-wave-export", help="Fish CLI emitted code chunks through one codec and waveform host export")
    fish_export.add_argument("--inputs", type=Path)
    fish_export.add_argument("--format", choices=("json", "md"), default="json")
    fish_export.add_argument("--output", type=Path)
    strategy_cost = sub.add_parser("strategy-record-cost", help="Archived strict protocol replay and all-attempt consumption")
    strategy_cost.add_argument("--format", choices=("json", "md"), default="json")
    strategy_cost.add_argument("--output", type=Path)
    train_nonmatrix = sub.add_parser("training-nonmatrix", help="Qwen8 declared nonlinear backward, AdamW and saved-object budget")
    train_nonmatrix.add_argument("--inputs", type=Path)
    train_nonmatrix.add_argument("--format", choices=("json", "md"), default="json")
    train_nonmatrix.add_argument("--output", type=Path)
    real_scaling = sub.add_parser("real-scaling-fit", help="Official C4 observations, fixed model holdout and coordinate sensitivities")
    real_scaling.add_argument("--format", choices=("json", "md"), default="json")
    real_scaling.add_argument("--output", type=Path)
    for topic in ("v4-training-primitives", "v4-hc-training", "v4-attention-training", "v4-attention-projections", "v4-compressor-training", "v4-compressor-overlap"):
        parser = sub.add_parser(topic, help="Pinned V4 differentiable training subgraph ledger")
        parser.add_argument("--inputs", type=Path)
        parser.add_argument("--format", choices=("json", "md"), default="json")
        parser.add_argument("--output", type=Path)
    topic_parser = sub.add_parser("stage-resource-bounds", help="Source-backed conditional calculation")
    topic_parser.add_argument("--inputs", type=Path)
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    topic_parser = sub.add_parser("v4-compressor-online", help="Source-backed conditional calculation")
    topic_parser.add_argument("--inputs", type=Path)
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    topic_parser = sub.add_parser("training-input-supply", help="Source-backed conditional calculation")
    topic_parser.add_argument("--inputs", type=Path)
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    topic_parser = sub.add_parser("qwen235-execution", help="Source-backed conditional calculation")
    topic_parser.add_argument("--inputs", type=Path)
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    topic_parser = sub.add_parser("qwen235-expert-granularity", help="Qwen235 expert count/width/top-k work and ownership")
    topic_parser.add_argument("--inputs", type=Path)
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    topic_parser = sub.add_parser("architecture-tile-work", help="Architecture matrices and explicitly chosen tile padding")
    topic_parser.add_argument("--inputs", type=Path)
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    sub.add_parser("plot-chat-agent", help="Render archived Chat/Agent and conditional KV figure")
    sub.add_parser("plot-architecture-shapes", help="Render data-bound architecture shape diagram (optional Matplotlib)")
    sub.add_parser("plot-capacity-curves", help="Render exact per-rank capacity staircases (optional Matplotlib)")
    topic_parser = sub.add_parser("trace-resource-bridge", help="Sealed Chat observations to conditional Qwen8 work")
    topic_parser.add_argument("--inputs", type=Path)
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    topic_parser = sub.add_parser("request-hardware-bridge", help="Four-model request work and precision-matched H100 supply")
    topic_parser.add_argument("--inputs", type=Path)
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    topic_parser = sub.add_parser("paired-projection-cost", help="Archived projection timing and conditional whole-system cost/power")
    topic_parser.add_argument("--inputs", type=Path)
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    topic_parser = sub.add_parser("matrix-vector-handoff", help="Qwen QK/softmax/PV row dependencies and finite handoff slots")
    topic_parser.add_argument("--inputs", type=Path)
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    topic_parser = sub.add_parser("v4-copy-coordinates", help="Pinned shared-expert FP8 source copy coordinates and payloads")
    topic_parser.add_argument("--rows", type=int, default=32)
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    topic_parser = sub.add_parser("attention-input-pipeline", help="Qwen QK input slots, register staging and asynchronous supply")
    topic_parser.add_argument("--inputs", type=Path)
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    topic_parser = sub.add_parser("fa4-resource-balance", help="Pinned FA4 Table 1 and single-SM resource supply scenarios")
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    topic_parser = sub.add_parser("storage-generation-comparison", help="Official memory capacity/bandwidth comparison for Qwen8/235")
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    topic_parser = sub.add_parser("granularity-selection", help="Conditional expert granularity capacity and service comparison")
    topic_parser.add_argument("--inputs", type=Path)
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    topic_parser = sub.add_parser("trace-cache-lifecycle", help="Sealed Chat prefix retention and conditional restore")
    topic_parser.add_argument("--inputs", type=Path)
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    topic_parser = sub.add_parser("v4-mtp-forward", help="One pinned Flash MTPBlock call with supplied target features")
    topic_parser.add_argument("--inputs", type=Path)
    topic_parser.add_argument("--format", choices=("json", "md"), default="json")
    topic_parser.add_argument("--output", type=Path)
    pcm = sub.add_parser("omni-audio-preprocess", help="Pinned PCM to mel work and audio encoder entry")
    pcm.add_argument("--inputs", type=Path)
    pcm.add_argument("--format", choices=("json", "md"), default="json")
    pcm.add_argument("--output", type=Path)
    optimizer = sub.add_parser("v4-optimizer", help="V4 Muon/AdamW parameter groups and optimizer work")
    optimizer.add_argument("--inputs", type=Path)
    optimizer.add_argument("--format", choices=("json", "md"), default="json")
    optimizer.add_argument("--output", type=Path)
    moe_train = sub.add_parser("v4-moe-training", help="Fixed-selection V4 single-layer MoE forward/backward")
    moe_train.add_argument("--inputs", type=Path)
    moe_train.add_argument("--format", choices=("json", "md"), default="json")
    moe_train.add_argument("--output", type=Path)
    preprocess = sub.add_parser("vision-preprocess", help="Pinned RGB CPU resize, normalization and vision-entry bytes")
    preprocess.add_argument("--inputs", type=Path)
    preprocess.add_argument("--format", choices=("json", "md"), default="json")
    preprocess.add_argument("--output", type=Path)
    gemm_state = sub.add_parser("training-pipeline-gemm-state", help="Qwen8 matrix-input identities, recomputation and pipeline retention")
    gemm_state.add_argument("--inputs", type=Path)
    gemm_state.add_argument("--format", choices=("json", "md"), default="json")
    gemm_state.add_argument("--output", type=Path)
    training_pipeline = sub.add_parser("training-pipeline-schedule", help="Qwen8 PP4 GPipe/1F1B events and activation lifetimes")
    training_pipeline.add_argument("--inputs", type=Path)
    training_pipeline.add_argument("--format", choices=("json", "md"), default="json")
    training_pipeline.add_argument("--output", type=Path)
    real_lifecycle = sub.add_parser("real-scaling-lifecycle", help="Real C4 fit to declared training and inference lifetime proxy")
    real_lifecycle.add_argument("--inputs", type=Path)
    real_lifecycle.add_argument("--format", choices=("json", "md"), default="json")
    real_lifecycle.add_argument("--output", type=Path)
    sub.add_parser("plot-real-scaling", help="Render source-backed fit and conditional lifecycle (optional Matplotlib)")
    profiles = sub.add_parser("workload-profiles", help="Archived 02-08 request distributions and nearest-rank p95")
    profiles.add_argument("--format", choices=("json", "md"), default="json")
    profiles.add_argument("--output", type=Path)
    for qwen_command, description in (("qwen36-forward", "Qwen3.6-35B-A3B real text operator ledger"),
                                  ("qwen36-capacity", "Qwen3.6 checkpoint and persistent-state capacity screen")):
        qwen_parser = sub.add_parser(qwen_command, help=description)
        qwen_parser.add_argument("--inputs", type=Path)
        qwen_parser.add_argument("--format", choices=("json", "md", "csv") if qwen_command == "qwen36-forward" else ("json", "md"), default="json")
        qwen_parser.add_argument("--output", type=Path)
    pool_parser = sub.add_parser("memory-pool-access", help="Pool capacity, declared periodic reads and replica failure dependencies")
    pool_parser.add_argument("--copies", type=int, default=1)
    pool_parser.add_argument("--format", choices=("json", "md"), default="json")
    pool_parser.add_argument("--output", type=Path)
    growing = sub.add_parser("growing-remote-kv", help="Growing history ownership, replica epochs and communication skeleton")
    growing.add_argument("--inputs", type=Path)
    growing.add_argument("--format", choices=("json", "md"), default="json")
    growing.add_argument("--output", type=Path)
    cohort = sub.add_parser("supernode-cohort-cost", help="Same eight cards: model capacity, replica queues, failure, SLO and declared cost")
    cohort.add_argument("--inputs", type=Path)
    cohort.add_argument("--format", choices=("json", "md"), default="json")
    cohort.add_argument("--output", type=Path)
    sequence_window = sub.add_parser("connection-sequence", help="Sequential requests with shared directional windows and pending ACKs")
    sequence_window.add_argument("--inputs", type=Path)
    sequence_window.add_argument("--format", choices=("json", "md"), default="json")
    sequence_window.add_argument("--output", type=Path)
    window = sub.add_parser("connection-window", help="Declared ACK/window/recovery events for a complete image request")
    window.add_argument("--inputs", type=Path)
    window.add_argument("--format", choices=("json", "md"), default="json")
    window.add_argument("--output", type=Path)
    streaming = sub.add_parser("image-request-streaming", help="Explicit image block dependencies, preview work and final delivery")
    streaming.add_argument("--inputs", type=Path)
    streaming.add_argument("--format", choices=("json", "md"), default="json")
    streaming.add_argument("--output", type=Path)
    picture = sub.add_parser("image-request-budget", help="Declared image file transfer, codec and complete-result budget")
    picture.add_argument("--inputs", type=Path)
    picture.add_argument("--format", choices=("json", "md"), default="json")
    picture.add_argument("--output", type=Path)
    sub.add_parser("plot-image-request", help="Figure12-1 image request path and bandwidth curves")
    gradient = sub.add_parser("hierarchical-gradient", help="Real gradient ownership and two-level DP physical resource bounds")
    gradient.add_argument("--inputs", type=Path)
    gradient.add_argument("--format", choices=("json", "md"), default="json")
    gradient.add_argument("--output", type=Path)
    sub.add_parser("plot-supernode-cost", help="Render exact deadline-cost staircases for experiment6-10")
    qwen35 = sub.add_parser("qwen35-forward", help="Qwen3.5 base-text reference operator ledger")
    qwen35.add_argument("--inputs", type=Path)
    qwen35.add_argument("--format", choices=("json", "md", "csv"), default="json")
    qwen35.add_argument("--output", type=Path)
    v3 = sub.add_parser('v3-forward', help='Pinned DeepSeek V3 base logical operators and expanded MLA')
    v3.add_argument('--inputs', type=Path)
    v3.add_argument('--format', choices=('json','md'), default='json')
    v3.add_argument('--output', type=Path)
    scaling = sub.add_parser('scaling-law', help='Controlled teaching fit, budget optimum and lifecycle sensitivity')
    scaling.add_argument('--inputs', type=Path)
    scaling.add_argument('--format', choices=('json','md'), default='json')
    scaling.add_argument('--output', type=Path)
    history = sub.add_parser('training-history', help='Archived training investment, proxy work and scoped conditional budgets')
    history.add_argument('--inputs', type=Path)
    history.add_argument('--format', choices=('json','md'), default='json')
    history.add_argument('--output', type=Path)
    ub = sub.add_parser('ub-scope', help='Declared eight-card one/two-server capacity and communication budget')
    ub.add_argument('--inputs', type=Path)
    ub.add_argument('--format', choices=('json','md'), default='json')
    ub.add_argument('--output', type=Path)
    lifecycle = sub.add_parser('environment-lifecycle', help='Clone/snapshot/prewarm budgets and separately archived process trials')
    lifecycle.add_argument('--inputs', type=Path)
    lifecycle.add_argument('--format', choices=('json','md'), default='json')
    lifecycle.add_argument('--output', type=Path)
    env = sub.add_parser('environment-resources', help='Archived CPU RSS and finite lifecycle resource accounting')
    env.add_argument('--inputs', type=Path)
    env.add_argument('--format', choices=('json','md'), default='json')
    env.add_argument('--output', type=Path)
    mm = sub.add_parser('multimodal-cache', help='Official Qwen3-VL EC/KV and declared E/PD pool bounds')
    mm.add_argument('--inputs', type=Path)
    mm.add_argument('--format', choices=('json','md'), default='json')
    mm.add_argument('--output', type=Path)
    fp8 = sub.add_parser('v4-fp8-linear', help='Pinned V4 FP8 Linear quantization, tiles and scale work')
    fp8.add_argument('--inputs', type=Path)
    fp8.add_argument('--format', choices=('json','md'), default='json')
    fp8.add_argument('--output', type=Path)
    costs = sub.add_parser('routing-cost', help='Fictional cache pricing and quality/deadline success costs')
    costs.add_argument('--inputs', type=Path)
    costs.add_argument('--format', choices=('json','md'), default='json')
    costs.add_argument('--output', type=Path)
    handoff = sub.add_parser('weight-handoff', help='Official Qwen EP weight distribution and phase allocations')
    handoff.add_argument('--inputs', type=Path)
    handoff.add_argument('--format', choices=('json','md'), default='json')
    handoff.add_argument('--output', type=Path)
    teacher = sub.add_parser('teacher-cache', help='Official final hidden versus full logits cache budget')
    teacher.add_argument('--inputs', type=Path)
    teacher.add_argument('--format', choices=('json', 'md'), default='json')
    teacher.add_argument('--output', type=Path)
    routing_meta = sub.add_parser('routing-metadata',help='Official routed-expert ID payload and identity/transport budget')
    routing_meta.add_argument('--inputs',type=Path)
    routing_meta.add_argument('--format',choices=('json','md'),default='json')
    routing_meta.add_argument('--output',type=Path)
    scale = sub.add_parser('dense-training-scale',help='Nominal Dense 6ND scale, deadlines and exact parameter bounds')
    scale.add_argument('--inputs',type=Path)
    scale.add_argument('--format',choices=('json','md'),default='json')
    scale.add_argument('--output',type=Path)
    deadline = sub.add_parser('training-deadline',help='Official matrix-work deadline and persistent-state device bounds')
    deadline.add_argument('--inputs',type=Path)
    deadline.add_argument('--format',choices=('json','md'),default='json')
    deadline.add_argument('--output',type=Path)
    resume = sub.add_parser('checkpoint-resume',help='Actual DCP resharded state and next-update verification')
    resume.add_argument('--format',choices=('json','md'),default='json')
    resume.add_argument('--output',type=Path)
    checkpoint_fault_parser = sub.add_parser('checkpoint-fault',help='Actual DCP process termination before metadata commit')
    checkpoint_fault_parser.add_argument('--format',choices=('json','md'),default='json')
    checkpoint_fault_parser.add_argument('--output',type=Path)
    baseline = sub.add_parser('checkpoint-baseline',help='Archived matched CPU no-save, sync and async training windows')
    baseline.add_argument('--format',choices=('json','md'),default='json')
    baseline.add_argument('--output',type=Path)
    interval = sub.add_parser('checkpoint-interval',help='Checkpoint interval, first-order loss and Poisson retry sensitivity')
    interval.add_argument('--inputs',type=Path)
    interval.add_argument('--format',choices=('json','md'),default='json')
    interval.add_argument('--output',type=Path)
    saving = sub.add_parser('checkpoint-async',help='Finite snapshot buffers, save barriers and durable recovery points')
    saving.add_argument('--inputs',type=Path)
    saving.add_argument('--format',choices=('json','md'),default='json')
    saving.add_argument('--output',type=Path)
    reshard = sub.add_parser('checkpoint-reshard',help='Logical checkpoint ranges and source/destination byte offsets')
    reshard.add_argument('--inputs',type=Path)
    reshard.add_argument('--format',choices=('json','md'),default='json')
    reshard.add_argument('--output',type=Path)
    casting = sub.add_parser('gradient-cast',help='Gradient casting placement, transfer and live buffer capacity')
    casting.add_argument('--inputs',type=Path)
    casting.add_argument('--format',choices=('json','md'),default='json')
    casting.add_argument('--output',type=Path)
    training = sub.add_parser('training-state',help='Full-parameter Adam and explicit ZeRO persistent state capacity')
    training.add_argument('--inputs',type=Path)
    training.add_argument('--format',choices=('json','md'),default='json')
    training.add_argument('--output',type=Path)
    residency = sub.add_parser('cache-residency',help='Immutable page residency, tier capacity and exact byte-seconds')
    residency.add_argument('--inputs',type=Path)
    residency.add_argument('--format',choices=('json','md'),default='json')
    residency.add_argument('--output',type=Path)
    fault = sub.add_parser('cache-fault',help='Actual corrupted-page fallback and censored wait-complete request')
    fault.add_argument('--format',choices=('json','md'),default='json')
    fault.add_argument('--output',type=Path)
    missing = sub.add_parser('cache-missing',help='Actual missing KV pages, recomputation and BF16 differences')
    missing.add_argument('--format',choices=('json','md'),default='json')
    missing.add_argument('--output',type=Path)
    restart = sub.add_parser('cache-restart',help='Verified persisted KV files, read bytes and reusable prefix after restart')
    restart.add_argument('--format',choices=('json','md'),default='json')
    restart.add_argument('--output',type=Path)
    pressure = sub.add_parser('router-pressure',help='Measured cache/queue choice with target and whole-pair outcomes')
    pressure.add_argument('--format',choices=('json','md'),default='json')
    pressure.add_argument('--output',type=Path)
    router = sub.add_parser('router-trace',help='Archived native router hits, worker identity and model work')
    router.add_argument('--policy',choices=router_trace.POLICIES,default='cache_aware')
    router.add_argument('--format',choices=('json','md'),default='json')
    router.add_argument('--output',type=Path)
    cache = sub.add_parser('cache-route',help='Queue/cache readiness, remote recovery and stale-hit tail risk')
    cache.add_argument('--inputs',type=Path)
    cache.add_argument('--format',choices=('json','md'),default='json')
    cache.add_argument('--output',type=Path)
    payback = sub.add_parser('replica-payback',help='Cold expert replica copy, per-rank capacity and strict amortization')
    payback.add_argument('--inputs',type=Path)
    payback.add_argument('--format',choices=('json','md'),default='json')
    payback.add_argument('--output',type=Path)
    grouped = sub.add_parser('grouped-experts',help='Per-expert GEMM padding, tile traffic and rank imbalance')
    grouped.add_argument('--inputs',type=Path)
    grouped.add_argument('--format',choices=('json','md'),default='json')
    grouped.add_argument('--output',type=Path)
    locality = sub.add_parser('expert-locality',help='Official expert weight reuse and CPU/GPU path accounting')
    locality.add_argument('--inputs',type=Path)
    locality.add_argument('--format',choices=('json','md'),default='json')
    locality.add_argument('--output',type=Path)
    pool = sub.add_parser('pd-pool',help='Integer prefill/decode pools in common request units')
    pool.add_argument('--inputs',type=Path)
    pool.add_argument('--format',choices=('json','md'),default='json')
    pool.add_argument('--output',type=Path)
    handoff = sub.add_parser('pd-af-handoff',help='PD snapshot and serial AF handoff resources')
    handoff.add_argument('--inputs',type=Path)
    handoff.add_argument('--format',choices=('json','md'),default='json')
    handoff.add_argument('--output',type=Path)
    quality = sub.add_parser('kv-quality',help='Archived KV storage and natural retrieval quality with Q control')
    quality.add_argument('--run',choices=kv_quality.RUNS,default='bf16')
    quality.add_argument('--format',choices=('json','md'),default='json')
    quality.add_argument('--output',type=Path)
    offload = sub.add_parser('weight-offload',help='Official FFN offload capacity and finite-buffer prefetch')
    offload.add_argument('--inputs',type=Path)
    offload.add_argument('--format',choices=('json','md'),default='json')
    offload.add_argument('--output',type=Path)
    codec = sub.add_parser('kv-codec',help='Official GQA quantized KV blocks and explicit conversion cost')
    codec.add_argument('--inputs',type=Path)
    codec.add_argument('--format',choices=('json','md'),default='json')
    codec.add_argument('--output',type=Path)
    layout = sub.add_parser('gguf-layout',help='Actual GGUF mixed tensor types, scale metadata and file padding')
    layout.add_argument('--variant',choices=('Q2_K','Q4_K_M'),default='Q2_K')
    layout.add_argument('--format',choices=('json','md'),default='json')
    layout.add_argument('--output',type=Path)
    gguf = sub.add_parser('gguf-inventory',help='Pinned actual GGUF shard sizes and declared memory/KV budget')
    gguf.add_argument('--inputs',type=Path)
    gguf.add_argument('--format',choices=('json','md'),default='json')
    gguf.add_argument('--output',type=Path)
    service = sub.add_parser('service-replay',help='Actual request delivery and joint timing SLO')
    service.add_argument('--inputs',type=Path)
    service.add_argument('--format',choices=('json','md'),default='json')
    service.add_argument('--output',type=Path)
    iteration = sub.add_parser('iteration-batching',help='Fixed, continuous and chunked request scheduling')
    iteration.add_argument('--inputs',type=Path)
    iteration.add_argument('--format',choices=('json','md'),default='json')
    iteration.add_argument('--output',type=Path)
    reuse = sub.add_parser('batch-reuse',help='Official Qwen batch weight reuse and per-request KV crossover')
    reuse.add_argument('--inputs',type=Path)
    reuse.add_argument('--format',choices=('json','md'),default='json')
    reuse.add_argument('--output',type=Path)
    chunk = sub.add_parser('chunk-history',help='Archived equal-size prefill timing and official matrix work')
    chunk.add_argument('--format',choices=('json','md'),default='json')
    chunk.add_argument('--output',type=Path)
    dflash = sub.add_parser('dflash-work',help='Official DFlash checkpoint matrices and feature/KV bytes')
    dflash.add_argument('--inputs',type=Path)
    dflash.add_argument('--format',choices=('json','md'),default='json')
    dflash.add_argument('--output',type=Path)
    budget = sub.add_parser('speculative-budget',help='Finite-output draft selection with one-time preparation cost')
    budget.add_argument('--inputs',type=Path)
    budget.add_argument('--format',choices=('json','md'),default='json')
    budget.add_argument('--output',type=Path)
    sampling = sub.add_parser('speculative-sampling',help='Exact rejection correction and biased resampling counterexample')
    sampling.add_argument('--inputs',type=Path)
    sampling.add_argument('--format',choices=('json','md'),default='json')
    sampling.add_argument('--output',type=Path)
    speculative = sub.add_parser('speculative-round',help='Accepted-length distribution, delivered work and target KV rollback')
    speculative.add_argument('--inputs',type=Path)
    speculative.add_argument('--format',choices=('json','md'),default='json')
    speculative.add_argument('--output',type=Path)
    apc = sub.add_parser('apc-trace',help='Archived Agent prefix hits and official saved matrix work')
    apc.add_argument('--run',choices=apc_trace.RUNS,default='cache6')
    apc.add_argument('--format',choices=('json','md'),default='json')
    apc.add_argument('--output',type=Path)
    prefix = sub.add_parser('prefix-value',help='Independent prefix cache value and exact capacity choice')
    prefix.add_argument('--inputs',type=Path)
    prefix.add_argument('--format',choices=('json','md'),default='json')
    prefix.add_argument('--output',type=Path)
    restore = sub.add_parser('kv-restore',help='KV keep/offload/recompute with an explicit next-use window')
    restore.add_argument('--inputs',type=Path)
    restore.add_argument('--format',choices=('json','md'),default='json')
    restore.add_argument('--output',type=Path)
    kvtrace = sub.add_parser('kv-trace',help='Recount archived vLLM KV blocks, preemption and cancellation')
    kvtrace.add_argument('--run',choices=('small','large','cancel'),default='small')
    kvtrace.add_argument('--format',choices=('json','md'),default='json')
    kvtrace.add_argument('--output',type=Path)
    pages = sub.add_parser('kv-pages',help='KV paging, reference counts, fork COW and safe-point cancellation')
    pages.add_argument('--inputs',type=Path)
    pages.add_argument('--format',choices=('json','md'),default='json')
    pages.add_argument('--output',type=Path)
    remote = sub.add_parser('remote-state',help='Repeated remote KV snapshot reads versus staging locally')
    remote.add_argument('--inputs',type=Path)
    remote.add_argument('--format',choices=('json','md'),default='json')
    remote.add_argument('--output',type=Path)
    rpc = sub.add_parser('rpc-trace',help='Recompute archived RPC stages and paired differences')
    rpc.add_argument('--payload-bytes',type=int,default=1048576)
    rpc.add_argument('--format',choices=('json','md'),default='json')
    rpc.add_argument('--output',type=Path)
    reclaim = sub.add_parser('completion-reclaim',help='Outstanding credits and periodic completion consumption')
    reclaim.add_argument('--inputs',type=Path)
    reclaim.add_argument('--format',choices=('json','md'),default='json')
    reclaim.add_argument('--output',type=Path)
    ordering = sub.add_parser('operation-ordering',help='Publication dependencies and stale-read ordering witness')
    ordering.add_argument('--inputs',type=Path)
    ordering.add_argument('--format',choices=('json','md'),default='json')
    ordering.add_argument('--output',type=Path)
    connections = sub.add_parser('connection-states',help='Local relations and isolated shared transport state accounting')
    connections.add_argument('--inputs',type=Path)
    connections.add_argument('--format',choices=('json','md'),default='json')
    connections.add_argument('--output',type=Path)
    tail = sub.add_parser('collective-tail',help='Rank readiness and finite completion trace counterfactuals')
    tail.add_argument('--inputs',type=Path)
    tail.add_argument('--format',choices=('json','md'),default='json')
    tail.add_argument('--output',type=Path)
    packets = sub.add_parser('packet-reorder',help='Striped payload, ordered delivery and explicit loss recovery')
    packets.add_argument('--inputs',type=Path)
    packets.add_argument('--format',choices=('json','md'),default='json')
    packets.add_argument('--output',type=Path)
    feedback = sub.add_parser('feedback-queue',help='Finite fluid buffer with explicit feedback delay and reduced rate')
    feedback.add_argument('--inputs',type=Path)
    feedback.add_argument('--format',choices=('json','md'),default='json')
    feedback.add_argument('--output',type=Path)
    queue = sub.add_parser('periodic-queue',help='Periodic external demand, fluid backlog and phase offsets')
    queue.add_argument('--inputs',type=Path)
    queue.add_argument('--format',choices=('json','md'),default='json')
    queue.add_argument('--output',type=Path)
    paths = sub.add_parser('collective-paths',help='First three recursive/Swing rounds on a directed physical ring')
    paths.add_argument('--model',default='qwen3-8b')
    paths.add_argument('--tokens',type=int,default=1024)
    paths.add_argument('--rounds',type=int,default=3)
    paths.add_argument('--bandwidth-bytes-per-second',type=int,default=50*10**9)
    paths.add_argument('--format',choices=('json','md'),default='json')
    paths.add_argument('--output',type=Path)
    allocation = sub.add_parser('topology-allocation',help='Periodic placement, directed cut and ring reconfiguration amortization')
    allocation.add_argument('--inputs',type=Path)
    allocation.add_argument('--format',choices=('json','md'),default='json')
    allocation.add_argument('--output',type=Path)
    overlap = sub.add_parser('microbatch-overlap', help='Two Qwen FFN microbatches, cold weight reads and paired contention')
    overlap.add_argument('--inputs',type=Path)
    overlap.add_argument('--format',choices=('json','md'),default='json')
    overlap.add_argument('--output',type=Path)
    dag = sub.add_parser('request-dag', help='Request dependencies, resource ordering and critical-path changes')
    dag.add_argument('--inputs',type=Path)
    dag.add_argument('--format',choices=('json','md'),default='json')
    dag.add_argument('--output',type=Path)
    persistent = sub.add_parser('persistent-tasks', help='Qwen row tiles, device tasks and explicit readiness overhead')
    persistent.add_argument('--model', default='qwen3-8b')
    for name,default in (('tokens',512),('tile-rows',64),('matrix-flops-per-second',200*10**12),('activation-elements-per-second',20*10**9),('host-launch-ns',5000),('task-dispatch-ns',500),('event-publish-ns',200)):
        persistent.add_argument('--'+name,type=int,default=default)
    persistent.add_argument('--format', choices=('json','md'), default='json')
    persistent.add_argument('--output',type=Path)
    runtime = sub.add_parser('runtime-trace', help='Recount archived FFN timing samples and Nsight events')
    runtime.add_argument('--tokens', type=int, default=32)
    runtime.add_argument('--format', choices=('json','md'), default='json')
    runtime.add_argument('--output', type=Path)
    sub.add_parser('plot-vl-stages', help='Render image encoding and language stage work (optional Matplotlib)')
    sub.add_parser('plot-collective-paths',help='Render directed physical link loads from verified results')
    sub.add_parser('plot-specialization', help='Render figure 5-6 from verified results (optional Matplotlib)')
    specialization = sub.add_parser('shape-specialization', help='Generic, bucketed and exact Qwen FFN preparation and reuse')
    specialization.add_argument('--inputs', type=Path)
    specialization.add_argument('--format', choices=('json','md'), default='json')
    specialization.add_argument('--output', type=Path)
    deployment = sub.add_parser('optimization-deployment', help='Shape scores, frequency weighting, fallback and preparation amortization')
    deployment.add_argument('--inputs', type=Path)
    deployment.add_argument('--format', choices=('json','md'), default='json')
    deployment.add_argument('--output', type=Path)
    graph = sub.add_parser('graph-execution', help='Graph boundary copies, FFN padding and exact reuse thresholds')
    graph.add_argument('--model', default='qwen3-8b')
    for name, default in (('input-tokens',256),('real-tokens',1536),('padded-tokens',2048),('copy-bandwidth-bytes-per-second',2*10**12),('device-ns',20000),('exposed-submit-ns',20000),('replay-ns',3000),('metadata-ns',2000),('indirect-ns',6000),('setup-ns',10**9),('calls',100000),('config-ns',20000),('segments',100),('device-speedup',4),('config-speedup',4)):
        graph.add_argument('--'+name, type=int, default=default)
    graph.add_argument('--format', choices=('json','md'), default='json')
    graph.add_argument('--output', type=Path)
    fifo = sub.add_parser('stream-buffer', help='FIFO capacity, layout slots and producer backpressure')
    fifo.add_argument('--model', default='qwen3-8b')
    for name, default in (('block-rows',64),('blocks',5),('first-produce',4),('produce-interval',1),('first-consume',5),('consume-interval',2),('budget-bytes',65536),('reorder-slots',2)):
        fifo.add_argument('--'+name, type=int, default=default)
    fifo.add_argument('--format', choices=('json','md'), default='json')
    fifo.add_argument('--output', type=Path)
    host = sub.add_parser('host-transfer',help='Qwen activation H2D with independent host/device slot release')
    host.add_argument('--model',default='qwen3-8b')
    for name,default in (('tokens',8192),('blocks',8),('host-slots',2),('device-slots',2),('prepare-ns',1000000),('consume-ns',4000000),('bandwidth-bytes-per-second',24*2**30)):
        host.add_argument('--'+name,type=int,default=default)
    host.add_argument('--format',choices=('json','md'),default='json')
    host.add_argument('--output',type=Path)
    attile = sub.add_parser('attention-tiles',help='One Qwen head under mixed-format buffer and causal tile scanning')
    attile.add_argument('--model',default='qwen3-8b')
    for name,default in (('tokens',8192),('capacity-bytes',131072),('kv-slots',1)):
        attile.add_argument('--'+name,type=int,default=default)
    attile.add_argument('--kv-blocks',nargs='+',type=int)
    attile.add_argument('--causal',action='store_true')
    attile.add_argument('--format',choices=('json','md'),default='json')
    attile.add_argument('--output',type=Path)
    softmax = sub.add_parser('online-softmax',help='Stable block states, empty identity and sequential/tree merging')
    softmax.add_argument('--inputs',type=Path,help='JSON object with scores, values, block_sizes')
    softmax.add_argument('--format',choices=('json','md'),default='json')
    softmax.add_argument('--output',type=Path)
    numeric = sub.add_parser('fusion-numerics',help='Exact E4M3FN and lost-state counterexamples')
    numeric.add_argument('--block-size',type=int,default=128)
    numeric.add_argument('--larger-first',action='store_true')
    numeric.add_argument('--format',choices=('json','md'),default='json')
    numeric.add_argument('--output',type=Path)
    quant = sub.add_parser('quantized-gemm',help='One expert projection: separate quantization versus fused rereads')
    quant.add_argument('--model',default='qwen3-235b-a22b')
    for name,default in (('tokens',4096),('tile-m',128),('tile-n',128),('tile-k',128)):
        quant.add_argument('--'+name,type=int,default=default)
    quant.add_argument('--format',choices=('json','md'),default='json')
    quant.add_argument('--output',type=Path)
    fusion = sub.add_parser('fusion-lifetime',help='Pointwise materialization boundaries and live tensor unions')
    fusion.add_argument('--model',default='qwen3-8b')
    fusion.add_argument('--tokens',type=int,default=1024)
    fusion.add_argument('--layout-copy',action='store_true')
    fusion.add_argument('--format',choices=('json','md'),default='json')
    fusion.add_argument('--output',type=Path)
    loops = sub.add_parser('loop-access',help='Pinned C loop array expressions and matching recorded samples')
    for name in ('m','k','n'): loops.add_argument('--'+name,type=int,default=64)
    loops.add_argument('--tiles',nargs='+',type=int)
    loops.add_argument('--format',choices=('json','md'),default='json')
    loops.add_argument('--output',type=Path)
    bank = sub.add_parser('bank-mapping', help='Scalar bank requests, padding and explicit broadcast')
    bank.add_argument('--stride-words',type=int,default=32)
    bank.add_argument('--access',choices=('row','column','same-word'),default='column')
    bank.add_argument('--ports',type=int,default=1)
    bank.add_argument('--broadcast',action='store_true')
    bank.add_argument('--format',choices=('json','md'),default='json')
    bank.add_argument('--output',type=Path)
    reduction = sub.add_parser('row-reduction', help='Qwen RMSNorm split groups, partials and rereads')
    reduction.add_argument('--model', default='qwen3-8b')
    for name, default in (('rows',1),('splits',8),('width-multiplier',1)):
        reduction.add_argument('--'+name,type=int,default=default)
    reduction.add_argument('--format',choices=('json','md'),default='json')
    reduction.add_argument('--output',type=Path)
    tiles = sub.add_parser('gemm-tiles', help='Qwen up-projection working capacity and next-level traffic')
    tiles.add_argument('--model', default='qwen3-8b')
    tiles.add_argument('--tokens', type=int, default=1024)
    tiles.add_argument('--tiles', nargs='+', type=int)
    tiles.add_argument('--tile-k', type=int, default=32)
    tiles.add_argument('--capacity-bytes', type=int, default=81920)
    tiles.add_argument('--input-buffers', type=int, default=1)
    tiles.add_argument('--order', choices=('output-stationary','k-outer'), default='output-stationary')
    tiles.add_argument('--format', choices=('json','md'), default='json')
    tiles.add_argument('--output', type=Path)
    audio = sub.add_parser('audio-timing', help='Explicit audio pipeline, jitter buffer, deadlines and mute response')
    audio.add_argument('--inputs', type=Path, help='JSON keyword inputs for audio timing')
    audio.add_argument('--format', choices=('json', 'md'), default='json')
    audio.add_argument('--output', type=Path)
    agent = sub.add_parser('agent-trace', help='Pinned real Agent rounds, prefix work and serial-path replacement')
    agent.add_argument('--trace', choices=('thinking-off', 'thinking-on'), default='thinking-off')
    agent.add_argument('--model-speedup', type=float, default=1)
    agent.add_argument('--selected-turn', type=int)
    agent.add_argument('--format', choices=('json', 'md'), default='json')
    agent.add_argument('--output', type=Path)
    trace = sub.add_parser('request-trace', help='Qwen paired lengths, FIFO service inputs and KV lifetime replay')
    trace.add_argument('--inputs', type=Path, help='JSON object with model, requests and workers')
    trace.add_argument('--format', choices=('json', 'md'), default='json')
    trace.add_argument('--output', type=Path)
    supply = sub.add_parser('rl-supply', help='Conditional RL stage service and shared-resource bounds')
    supply.add_argument('--inputs', type=Path, help='JSON object with cycle, supply and pool_speedups')
    supply.add_argument('--format', choices=('json', 'md'), default='json')
    supply.add_argument('--output', type=Path)
    rl = sub.add_parser('rl-cycle', help='Declared Qwen RL candidate/accepted cohort matrix and weight-transfer ledger')
    rl.add_argument('--model', default='qwen3-8b')
    for name, default in (('prompts', 8), ('samples-per-prompt', 4), ('prompt-tokens', 1024), ('output-tokens', 256),
                          ('accepted-samples', 16), ('update-epochs', 1), ('reference-passes', 1),
                          ('teacher-passes', 0), ('rollout-replicas', 1)):
        rl.add_argument('--' + name, type=int, default=default)
    rl.add_argument('--head-strategy', choices=('dense', 'compact'), default='dense')
    rl.add_argument('--format', choices=('json', 'md'), default='json')
    rl.add_argument('--output', type=Path)
    training = sub.add_parser('training-matrix', help='Dense forward/backward matrix work and explicit SFT head strategy')
    training.add_argument('--model', default='qwen3-8b')
    training.add_argument('--routing', choices=('balanced', 'concentrated'), default='balanced')
    for name, default in (('batch', 1), ('tokens', 8192), ('gradient-bytes', 4), ('master-weight-bytes', 4)):
        training.add_argument('--' + name, type=int, default=default)
    training.add_argument('--supervised-tokens', type=int)
    training.add_argument('--head-strategy', choices=('dense', 'compact'), default='dense')
    training.add_argument('--format', choices=('json', 'md'), default='json')
    training.add_argument('--output', type=Path)
    pipeline = sub.add_parser('pipeline-schedule', help='FIFO inference stages, links, feedback and boundary buffer lifetimes')
    pipeline.add_argument('--model', default='qwen3-8b')
    pipeline.add_argument('--buffer-slots', type=int)
    pipeline.add_argument('--stage-ns', nargs='+', type=int)
    pipeline.add_argument('--transfer-ns', nargs='*', type=int)
    for name, default in (('microbatches', 4), ('requests-per-microbatch', 1), ('steps', 4), ('feedback-ns', 100000)):
        pipeline.add_argument('--' + name, type=int, default=default)
    pipeline.add_argument('--format', choices=('json', 'md'), default='json')
    pipeline.add_argument('--output', type=Path)
    communication = sub.add_parser('dense-communication', help='Embedding/layer/logits/PP/token-feedback communication path')
    communication.add_argument('--model', default='qwen3-8b')
    for name, default in (('tp', 8), ('pp', 1), ('dp', 1), ('batch-per-replica', 1), ('tokens', 1),
                          ('bandwidth-bytes-per-second', 50000000000), ('startup-ns', 2000), ('logit-element-bytes', 4)):
        communication.add_argument('--' + name, type=int, default=default)
    communication.add_argument('--format', choices=('json', 'md'), default='json')
    communication.add_argument('--output', type=Path)
    placement = sub.add_parser('dense-placement', help='Explicit Qwen Dense/Llama70 TP/PP/DP shapes, KV head IDs and per-card budgets')
    placement.add_argument('--model', default='qwen3-8b')
    for name, default in (('tp', 8), ('pp', 1), ('dp', 1), ('batch-per-replica', 1), ('history', 8192), ('tokens', 1),
                          ('capacity-bytes', 24000000000), ('workspace-bytes', 2147483648)):
        placement.add_argument('--' + name, type=int, default=default)
    placement.add_argument('--format', choices=('json', 'md'), default='json')
    placement.add_argument('--output', type=Path)
    capacity = sub.add_parser('capacity-scan', help='Actual Qwen/Llama70 shapes, declared grouped storage and KV concurrency budgets')
    capacity.add_argument('--model', default='qwen3-8b')
    capacity.add_argument('--capacities', nargs='+', type=int)
    for name, default in (('length', 8192), ('workspace-bytes', 2147483648), ('group-size', 128), ('scale-bytes', 2)):
        capacity.add_argument('--' + name, type=int, default=default)
    capacity.add_argument('--format', choices=('json', 'md'), default='json')
    capacity.add_argument('--output', type=Path)
    dedup = sub.add_parser('moe-dedup', help='Token-identity routing, destination reuse and partial combine')
    dedup.add_argument('--model', default='qwen3-235b-a22b')
    dedup.add_argument('--pattern', choices=('clustered', 'spread'), default='clustered')
    dedup.add_argument('--routes', type=Path)
    for name, default in (('tokens-per-rank', 64), ('participants', 8), ('combine-element-bytes', 4),
                          ('bandwidth-bytes-per-second', 50000000000), ('startup-ns', 2000)):
        dedup.add_argument('--' + name, type=int, default=default)
    dedup.add_argument('--format', choices=('json', 'md'), default='json')
    dedup.add_argument('--output', type=Path)
    staging = sub.add_parser('numa-staging', help='Four-GPU ring physical PCIe/DRAM/intersocket traffic')
    staging.add_argument('--placement', choices=('all-a', 'sender-local'), default='all-a')
    staging.add_argument('--order', choices=('grouped', 'alternating'), default='grouped')
    for name, default in (('tokens', 1024), ('pcie-bytes-per-second', 12000000000), ('dram-bytes-per-second', 40000000000),
                          ('intersocket-bytes-per-second', 8000000000), ('startup-ns', 0)):
        staging.add_argument('--' + name, type=int, default=default)
    staging.add_argument('--format', choices=('json', 'md'), default='json')
    staging.add_argument('--output', type=Path)
    exchange = sub.add_parser('all-to-all', help='Explicit MoE assignment traffic and pairwise barrier rounds')
    exchange.add_argument('--model', default='qwen3-235b-a22b')
    for name, default in (('tokens-per-rank', 64), ('participants', 8), ('bandwidth-bytes-per-second', 50000000000), ('startup-ns', 2000)):
        exchange.add_argument('--' + name, type=int, default=default)
    exchange.add_argument('--routing', choices=('balanced', 'hotspot'), default='balanced')
    exchange.add_argument('--counts', type=Path)
    exchange.add_argument('--format', choices=('json', 'md'), default='json')
    exchange.add_argument('--output', type=Path)
    tree = sub.add_parser('tree-collective', help='Unsegmented binomial reduction/broadcast with per-rank traffic')
    tree.add_argument('--model', default='qwen3-8b')
    for name, default in (('batch', 1), ('tokens', 1), ('participants', 8), ('bandwidth-bytes-per-second', 50000000000), ('startup-ns', 2000)):
        tree.add_argument('--' + name, type=int, default=default)
    tree.add_argument('--format', choices=('json', 'md'), default='json')
    tree.add_argument('--output', type=Path)
    ring = sub.add_parser('ring-collective', help='Qwen Dense activation ring rounds, bytes and serial TP budget')
    ring.add_argument('--model', default='qwen3-8b')
    for name, default in (('batch', 1), ('tokens', 1), ('participants', 8), ('bandwidth-bytes-per-second', 50000000000), ('startup-ns', 2000)):
        ring.add_argument('--' + name, type=int, default=default)
    ring.add_argument('--format', choices=('json', 'md'), default='json')
    ring.add_argument('--output', type=Path)
    budget = sub.add_parser('decode-budget', help='Nominal 70B decode sensitivity with strict BF16 compute peak')
    for name, default in (('batch', 1), ('parameters', 70000000000), ('weight-bits', 8),
                          ('kv-history-bytes-per-request', 0), ('kv-append-bytes-per-request', 0),
                          ('workspace-bytes', 0), ('metadata-bytes', 0)):
        budget.add_argument('--' + name, type=int, default=default)
    budget.add_argument('--compute-multiplier', type=float, default=1.0)
    budget.add_argument('--bandwidth-multiplier', type=float, default=1.0)
    budget.add_argument('--format', choices=('json', 'md'), default='json')
    budget.add_argument('--output', type=Path)
    window = sub.add_parser('memory-concurrency', help='Independent transaction window versus interface bandwidth')
    window.add_argument('--model', default='qwen3-8b')
    for name, default in (('length', 8192), ('batch', 1), ('transactions', 128), ('transaction-bytes', 128),
                          ('latency-ns', 500), ('bandwidth-bytes-per-second', 1000000000000)):
        window.add_argument('--' + name, type=int, default=default)
    window.add_argument('--active-transactions',type=int)
    window.add_argument('--service-interval-ns',type=int)
    window.add_argument('--format', choices=('json', 'md'), default='json')
    window.add_argument('--output', type=Path)
    basics = sub.add_parser('resource-basics', help='Teaching units, per-card capacity and serial transfer budget')
    for name, default in (('parameters', 70000000000), ('weight-bits', 16), ('cards', 2),
                          ('card-capacity-bytes', 80000000000), ('state-bytes-per-card', 0),
                          ('workspace-bytes-per-card', 0), ('metadata-bytes-per-card', 0),
                          ('link-bits-per-second', 400000000000), ('messages', 1)):
        basics.add_argument('--' + name, type=int, default=default)
    basics.add_argument('--payload-bytes', type=int)
    basics.add_argument('--shard-parameters', type=Path, help='JSON list of parameter counts per card')
    basics.add_argument('--startup-seconds', type=float, default=0.000003)
    basics.add_argument('--link-efficiency', type=float, default=1.0)
    basics.add_argument('--format', choices=('json', 'md'), default='json')
    basics.add_argument('--output', type=Path)
    timeline = sub.add_parser('cache-sequence', help='Prompt reuse and cumulative decode cache payloads')
    timeline.add_argument('--model', default='qwen3-8b')
    timeline.add_argument('--batch', type=int, default=1)
    timeline.add_argument('--prompt', type=int, default=8192)
    timeline.add_argument('--steps', type=int, default=1024)
    timeline.add_argument('--prefix-hit', type=int, default=6144)
    timeline.add_argument('--element-bytes', type=int, default=2)
    timeline.add_argument('--recurrent-bytes', type=int, default=4)
    timeline.add_argument('--format', choices=('json', 'md'), default='json')
    timeline.add_argument('--output', type=Path)
    sequence = sub.add_parser("generate", help="Sum G subsequent decode forwards, excluding prompt prefill")
    sequence.add_argument("--model", default="qwen3-8b")
    sequence.add_argument("--batch", type=int, default=1)
    sequence.add_argument("--history", type=int, default=8192)
    sequence.add_argument("--steps", type=int, default=1024)
    sequence.add_argument("--format", choices=("json", "md"), default="json")
    sequence.add_argument("--output", type=Path)
    cache = sub.add_parser("state", help="Qwen3 Dense/MoE, V4 Flash/Pro or Kimi K3 state accounting")
    cache.add_argument("--model", required=True)
    cache.add_argument("--length", type=int, default=8192)
    cache.add_argument("--batch", type=int, default=1)
    cache.add_argument("--element-bytes", type=int, default=2)
    cache.add_argument("--recurrent-bytes", type=int, default=4)
    cache.add_argument("--mla-path", choices=("compact", "expanded"), default="compact")
    cache.add_argument("--format", choices=("json", "md"), default="json")
    cache.add_argument("--output", type=Path)
    expert = sub.add_parser('experts', help='Qwen MoE/V4/K3 FFN matrix ledger; not a full forward')
    expert.add_argument('--model', required=True)
    expert.add_argument('--batch', type=int, default=64)
    expert.add_argument('--tokens', type=int, default=1)
    expert.add_argument('--routing', choices=('balanced', 'concentrated'), default='balanced')
    expert.add_argument('--routing-counts', type=Path)
    expert.add_argument('--element-bytes', type=int, default=2)
    expert.add_argument('--format', choices=('json', 'md'), default='json')
    expert.add_argument('--output', type=Path)
    hc = sub.add_parser('hyper-connections', help='V4 mHC projection, Sinkhorn and residual arithmetic')
    hc.add_argument('--model', default='deepseek-v4-flash')
    hc.add_argument('--batch', type=int, default=1)
    hc.add_argument('--tokens', type=int, default=8192)
    hc.add_argument('--format', choices=('json', 'md'), default='json')
    hc.add_argument('--output', type=Path)
    va = sub.add_parser('v4-attention', help='V4 projection, compressor and index matrix work')
    va.add_argument('--model', default='deepseek-v4-flash')
    va.add_argument('--batch', type=int, default=1)
    va.add_argument('--tokens', type=int, default=8192)
    va.add_argument('--history', type=int, default=0)
    va.add_argument('--format', choices=('json', 'md'), default='json')
    va.add_argument('--output', type=Path)
    vf = sub.add_parser('v4-forward', help='Compose base-forward accounting; coverage gaps remain explicit')
    vf.add_argument('--model', default='deepseek-v4-flash')
    vf.add_argument('--batch', type=int, default=1)
    vf.add_argument('--tokens', type=int, default=8192)
    vf.add_argument('--history', type=int, default=0)
    vf.add_argument('--routing', choices=('balanced', 'concentrated'), default='balanced')
    vf.add_argument('--routing-counts', type=Path)
    vf.add_argument('--format', choices=('json', 'md'), default='json')
    vf.add_argument('--output', type=Path)
    kf = sub.add_parser('k3-forward', help='Kimi K3 text forward with explicit logical algorithm coverage')
    kf.add_argument('--batch', type=int, default=1)
    kf.add_argument('--tokens', type=int, default=8192)
    kf.add_argument('--history', type=int, default=0)
    kf.add_argument('--mla-path', choices=('expanded', 'compact'), default='expanded')
    kf.add_argument('--kda-algorithm', choices=('auto', 'recurrent', 'chunk'), default='auto')
    kf.add_argument('--chunk-size', choices=(32, 64), type=int, default=64)
    kf.add_argument('--output-head', choices=('last', 'all'), default='last')
    kf.add_argument('--routing', choices=('balanced', 'concentrated'), default='balanced')
    kf.add_argument('--routing-counts', type=Path)
    kf.add_argument('--format', choices=('json', 'md'), default='json')
    kf.add_argument('--output', type=Path)
    mla = sub.add_parser('k3-mla', help='Kimi K3 expanded reference vs compact MLA absorption')
    mla.add_argument('--batch', type=int, default=1)
    mla.add_argument('--tokens', type=int, default=8192)
    mla.add_argument('--history', type=int, default=0)
    mla.add_argument('--path', choices=('expanded', 'compact'), default='expanded')
    mla.add_argument('--format', choices=('json', 'md'), default='json')
    mla.add_argument('--output', type=Path)
    kda = sub.add_parser('k3-kda', help='Kimi K3 projection/conv and recurrent arithmetic baseline')
    kda.add_argument('--batch', type=int, default=1)
    kda.add_argument('--tokens', type=int, default=1)
    kda.add_argument('--history', type=int, default=8192)
    kda.add_argument('--format', choices=('json', 'md'), default='json')
    kda.add_argument('--output', type=Path)
    residual = sub.add_parser('k3-attn-res', help='Kimi K3 depth-dependent block Attention Residuals')
    residual.add_argument('--batch', type=int, default=1)
    residual.add_argument('--tokens', type=int, default=8192)
    residual.add_argument('--format', choices=('json', 'md'), default='json')
    residual.add_argument('--output', type=Path)
    chunk = sub.add_parser('k3-kda-chunk', help='Selected FLA chunk allocations and known live subsets')
    chunk.add_argument('--batch', type=int, default=1)
    chunk.add_argument('--tokens', type=int, default=8192)
    chunk.add_argument('--chunk-size', type=int, choices=(32, 64), default=64)
    chunk.add_argument('--format', choices=('json', 'md'), default='json')
    chunk.add_argument('--output', type=Path)
    sub.add_parser("reproduce", help="Generate all currently registered book scenarios")
    sub.add_parser("verify-results", help="Verify generated files and their code/config inputs are current")
    inventory = sub.add_parser("inventory", help="Audit source changes and pending calculation review")
    inventory.add_argument("--refresh", action="store_true")
    sub.add_parser("sync-outline", help="Insert verified generated results into current chapter Markdown")
    devices = sub.add_parser("hardware", help="Official specifications, with precision and sparsity separated")
    devices.add_argument("--format", choices=("json", "md"), default="json")
    devices.add_argument("--output", type=Path)
    devices.add_argument("--audit", action="store_true", help="Show field recording gaps; does not automatically accept source claims")
    bound = sub.add_parser("roofline", help="Resource bound with an exactly matched official peak")
    bound.add_argument("--device", required=True)
    bound.add_argument("--flops", required=True, type=int)
    bound.add_argument("--traffic-bytes", required=True, type=int)
    bound.add_argument("--precision", default="BF16")
    bound.add_argument("--accumulator", default="FP32")
    bound.add_argument("--unit", choices=("tensor", "vector", "cube"), default="tensor")
    bound.add_argument("--sparsity", choices=("dense", "structured"), default="dense")
    bound.add_argument("--sparse-eligible", action="store_true")
    bound.add_argument("--compute-efficiency", type=float, default=1.0)
    bound.add_argument("--bandwidth-efficiency", type=float, default=1.0)
    bound.add_argument("--format", choices=("json", "md"), default="json")
    bound.add_argument("--output", type=Path)
    gemm = sub.add_parser("projection-bound", help="Real Qwen3 Q projection: BF16/FP32 dense, cold-memory bounds")
    gemm.add_argument("--model", default="qwen3-8b")
    gemm.add_argument("--device", required=True)
    gemm.add_argument("--batch", type=int, default=1)
    gemm.add_argument("--tokens", type=int, default=1)
    gemm.add_argument("--format", choices=("json", "md"), default="json")
    gemm.add_argument("--output", type=Path)
    return command


def model_list() -> list[dict]:
    """List root and component configurations without assuming a text-model layout."""
    configurations = {}
    for row in records():
        path = row.get('file', '')
        upstream = row.get('upstream_file', '')
        if (path.startswith('configs/models/') and path.endswith('/config.json')
                or upstream == 'config.json' or upstream.endswith('/config.json')):
            configurations.setdefault(row['model'], []).append(row)
    stage_commands = {
        'qwen3-vl-4b': ['vision-encoding', 'vl-request', 'multimodal-cache'],
        'qwen3-omni-30b-a3b-instruct': ['omni-understanding', 'omni-vision-encoding', 'omni-audio-encoder', 'omni-audio'],
        'fish-audio-s2-pro': ['omni-audio'],
        'minimax-h3': ['video-generation'],
        'wan2.2-ti2v-5b': ['video-generation'],
        'qwen-image-2512': ['image-generation'],
        'flux2-klein-4b': ['image-generation'],
    }
    base_commands = {'kimi-k3': 'k3-forward', 'deepseek-v4-flash': 'v4-forward',
                     'deepseek-v4-pro': 'v4-forward', 'deepseek-v3': 'v3-forward', 'qwen3.5-397b-a17b': 'qwen35-forward', 'qwen3.6-35b-a3b': 'qwen36-forward'}
    result = []
    for model, sources in sorted(configurations.items()):
        root = next((row for row in sources
                     if row.get('file') == f'configs/models/{model}/config.json'), None)
        kind = (model_config(model).get('model_type')
                if root and root['status'] == 'downloaded' else None)
        dense_or_moe = kind in ('qwen3', 'qwen3_moe')
        source = root or sources[0]
        result.append(dict(model=model, revision=source['revision'],
            config=source['status'],
            config_layout='root' if root else 'components',
            component_configs=[dict(file=row['file'],status=row['status'],revision=row['revision'])
                               for row in sources],
            forward='implemented' if dense_or_moe or (kind == 'llama' and model == 'deepseek-r1-distill-llama-70b') else 'pending',
            base_forward_ledger=base_commands.get(model),
            stage_calculations=stage_commands.get(model, []),
            stage_scope='Declared operators and scenarios; not complete runtime or measured performance',
            expert_matrices='implemented' if kind == 'qwen3_moe' or model in (
                'deepseek-v4-flash','deepseek-v4-pro','kimi-k3') else 'not_applicable_or_pending',
            state='implemented' if dense_or_moe or model in (
                'deepseek-v4-flash','deepseek-v4-pro','kimi-k3') else 'pending'))
    return result


def main(argv: list[str] | None = None) -> None:
    command = parser()
    args = command.parse_args(argv)
    try:
        if args.command == "models":
            result = model_list()
        elif args.command == "verify-sources":
            result = verify_sources()
        elif args.command == "fetch":
            result = fetch_sources(args.model)
        elif args.command == "forward":
            counts = json.loads(args.routing_counts.read_text()) if args.routing_counts else None
            result = model_forward(args.model, Scenario(batch=args.batch, history=args.history, tokens=args.tokens,
                                     output_head=args.output_head, score_bytes=args.score_bytes), args.routing, counts)
        elif args.command == 'k3-forward':
            counts = json.loads(args.routing_counts.read_text()) if args.routing_counts else None
            result = k3_forward.calculate(args.batch, args.tokens, args.history, args.mla_path,
                                          args.kda_algorithm, args.chunk_size, args.output_head, args.routing, counts)
        elif args.command == 'k3-kda-chunk':
            result = kda_chunk.calculate(args.batch, args.tokens, args.chunk_size)
        elif args.command == 'k3-attn-res':
            result = attn_res.calculate(args.batch, args.tokens)
        elif args.command == 'k3-kda':
            result = k3_kda.calculate(args.batch, args.tokens, args.history)
        elif args.command == 'k3-mla':
            result = k3_mla.calculate(args.batch, args.tokens, args.history, args.path)
        elif args.command == 'v4-forward':
            counts = json.loads(args.routing_counts.read_text()) if args.routing_counts else None
            result = v4_forward.calculate(args.model, args.batch, args.tokens, args.history, args.routing, counts)
        elif args.command == 'v4-attention':
            result = v4_attention.calculate(args.model, args.batch, args.tokens, args.history)
        elif args.command == 'hyper-connections':
            result = hyper_connections.calculate(args.model, args.batch, args.tokens)
        elif args.command == 'experts':
            counts = json.loads(args.routing_counts.read_text()) if args.routing_counts else None
            result = experts.calculate(args.model, args.batch, args.tokens, args.routing, counts, args.element_bytes)
        elif args.command == 'cache-sequence':
            result = cache_sequence.calculate(args.model, args.batch, args.prompt, args.steps, args.prefix_hit,
                                              args.element_bytes, args.recurrent_bytes)
        elif args.command == 'resource-basics':
            values = {key: value for key, value in vars(args).items() if key not in ('command', 'format', 'output')}
            values['shard_parameters'] = json.loads(args.shard_parameters.read_text()) if args.shard_parameters else None
            result = resource_basics.calculate(**values)
        elif args.command == 'memory-concurrency':
            result = memory_concurrency.calculate(**{key: value for key, value in vars(args).items()
                                                     if key not in ('command', 'format', 'output')})
        elif args.command == 'decode-budget':
            result = decode_budget.calculate(**{key: value for key, value in vars(args).items()
                                                if key not in ('command', 'format', 'output')})
        elif args.command == 'ring-collective':
            result = ring_collective.calculate(**{key: value for key, value in vars(args).items() if key not in ('command', 'format', 'output')})
        elif args.command == 'tree-collective':
            result = tree_collective.calculate(**{key: value for key, value in vars(args).items() if key not in ('command', 'format', 'output')})
        elif args.command == 'all-to-all':
            values = {key: value for key, value in vars(args).items() if key not in ('command', 'format', 'output')}
            values['counts'] = json.loads(args.counts.read_text()) if args.counts else None
            result = all_to_all.calculate(**values)
        elif args.command == 'numa-staging':
            result = numa_staging.calculate(**{key: value for key, value in vars(args).items() if key not in ('command', 'format', 'output')})
        elif args.command == 'moe-dedup':
            values = {key: value for key, value in vars(args).items() if key not in ('command', 'format', 'output')}
            values['routes'] = json.loads(args.routes.read_text()) if args.routes else None
            result = moe_dedup.calculate(**values)
        elif args.command == 'capacity-scan':
            result = capacity_scan.calculate(**{key: value for key, value in vars(args).items() if key not in ('command', 'format', 'output')})
        elif args.command == 'dense-placement':
            result = dense_placement.calculate(**{key: value for key, value in vars(args).items() if key not in ('command', 'format', 'output')})
        elif args.command == 'dense-communication':
            result = dense_communication.calculate(**{key: value for key, value in vars(args).items() if key not in ('command', 'format', 'output')})
        elif args.command == 'omni-vision-encoding':
            result = omni_vision_encoding.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'omni-understanding':
            result = omni_understanding.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'sequence-dependencies':
            result = sequence_dependencies.calculate()
        elif args.command == 'tpu-demand':
            result = tpu_demand.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'nic-budget':
            result = nic_budget.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'omni-audio-encoder':
            result = omni_audio_encoder.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'vl-request':
            result = vl_request.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'retry-paths':
            result = retry_paths.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'vision-encoding':
            result = vision_encoding.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'omni-audio':
            result = omni_audio.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'image-generation':
            result = image_generation.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'video-generation':
            result = video_generation.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command in ("flux-vae-decode", "architecture-variants"):
            module = flux_vae_decode if args.command == "flux-vae-decode" else architecture_variants
            result = module.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "v4-prefix-continuation":
            result = v4_prefix_continuation.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "qwen235-placement":
            result = qwen235_placement.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "dense-quantized-placement":
            result = dense_quantized_placement.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "request-model-comparison":
            result = request_model_comparison.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "fish-wave-export":
            result = fish_wave_export.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "strategy-record-cost":
            result = strategy_record_cost.calculate()
        elif args.command == "training-nonmatrix":
            result = training_nonmatrix.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "real-scaling-fit":
            result = real_scaling_fit.calculate()
        elif args.command == "v4-training-primitives":
            result = v4_training_primitives.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "v4-compressor-overlap":
            result = v4_compressor_overlap.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "v4-compressor-training":
            result = v4_compressor_training.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "v4-attention-projections":
            result = v4_attention_projections.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "v4-attention-training":
            result = v4_attention_training.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "v4-hc-training":
            result = v4_hc_training.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "stage-resource-bounds":
            result = stage_resource_bounds.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "v4-compressor-online":
            result = v4_compressor_online.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "training-input-supply":
            result = training_input_supply.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "qwen235-execution":
            result = qwen235_execution.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "qwen235-expert-granularity":
            result = qwen235_expert_granularity.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "architecture-tile-work":
            result = architecture_tile_work.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "plot-chat-agent":
            from .chat_agent_plot import render
            result = render()
        elif args.command == "plot-architecture-shapes":
            from .architecture_shape_plot import render
            result = render()
        elif args.command == "plot-capacity-curves":
            from .capacity_plot import render
            result = render()
        elif args.command == "trace-resource-bridge":
            result = trace_resource_bridge.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "paired-projection-cost":
            result = paired_projection_cost.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "matrix-vector-handoff":
            result = matrix_vector_handoff.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "v4-copy-coordinates":
            result = v4_copy_coordinates.calculate(rows=args.rows)
        elif args.command == "attention-input-pipeline":
            result = attention_input_pipeline.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "fa4-resource-balance":
            result = fa4_resource_balance.calculate()
        elif args.command == "storage-generation-comparison":
            result = storage_generation_comparison.calculate()
        elif args.command == "granularity-selection":
            result = granularity_selection.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "trace-cache-lifecycle":
            result = trace_cache_lifecycle.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "v4-mtp-forward":
            result = v4_mtp_forward.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "request-hardware-bridge":
            result = request_hardware_bridge.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "omni-audio-preprocess":
            result = omni_audio_preprocess.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "v4-optimizer":
            result = v4_optimizer.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "v4-moe-training":
            result = v4_moe_training.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "vision-preprocess":
            result = vision_preprocess.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "training-pipeline-gemm-state":
            result = training_pipeline_gemm_state.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "training-pipeline-schedule":
            result = training_pipeline_schedule.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "real-scaling-lifecycle":
            result = real_scaling_lifecycle.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "plot-real-scaling":
            from .real_scaling_plot import render
            result = render()
        elif args.command == "workload-profiles":
            result = workload_profiles.calculate()
        elif args.command == "connection-sequence":
            result = connection_sequence.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "connection-window":
            result = connection_window.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "image-request-streaming":
            result = image_request_streaming.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "image-request-budget":
            result = image_request_budget.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "plot-image-request":
            from .image_request_plot import render
            result = render()
        elif args.command == "hierarchical-gradient":
            result = hierarchical_gradient.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "supernode-cohort-cost":
            result = supernode_cohort_cost.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "plot-supernode-cost":
            from .supernode_cost_plot import render
            result = render()
        elif args.command == "growing-remote-kv":
            result = growing_remote_kv.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "memory-pool-access":
            result = memory_pool_access.calculate(copies=args.copies)
        elif args.command == "qwen36-forward":
            result = qwen36_forward.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "qwen36-capacity":
            result = qwen36_capacity.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == "qwen35-forward":
            result = qwen35_forward.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'v3-forward':
            result = v3_forward.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'reconfiguration':
            result = reconfiguration.calculate(json.loads(args.inputs.read_text()))
        elif args.command == 'scaling-law':
            result = scaling_law.calculate(json.loads(args.inputs.read_text()) if args.inputs else None)
        elif args.command == 'training-history':
            inputs = json.loads(args.inputs.read_text()) if args.inputs else {}
            if set(inputs) - {'comparisons', 'duration_scenarios', 'lifecycle'}:
                raise ValueError('training-history inputs accept comparisons, duration_scenarios and lifecycle only')
            result = training_history.calculate(**inputs)
        elif args.command == 'ub-scope':
            result = ub_scope.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'environment-lifecycle':
            result = environment_lifecycle.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'environment-resources':
            result = environment_resources.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'multimodal-cache':
            result = multimodal_cache.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'v4-fp8-linear':
            result = v4_fp8_linear.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'routing-cost':
            result = routing_cost.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'weight-handoff':
            result = weight_handoff.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'teacher-cache':
            result = teacher_cache.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'routing-metadata':
            result = routing_metadata.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'dense-training-scale':
            result = dense_training_scale.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'training-deadline':
            result = training_deadline.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'checkpoint-resume':
            result = checkpoint_resume.calculate()
        elif args.command == 'checkpoint-fault':
            result = checkpoint_fault.calculate()
        elif args.command == 'checkpoint-baseline':
            result = checkpoint_baseline.calculate()
        elif args.command == 'checkpoint-interval':
            result = checkpoint_interval.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'checkpoint-async':
            result = checkpoint_async.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'checkpoint-reshard':
            result = checkpoint_reshard.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'gradient-cast':
            result = gradient_cast.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'training-state':
            result = training_state.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'cache-residency':
            result = cache_residency.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'cache-fault':
            result = cache_fault.calculate()
        elif args.command == 'cache-missing':
            result = cache_missing.calculate()
        elif args.command == 'cache-restart':
            result = cache_restart.calculate()
        elif args.command == 'router-pressure':
            result = router_pressure.calculate()
        elif args.command == 'router-trace':
            result = router_trace.calculate(args.policy)
        elif args.command == 'cache-route':
            result = cache_route.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'replica-payback':
            result = replica_payback.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'grouped-experts':
            result = grouped_experts.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'expert-locality':
            result = expert_locality.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'pd-pool':
            result = pd_pool.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'pd-af-handoff':
            result = pd_af_handoff.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'kv-quality':
            result = kv_quality.calculate(args.run)
        elif args.command == 'weight-offload':
            result = weight_offload.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'kv-codec':
            result = kv_codec.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'gguf-layout':
            result = gguf_layout.calculate(args.variant)
        elif args.command == 'gguf-inventory':
            result = gguf_inventory.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'service-replay':
            result = service_replay.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'iteration-batching':
            result = iteration_batching.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'batch-reuse':
            result = batch_reuse.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'chunk-history':
            result = chunk_history.calculate()
        elif args.command == 'dflash-work':
            result = dflash_work.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'speculative-budget':
            result = speculative_budget.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'speculative-sampling':
            result = speculative_sampling.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'speculative-round':
            result = speculative_round.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'apc-trace':
            result = apc_trace.calculate(run=args.run)
        elif args.command == 'prefix-value':
            result = prefix_value.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'kv-restore':
            result = kv_restore.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'kv-trace':
            result = kv_trace.calculate(run=args.run)
        elif args.command == 'kv-pages':
            result = kv_pages.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'remote-state':
            result = remote_state.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'rpc-trace':
            result = rpc_trace.calculate(payload_bytes=args.payload_bytes)
        elif args.command == 'completion-reclaim':
            result = completion_reclaim.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'operation-ordering':
            result = operation_ordering.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'connection-states':
            result = connection_states.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'collective-tail':
            result = collective_tail.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'packet-reorder':
            result = packet_reorder.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'feedback-queue':
            result = feedback_queue.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'periodic-queue':
            result = periodic_queue.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'collective-paths':
            result = collective_paths.calculate(**{key:value for key,value in vars(args).items() if key not in ('command','format','output')})
        elif args.command == 'topology-allocation':
            result = topology_allocation.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'microbatch-overlap':
            result = microbatch_overlap.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'request-dag':
            result = request_dag.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'persistent-tasks':
            result = persistent_tasks.calculate(**{key:value for key,value in vars(args).items() if key not in ('command','format','output')})
        elif args.command == 'runtime-trace':
            result = runtime_trace.calculate(tokens=args.tokens)
        elif args.command == 'plot-vl-stages':
            from .vl_plot import render
            result = render()
        elif args.command == 'plot-collective-paths':
            from .collective_plot import render
            result = render()
        elif args.command == 'plot-specialization':
            from .specialization_plot import render
            result = render()
        elif args.command == 'shape-specialization':
            result = shape_specialization.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'optimization-deployment':
            result = optimization_deployment.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'graph-execution':
            result = graph_execution.calculate(**{key:value for key,value in vars(args).items() if key not in ('command','format','output')})
        elif args.command == 'stream-buffer':
            result = stream_buffer.calculate(**{key:value for key,value in vars(args).items() if key not in ('command','format','output')})
        elif args.command == 'host-transfer':
            result = host_transfer.calculate(**{key:value for key,value in vars(args).items() if key not in ('command','format','output')})
        elif args.command == 'attention-tiles':
            result = attention_tiles.calculate(**{key:value for key,value in vars(args).items() if key not in ('command','format','output')})
        elif args.command == 'online-softmax':
            result = online_softmax.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'fusion-numerics':
            result = fusion_numerics.calculate(**{key:value for key,value in vars(args).items() if key not in ('command','format','output')})
        elif args.command == 'quantized-gemm':
            result = quantized_gemm.calculate(**{key:value for key,value in vars(args).items() if key not in ('command','format','output')})
        elif args.command == 'fusion-lifetime':
            result = fusion_lifetime.calculate(**{key:value for key,value in vars(args).items() if key not in ('command','format','output')})
        elif args.command == 'loop-access':
            result = loop_access.calculate(**{key:value for key,value in vars(args).items() if key not in ('command','format','output')})
        elif args.command == 'bank-mapping':
            result = bank_mapping.calculate(**{key:value for key,value in vars(args).items() if key not in ('command','format','output')})
        elif args.command == 'row-reduction':
            result = row_reduction.calculate(**{key:value for key,value in vars(args).items() if key not in ('command','format','output')})
        elif args.command == 'gemm-tiles':
            result = gemm_tiles.calculate(**{key: value for key,value in vars(args).items() if key not in ('command','format','output')})
        elif args.command == 'audio-timing':
            result = audio_timing.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'agent-trace':
            result = agent_trace.calculate(**{key: value for key, value in vars(args).items() if key not in ('command', 'format', 'output')})
        elif args.command == 'request-trace':
            result = request_trace.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'rl-supply':
            result = rl_supply.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
        elif args.command == 'rl-cycle':
            result = rl_cycle.calculate(**{key: value for key, value in vars(args).items() if key not in ('command', 'format', 'output')})
        elif args.command == 'training-matrix':
            result = training_matrix.calculate(**{key: value for key, value in vars(args).items() if key not in ('command', 'format', 'output')})
        elif args.command == 'pipeline-schedule':
            result = pipeline_schedule.calculate(**{key: value for key, value in vars(args).items() if key not in ('command', 'format', 'output')})
        elif args.command == "generate":
            result = qwen3.generation(args.model, args.batch, args.history, args.steps)
        elif args.command == "state":
            result = state.calculate(args.model, args.length, args.batch, args.element_bytes,
                                     args.recurrent_bytes, args.mla_path)
        elif args.command == "reproduce":
            from .reproduce import run
            result = run()
        elif args.command == "verify-results":
            from .reproduce import verify_results
            result = verify_results()
        elif args.command == "hardware":
            result = hardware.catalog()
            if args.audit:
                result = hardware.audit_catalog(result)
        elif args.command == "inventory":
            from .inventory import audit
            result = audit(args.refresh)
        elif args.command == "sync-outline":
            from .outline import sync
            result = sync()
        elif args.command == "roofline":
            result = hardware.roofline(args.device, args.flops, args.traffic_bytes, args.precision,
                                      args.accumulator, args.unit, args.sparsity, args.sparse_eligible,
                                      args.compute_efficiency, args.bandwidth_efficiency)
        elif args.command == "projection-bound":
            result = projection.calculate(args.model, args.device, args.batch, args.tokens)
        fmt = getattr(args, "format", "json")
        if args.command == "hardware" and fmt == "md":
            text = hardware.markdown_audit(result) if args.audit else hardware.markdown_catalog(result)
        else:
            text = markdown(result) if fmt == "md" else operator_csv(result) if fmt == "csv" else json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        output = getattr(args, "output", None)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text)
        else:
            sys.stdout.write(text)
    except (ValueError, KeyError, OSError) as error:
        command.error(str(error))
