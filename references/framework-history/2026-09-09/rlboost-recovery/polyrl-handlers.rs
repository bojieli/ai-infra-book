use std::net::SocketAddr;
use std::time::Instant;
use std::sync::atomic::Ordering;

use serde_json::Value;
use tokio::sync::mpsc;
use tokio::task::JoinHandle;
use uuid::Uuid;
use axum::extract::{Json, State};
use axum::http::StatusCode;
use axum::response::IntoResponse;
use axum_streams::*;
use futures::future::join_all;

use crate::models::*;
use crate::state::AppState;
use crate::instance_manager;
use crate::balance::TimingCollector;
use crate::utils::{
    adjust_sampling_params_for_used_tokens, build_final_response, build_partial_current_response, count_output_tokens, extend_input_ids_with_response_tokens
};

async fn create_register_response(
    state: &AppState, 
    instance: &Instance, 
    group_idx: usize, 
    num_engines_per_group: usize,
) -> (StatusCode, Json<RegisterResponse>) {
    let config = state.config.read().await;
    let resp = RegisterResponse {
        mooncake_transfer_device_name: config.mooncake_transfer_device_name.clone(),
        mooncake_transfer_protocol: config.mooncake_transfer_protocol.clone(),
        weight_sender_rpyc_endpoint: instance.weight_sender_endpoint.unwrap(),
        sender_group_idx: group_idx,
        num_mooncake_engines_per_group: num_engines_per_group,
    };
    (StatusCode::OK, Json(resp))
}

pub async fn register_rollout_instance(
    State(state): State<AppState>,
    Json(payload): Json<RegisterRequest>,
) -> impl IntoResponse {
    // Wait for weight senders if none are available
    state.wait_for_weight_senders().await;
    
    let addr: SocketAddr = match format!("{}:{}", payload.host, payload.port).parse() {
        Ok(addr) => addr,
        Err(_) => return (StatusCode::BAD_REQUEST, Json(serde_json::json!({"error": "invalid host:port format"}))).into_response(),
    };
    
    let mooncake_handshake_addr = if let Some(port) = payload.mooncake_handshake_port {
        match format!("{}:{}", payload.host, port).parse() {
            Ok(addr) => Some(addr),
            Err(_) => return (StatusCode::BAD_REQUEST, Json(serde_json::json!({"error": "invalid mooncake handshake host:port format"}))).into_response(),
        }
    } else {
        None
    };
        
    let mut instance = Instance::new(Uuid::new_v4(), addr, mooncake_handshake_addr);

    if state.instances.contains_key(&instance.addr) {
        log::info!("Instance already registered and ready: {}", instance.endpoint());
        return (StatusCode::CONFLICT, Json(serde_json::json!({"error": "instance already registered"}))).into_response();
    }

    if state.is_pending(&instance.addr) {
        log::info!("Instance already pending health check: {}", instance.endpoint());
        return (StatusCode::CONFLICT, Json(serde_json::json!({"error": "instance already pending health check"}))).into_response();
    }
    
    let (weight_sender, group_idx, num_engines_per_group) = state.get_next_weight_sender().await;
    instance.set_weight_sender(weight_sender);

    state.add_to_pending(&instance.addr);
    log::info!("Received registration request for instance: {} (id: {})", instance.endpoint(), instance.id);

    // Spawn health check task
    let state_clone = state.clone();
    tokio::spawn(async move {
        instance_manager::health_check_instance(state_clone, instance).await;
    });
    
    create_register_response(&state, &instance, group_idx, num_engines_per_group).await.into_response()
}

pub async fn update_weight_senders(
    State(state): State<AppState>,
    Json(payload): Json<UpdateWeightSendersRequest>,
) -> impl IntoResponse {
    {
        let mut config = state.config.write().await;
        
        // Update configuration values
        config.num_mooncake_groups_per_sender = payload.num_mooncake_groups_per_sender.unwrap_or(config.num_mooncake_groups_per_sender);
        config.num_mooncake_engines_per_group = payload.num_mooncake_engines_per_group.unwrap_or(config.num_mooncake_engines_per_group);
        
        // Convert IPs to endpoints using the base port and round-robin logic
        let base_port = config.weight_sender_rpyc_base_port;

        // weight_sender_ips is list of list: each inner list are ips from one node
        // For each node, filter by allowed_sender_ips and pick the first allowed ip
        let mut endpoints = Vec::new();
        let mut total_original_ips = 0usize;
        let mut total_filtered_ips = 0usize;
        for node_ips in &payload.weight_sender_ips {
            total_original_ips += node_ips.len();
            let filtered = crate::utils::filter_ips_by_config(node_ips, &config.allowed_sender_ips);
            total_filtered_ips += filtered.len();
            // choose first allowed ip if any
            if let Some(first_ip) = filtered.first() {
                let ip = first_ip.clone();
                match format!("{}:{}", ip, base_port).parse::<std::net::SocketAddr>() {
                    Ok(addr) => endpoints.push(addr),
                    Err(e) => {
                        log::error!("Failed to parse IP address {}:{}: {}", ip, base_port, e);
                        return (StatusCode::BAD_REQUEST, Json(serde_json::json!({
                            "error": format!("Invalid IP address: {}", ip)
                        }))).into_response();
                    }
                }
            } else {
                log::warn!("No allowed IPs found for a node after filtering; node_ips={:?}", node_ips);
            }
        }
        log::info!(
            "Filtered {} IPs from {} original IPs across {} nodes using allowed_sender_ips: {}",
            total_filtered_ips,
            total_original_ips,
            payload.weight_sender_ips.len(),
            config.allowed_sender_ips
        );
        if endpoints.is_empty() {
            return (StatusCode::BAD_REQUEST, Json(serde_json::json!({
                "error": "no valid weight sender endpoints after filtering"
            }))).into_response();
        }
        
        config.weight_sender_rpyc_endpoints = endpoints;
        
        log::info!("Updated weight sender endpoints: {:?} with {} groups per ip, {} engines will be initialized per group", 
                   config.weight_sender_rpyc_endpoints, config.num_mooncake_groups_per_sender, config.num_mooncake_engines_per_group);
    }
    
    // Notify any waiters that weight senders are now available
    state.weight_sender_register_notify.notify_waiters();
    
    (StatusCode::OK, Json(serde_json::json!({"success": true}))).into_response()
}

async fn collect_streaming_response(
    state: &AppState,
    instance: &Instance,
    request_body: &serde_json::Value,
    accumulated_response: Option<&serde_json::Value>,
) -> Result<serde_json::Value, (StatusCode, serde_json::Value)> {
    let url = format!("{}/generate", instance.endpoint());
    
    let mut stream_request = request_body.clone();
    stream_request["stream"] = serde_json::json!(true);
    
    // Append tokens from accumulated_response to input for continuation
    if let (Some(prev_response), Some(input_ids_val)) = (accumulated_response, stream_request.get_mut("input_ids")) {
        extend_input_ids_with_response_tokens(input_ids_val, prev_response);
    }
    
    match state.client.post(&url).json(&stream_request).send().await {
        Ok(mut res) => {
            if !res.status().is_success() {
                let status = res.status();
                let error_text = res.text().await.unwrap_or_else(|_| "Unknown error".to_string());
                return Err((StatusCode::BAD_GATEWAY, serde_json::json!({
                    "error": format!("server returned {}: {}", status, error_text),
                    "error_type": "server_error"
                })));
            }
                
                let accumulated = accumulated_response.cloned();
                
                // Determine if input is batch format (array of arrays)
                let is_batch_input = if let Some(input_ids) = request_body.get("input_ids") {
                    input_ids.as_array()
                        .map(|ids_array| !ids_array.is_empty() && ids_array[0].is_array())
                        .unwrap_or(false)
                } else {
                    panic!("input_ids is not set in request body");
                };
                
                let num_sub_requests = if is_batch_input {
                    request_body.get("input_ids")
                        .and_then(|ids| ids.as_array())
                        .map(|arr| arr.len())
                        .unwrap_or(1)
                } else {
                    1
                };
                
                // Track responses for each sub-request
                let mut current_received_responses: Vec<Option<serde_json::Value>> = vec![None; num_sub_requests];
                let mut line_buffer = String::new();
                
                // Process streaming response chunk by chunk
                loop {
                    match res.chunk().await {
                        Ok(Some(chunk)) => {
                            let chunk_str = String::from_utf8_lossy(&chunk);
                            line_buffer.push_str(&chunk_str);
                            
                            // Process complete lines
                            while let Some(newline_pos) = line_buffer.find('\n') {
                                let line = line_buffer[..newline_pos].to_string();
                                line_buffer.drain(..=newline_pos);
                                
                                if line.starts_with("data: ") {
                                    let json_str: &str = &line[6..];
                                    if json_str == "[DONE]" {
                                        // Build final response based on input format
                                        let final_response = if is_batch_input {
                                            // Always return array for batch input (even if single element)
                                            serde_json::json!(current_received_responses.into_iter().map(|r| r.unwrap_or(serde_json::json!({}))).collect::<Vec<_>>())
                                        } else {
                                            // Return single object for non-batch input
                                            current_received_responses.into_iter().next().unwrap().unwrap_or(serde_json::json!({}))
                                        };
                                        // Check if the finish reason is abort
                                        let is_abort = if final_response.is_array() {
                                            final_response.as_array().unwrap().iter().any(|sub_response| {
                                                let finish_reason_type = sub_response.get("meta_info")
                                                    .and_then(|m| m.get("finish_reason"))
                                                    .and_then(|f| f.get("type"))
                                                    .and_then(|t| t.as_str());
                                                finish_reason_type == Some("abort")
                                            })
                                        } else {
                                            let finish_reason_type = final_response.get("meta_info")
                                                .and_then(|m| m.get("finish_reason"))
                                                .and_then(|f| f.get("type"))
                                                .and_then(|t| t.as_str());
                                            finish_reason_type == Some("abort")
                                        };
                                        if is_abort {
                                            return Err((StatusCode::BAD_GATEWAY, serde_json::json!({
                                                "error": "stream aborted by engine",
                                                "error_type": "stream_abort",
                                                "partial_response": build_final_response(final_response, accumulated)
                                            })));
                                        } else {
                                            return Ok(build_final_response(final_response, accumulated));
                                        }
                                    }
                                    
                                    if let Ok(chunk_json) = serde_json::from_str::<serde_json::Value>(json_str) {
                                        // Handle streaming chunk - each chunk corresponds to one sub-request
                                        if let Some(index) = chunk_json.get("index").and_then(|i| i.as_u64()) {
                                            // Multi-request case: chunk has an index indicating which sub-request
                                            let idx = index as usize;
                                            if idx < current_received_responses.len() {
                                                current_received_responses[idx] = Some(chunk_json);
                                            }
                                        } else if !is_batch_input {
                                            // Single request case: no index needed
                                            current_received_responses[0] = Some(chunk_json);
                                        } else {
                                            log::error!("Streaming response missing index field");
                                            return Err((StatusCode::BAD_REQUEST, serde_json::json!({"error": "batch input requires index in streaming chunks"})));
                                        }
                                    }
                                }
                            }
                        }
                        Ok(None) => {
                            log::error!("Stream ended without [DONE]");
                            let partial_current = build_partial_current_response(is_batch_input, &current_received_responses);
                            let merged_partial = build_final_response(partial_current, accumulated.clone());
                            return Err((StatusCode::BAD_GATEWAY, serde_json::json!({
                                "error": "stream ended without [DONE]",
                                "error_type": "stream_error",
                                "partial_response": merged_partial
                            })));
                        }
                        Err(e) => {
                            log::error!("Stream error: {}", e);
                            let error_type = if e.is_timeout() { "timeout" } else if e.is_connect() { "connection_error" } else if e.is_decode() { "decode_error" } else { "stream_error" };
                            let partial_current = build_partial_current_response(is_batch_input, &current_received_responses);
                            let merged_partial = build_final_response(partial_current, accumulated.clone());
                            return Err((StatusCode::BAD_GATEWAY, serde_json::json!({
                                "error": format!("stream error: {}", e),
                                "error_type": error_type,
                                "partial_response": merged_partial
                            })));
                        }
                    }
                }
                
            }
        Err(e) => {
            let error_type = if e.is_timeout() { 
                "timeout" 
            } else if e.is_connect() { 
                "connection_error" 
            } else if e.is_decode() {
                "decode_error"
            } else if e.is_request() { 
                "request_error" 
            } else { 
                "unknown_error" 
            };
            
            log::error!("Failed to connect to {}: {} (type: {})", instance.endpoint(), e, error_type);
            
            // For connection errors before any streaming, we can only return the last accumulated response if present
            if let Some(partial) = accumulated_response {
                return Err((StatusCode::BAD_GATEWAY, serde_json::json!({
                    "error": format!("connection failed: {} ({})", e, error_type),
                    "error_type": error_type,
                    "partial_response": partial
                })));
            }
            
            // request error has no partial response field
            return Err((StatusCode::BAD_GATEWAY, serde_json::json!({
                "error": format!("connection failed: {} ({})", e, error_type),
                "error_type": error_type
            })));
        }
    }
}

async fn process_single_generate_request(
    state: &AppState,
    body: &GenerateRequest,
) -> Result<serde_json::Value, (StatusCode, serde_json::Value)> {
    let mut accumulated_response: Option<serde_json::Value> = None;
    let mut total_attempts = 0;
    const MAX_TOTAL_ATTEMPTS: u32 = 5;
    
    let original_request_body = body.0.clone();
    
    loop {
        if total_attempts >= MAX_TOTAL_ATTEMPTS {
            return Err((StatusCode::SERVICE_UNAVAILABLE, serde_json::json!({"error": "max attempts exceeded"})));
        }
        
        let (instance, is_local) = match state.next_instance_with_type().await {
            Some((inst, is_local)) => (inst, is_local),
            None => {
                log::warn!("No rollout instances registered for generate request");
                return Err((StatusCode::SERVICE_UNAVAILABLE, serde_json::json!({"error": "no rollout instances registered"})));
            }
        };
        
        log::debug!("Forwarding generate request to instance: {} ({})", instance.endpoint(), if is_local { "local" } else { "remote" });
        
        let mut request_body = original_request_body.clone();
        
        if let Some(prev_response) = &mut accumulated_response {
            if let Some(sampling_params) = request_body.get_mut("sampling_params") {
                adjust_sampling_params_for_used_tokens(sampling_params, prev_response);
            }
        }
        
        match collect_streaming_response(state, &instance, &request_body, accumulated_response.as_ref()).await {
            Ok(response) => {
                state.decrement_pending_request(&instance.addr).await;
                return Ok(response);
            }
            Err((status, error)) => {
                state.decrement_pending_request(&instance.addr).await;

                // Only retry on timeout or connection errors from remote instances
                let should_retry = total_attempts < MAX_TOTAL_ATTEMPTS - 1 &&
                    error.get("error_type")
                        .and_then(|t| t.as_str())
                        .map(|t| t == "timeout" || t == "connection_error" || t == "decode_error" || t == "stream_abort" || t == "request_error")
                        .unwrap_or(false);

                // FIXME: handle "request_error" when rollout instance fails when request is just sent, the response is empty, no need for concatente
                
                // FIXME(liuxs): condition of remove active_instance should not fully overlap retry
                if should_retry {
                    log::warn!("Stream failed on instance {} due to {} [ignore stream_abort], removing instance and attempting to continue with another instance", 
                        instance.endpoint(),
                        error.get("error_type").and_then(|t| t.as_str()).unwrap_or("unknown"));
                    
                    // remove instance out of active instances
                    if !is_local { // local instance is removed outside, request_error should not remove local instance
                        let mut active_instances = state.active_instances.write().await;
                        // TODO: retain is inefficient, impl active_instances with dash_map
                        active_instances.retain(|i| i.addr != instance.addr);
                    } // Lock released here
                                        
                    // if not local instance, also remove from instance list
                    if !is_local {
                        // Remove the failed instance from instances and active_instances
                        state.instances.remove(&instance.addr);
                        // Send shutdown command to the failed instance (don't wait for completion)
                        tokio::spawn(async move {
                            let url = format!("{}/shutdown?graceful=false", instance.endpoint());
                            let _ = reqwest::Client::new().post(&url).send().await;
                        });
                    }
                    
                    if let Some(partial_response) = error.get("partial_response") {
                        // request_error should have no accumulated response
                        assert!(error.get("error_type").and_then(|t| t.as_str()).is_some_and(|t| t != "request_error"));
                        accumulated_response = Some(partial_response.clone());
                    }
                    
                    total_attempts += 1;
                    continue;
                }
                
                return Err((status, error));
            }
        }
    }
}

pub async fn generate_request(
    State(state): State<AppState>,
    Json(body): Json<GenerateRequest>,
) -> impl IntoResponse {
    match process_single_generate_request(&state, &body).await {
        Ok(json) => (StatusCode::OK, Json(json)).into_response(),
        Err((status, error)) => (status, Json(error)).into_response(),
    }
}

#[derive(serde::Serialize)]
struct BatchResult {
    id: u64,
    success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    data: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    status_code: Option<u16>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<serde_json::Value>,
}

pub async fn timed_batch_generate_requests(
    State(state): State<AppState>,
    Json(payload): Json<BatchGenerationRequest>,
) -> impl IntoResponse {
    if payload.0.is_empty() {
        return (StatusCode::BAD_REQUEST, Json(serde_json::json!({"error": "no requests provided"}))).into_response();
    }

    let active_instances = state.active_instances.read().await;
    for instance in active_instances.iter() {
        log::debug!("Active instance {}", instance.endpoint());
    }
    drop(active_instances);

    let num_requests = payload.0.len();
    let (result_tx, mut result_rx) = mpsc::channel::<(BatchResult, Instant)>(num_requests * 2);
    
    let mut task_handles: Vec<JoinHandle<()>> = Vec::new();
    
    let mut batch_timer = TimingCollector::new();
    let mut local_gen_timer = TimingCollector::new();
    batch_timer.start();
    local_gen_timer.start();
        
    for (id, request) in payload.0 {
        let state_clone = state.clone();
        let result_tx_clone = result_tx.clone();
        
        let handle = tokio::spawn(async move {
            match process_single_generate_request(
                &state_clone, 
                &request).await {
                    Ok(json) => {
                        let _ = result_tx_clone.send((BatchResult {
                            id,
                            success: true,
                            data: Some(json),
                            status_code: None,
                            error: None,
                        }, Instant::now())).await;
                    },
                    Err((status_code, error)) => {
                        let _ = result_tx_clone.send((
                            BatchResult {
                                id,
                                success: false,
                                data: None,
                                status_code: Some(status_code.as_u16()),
                                error: Some(error),
                        }, Instant::now())).await;
                    return;
                }
            };
        });
        
        task_handles.push(handle);
    }

    // sleep a few seconds and abort all requests
    // TODO: remove local instances out of active instances before abort
    let max_gen_s = state.load_balance_state.get_max_local_instance_gen_s();
    log::debug!("All requests submitted, sleep {max_gen_s}s for local rollout");
    tokio::time::sleep(tokio::time::Duration::from_secs(max_gen_s)).await;
    // remove from active instances before abort
    let mut active_instances = state.active_instances.write().await;
    active_instances.retain(|inst| !state.local_instances.contains_key(&inst.addr));
    drop(active_instances);
    // we might still need a channel to drain the local results to make sure all aborted requests are received
    abort_local_requests_helper(&state).await;
    let local_gen_time_s = local_gen_timer.elapsed_s();
    // NOTE(liuxs): sleep additional 1s to let abortion finish
    tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
    drop(result_tx);
    
    let results_stream = async_stream::stream! {
        let mut response_tokens = Vec::new();
        let mut total_sub_responses = 0;
        log::debug!("Local rollout is done, yield notifier");
        yield BatchResult {id: 0, success: true, data: None, status_code: None, error: None};
        
        let mut latest_finish_time = None;
        while let Some((result, finish_time)) = result_rx.recv().await {
            if latest_finish_time.is_none() || finish_time > latest_finish_time.unwrap() {
                latest_finish_time = Some(finish_time);
            }
            if let Some(ref data) = result.data {
                let tokens = count_output_tokens(data, true);
                response_tokens.push(tokens);
                
                if data.is_array() {
                    total_sub_responses += data.as_array().unwrap().len();
                } else {
                    total_sub_responses += 1;
                }
            }
            
            yield result;
        }

        log::debug!("Stream done, yield all {} responses", total_sub_responses);
        
        for handle in task_handles {
            let _ = handle.await;
        }
        
        let total_gen_time_s = latest_finish_time.map_or(
            batch_timer.elapsed_s(),
            |finish_time| batch_timer.duration_s(finish_time),
        );
        
        if !response_tokens.is_empty() && total_sub_responses > 0 {
            let total_tokens: usize = response_tokens.iter().sum();
            let response_length_mean = total_tokens as f64 / total_sub_responses as f64;
            
            state.load_balance_state.update_generation_stats(total_gen_time_s, response_length_mean, local_gen_time_s);
            
            log::debug!("Generation completed: total_time={}s, local_gen_time={}s, response_len_mean={:.1}", 
                total_gen_time_s, local_gen_time_s, response_length_mean);
        }
    };

    StreamBodyAs::json_nl(results_stream).into_response()
}

pub async fn update_weight_version(
    State(state): State<AppState>,
) -> impl IntoResponse {
    let instances = state.get_all_instances();
    
    for instance in instances {
        if let Some(instance_state) = state.instances.get(&instance.addr) {
            let pending = instance_state.pending_batches.load(Ordering::Relaxed);
            if pending > 0 {
                log::error!("Instance {} has {} pending requests during weight version update", 
                    instance.endpoint(), pending);
            }
        }
    }
    
    let mut active_instances = state.active_instances.write().await;
    active_instances.clear();
    // NOTE(yongji): relaxed ordering should be enough
    let new_version = state.latest_weight_version.fetch_add(1, Ordering::AcqRel) + 1;
    // NOTE(liuxs): add local instance to active instances
    for instance_state in state.local_instances.iter() {
        if !active_instances.iter().any(|i| i.addr == instance_state.instance.addr) {
            active_instances.push(instance_state.instance);
        }
        log::debug!("Push local instance {} to active instances, pending {}", instance_state.instance.endpoint(), instance_state.pending_batches.load(Ordering::Relaxed));
    }
    drop(active_instances);
    
    log::info!("Updated weight version to {}", new_version);
    
    (StatusCode::OK, Json(serde_json::json!({
        "success": true,
        "new_weight_version": new_version
    })))
}

pub async fn get_receive_instances(
    State(state): State<AppState>,
    Json(payload): Json<GetReceiveInstancesRequest>,
) -> impl IntoResponse {
    let current_latest_version = state.latest_weight_version.load(Ordering::Relaxed);
    
    if payload.sender_weight_version < current_latest_version {
        log::warn!("Weight sender version {} is outdated, skipping", payload.sender_weight_version);
        return (StatusCode::OK, Json(GetReceiveInstancesResponse {
            instances: Vec::new(),
        }));
    } else if payload.sender_weight_version > current_latest_version {
        log::error!("Weight sender version {} is ahead of latest version {}, this should not happen", 
            payload.sender_weight_version, current_latest_version);
        return (StatusCode::CONFLICT, Json(GetReceiveInstancesResponse {
            instances: Vec::new(),
        }));
    }
    
    let all_instances = state.get_all_instances();
    let mut instances_to_update = Vec::new();
    
    for instance in all_instances {
        if let Some(ws_endpoint) = instance.weight_sender_endpoint {
            if ws_endpoint == payload.weight_sender_endpoint {
                if let Some(instance_state) = state.instances.get(&instance.addr) {
                    let current_version = instance_state.current_weight_version.load(Ordering::Relaxed);
                    if current_version < current_latest_version {
                        if instance_state.updating_weight.compare_exchange(false, true, Ordering::AcqRel, Ordering::Relaxed).is_ok() {
                            instances_to_update.push(InstanceWithVersion {
                                instance,
                                current_weight_version: current_version,
                            });
                            log::debug!("Instance {} scheduled for weight update (version {} -> {}) by weight sender {}", 
                                instance.endpoint(), current_version, current_latest_version, payload.weight_sender_endpoint);
                        } else {
                            log::warn!("Instance {} is already in weight updating state", instance.endpoint());
                        }
                    }
                }
            }
        }
    }

    (StatusCode::OK, Json(GetReceiveInstancesResponse {
        instances: instances_to_update,
    }))
}

async fn update_single_instance_weight(
    state: &AppState,
    instance: Instance,
    update_request: &UpdateWeightsFromAgentRequest,
) -> Result<(Instance, serde_json::Value), (StatusCode, String)> {
    let url = format!("{}/update_weights_from_agent", instance.endpoint());
    
    let res = state.client
        .post(&url)
        .json(update_request)
        .send()
        .await
        .map_err(|e| {
            (StatusCode::BAD_GATEWAY, format!("request to instance failed: {}", e))
        })?;
    
    let status = res.status();
    let json_response = res.json::<serde_json::Value>()
        .await
        .map_err(|e| {
            (StatusCode::BAD_GATEWAY, format!("failed to parse response from instance: {}", e))
        })?;
    
    if status.is_success() && json_response.get("success").and_then(|s| s.as_bool()) == Some(true) {
        Ok((instance, json_response))
    } else {
        Err((status, format!("weight update failed: status={}, response={:?}", status, json_response)))
    }
}

pub async fn update_weights(
    State(state): State<AppState>,
    Json(payload): Json<UpdateWeightsRequest>,
) -> impl IntoResponse {
    if payload.instance_endpoints.is_empty() {
        return (StatusCode::BAD_REQUEST, Json(serde_json::json!({"error": "no instance endpoints provided"})));
    }
    
    log::info!("Updating weights for {} instances to version {}", 
        payload.instance_endpoints.len(), payload.weight_version);
    
    let update_request = UpdateWeightsFromAgentRequest {
        tensors_meta: payload.tensors_meta,
        load_format: payload.load_format,
        flush_cache: payload.flush_cache,
        bootstrap: payload.bootstrap,
    };
    
    let mut results = Vec::new();
    let mut all_successful = true;
    let mut updated_instances = Vec::with_capacity(payload.instance_endpoints.len());
    let mut instances_to_update = Vec::with_capacity(payload.instance_endpoints.len());
    let mut missing_endpoints = Vec::new();

    for endpoint in &payload.instance_endpoints {
        if let Some(instance_state) = state.instances.get(endpoint) {
            log::debug!("Updating weights for instance: {}", instance_state.instance.endpoint());
            instances_to_update.push(instance_state.instance);
        } else {
            log::warn!("Instance {} not found in instances map", endpoint);
            missing_endpoints.push(endpoint.to_string());
            all_successful = false;
        }
    }

    let futures = instances_to_update
        .iter()
        .map(|instance| update_single_instance_weight(&state, *instance, &update_request));

    let task_results = join_all(futures).await;

    for (idx, result) in task_results.into_iter().enumerate() {
        let instance = instances_to_update[idx];
        let addr = instance.addr;
        let endpoint_str = instance.endpoint();
        match result {
            Ok((inst, json_response)) => {
                if let Some(instance_state) = state.instances.get(&addr) {
                    if !update_request.bootstrap {
                        instance_state.current_weight_version.store(payload.weight_version, Ordering::Relaxed);
                    }
                    let _ = instance_state.updating_weight.compare_exchange(true, false, Ordering::AcqRel, Ordering::Relaxed);
                }
                updated_instances.push(inst);
                results.push(serde_json::json!({
                    "instance_id": inst.id,
                    "endpoint": inst.endpoint(),
                    "status_code": 200,
                    "response": json_response
                }));
                log::info!("Weight update successful for instance {}", inst.endpoint());
            }
            Err((status_code, error_msg)) => {
                if let Some(instance_state) = state.instances.get(&addr) {
                    let _ = instance_state.updating_weight.compare_exchange(true, false, Ordering::AcqRel, Ordering::Relaxed);
                }
                all_successful = false;
                log::error!("Weight update failed for endpoint {}: {}", endpoint_str, error_msg);
                results.push(serde_json::json!({
                    "endpoint": endpoint_str,
                    "status_code": status_code.as_u16(),
                    "error": error_msg
                }));
            }
        }
    }

    for endpoint in missing_endpoints {
        results.push(serde_json::json!({
            "endpoint": endpoint,
            "status_code": 404,
            "error": "instance not found"
        }));
    }
    
    if !payload.bootstrap {
        let mut active_instances = state.active_instances.write().await;
        let current_latest_version = state.latest_weight_version.load(Ordering::Relaxed);
        
        if payload.weight_version == current_latest_version {
            log::info!("Adding {} instances to active pool", updated_instances.len());
            for instance in updated_instances {
                if !active_instances.iter().any(|ai| ai.addr == instance.addr) {
                    active_instances.push(instance);
                } else {
                    log::error!("Instance {} that just completed weight update is already in active pool", instance.endpoint());
                }
            }
            state.instances_available_notify.notify_waiters();
        } else {
            log::warn!("Weight version {} does not match latest version {}, skipping active pool update", 
                payload.weight_version, current_latest_version);
        }
        
        drop(active_instances);
    }
    
    if all_successful {
        log::info!("Weight update completed successfully for all instances");
        (StatusCode::OK, Json(serde_json::json!({ "success": true, "details": results })))
    } else {
        log::error!("Weight update failed for some instances");
        (StatusCode::MULTI_STATUS, Json(serde_json::json!({ "success": false, "details": results })))
    }
}

pub async fn health_check() -> impl IntoResponse {
    log::debug!("Health check requested");
    (StatusCode::OK, Json(serde_json::json!({"status": "healthy", "message": "Rollout manager is ready"})))
}

pub async fn get_instances_status(State(state): State<AppState>) -> impl IntoResponse {
    let instances = state.get_all_instances();
    
    // Only collect if we need the actual endpoints, use iterators for counts
    let pending_count = state.pending_instances.len();
    
    let ready_endpoints: Vec<String> = instances.iter().map(|i| i.endpoint()).collect();
    let pending_endpoints: Vec<String> = state.pending_instances.iter()
        .map(|entry| entry.key().to_string())
        .collect();
    
    let status = serde_json::json!({
        "ready_instances": instances.len(),
        "pending_instances": pending_count,
        "ready_instance_endpoints": ready_endpoints,
        "pending_instance_endpoints": pending_endpoints
    });
    
    (StatusCode::OK, Json(status))
}

pub async fn shutdown_instances_handler(
    State(state): State<AppState>,
    Json(payload): Json<ShutdownInstancesRequest>,
) -> impl IntoResponse {
    if payload.endpoints.is_empty() {
        return (StatusCode::BAD_REQUEST, Json(serde_json::json!({"error": "no endpoints provided"})));
    }
    
    
    log::info!("Received shutdown request for {} instances: {:?}", payload.endpoints.len(), payload.endpoints);
    
    let shutdown_endpoints = state.shutdown_instances(&payload.endpoints, payload.check_weight_update).await;
    
    let response = serde_json::json!({
        "success": true,
        "message": format!("Removed {} instances from active pool and shutdown commands sent", shutdown_endpoints.len()),
        "shutdown_endpoints": shutdown_endpoints
    });
    
    (StatusCode::OK, Json(response))
}

pub async fn register_local_rollout_instances(
    State(state): State<AppState>,
    Json(payload): Json<RegisterLocalInstancesRequest>,
) -> impl IntoResponse {
    let mut local_instances = Vec::new();
    
    for (host, port) in payload.0 {
        // FIXME(liuxs): localhost is not accepted
        let addr: SocketAddr = match format!("{}:{}", host, port).parse() {
            Ok(addr) => addr,
            Err(_) => return (StatusCode::BAD_REQUEST, Json(serde_json::json!({"error": "invalid host:port format"}))).into_response(),
        };
        
        let local_instance = Instance::new(Uuid::new_v4(), addr, None);
        local_instances.push(local_instance);
    }
    
    state.register_local_instances(local_instances).await;
    
    (StatusCode::OK, Json(serde_json::json!({"success": true}))).into_response()
}

pub async fn update_metrics(
    State(state): State<AppState>,
    Json(payload): Json<UpdateMetricsRequest>,
) -> impl IntoResponse {
    let config = state.config.read().await;
    // let train_batch_size = payload.train_batch_size.or(config.train_batch_size).unwrap_or(8);
    drop(config);
    
    let response_length_mean = state.load_balance_state.get_last_response_length_mean();
    let local_gen_time_s = state.load_balance_state.last_local_gen_time_s.load(std::sync::atomic::Ordering::Relaxed);
    let total_gen_time_s = state.load_balance_state.last_total_gen_time_s.load(std::sync::atomic::Ordering::Relaxed);

    let new_max_gen_s = state.load_balance_state.adjust_local_instances_gen_s(
        total_gen_time_s,
        payload.step_time_s,
        payload.trainer_bubble_time_s,
        state.instances.len() as u64,
        payload.step_throughput,
    );
    
    let response = serde_json::json!({
        "success": true,
        "new_max_gen_s": new_max_gen_s,
        "new_num_rollout_instances": state.instances.len(),
        "total_gen_time_s": total_gen_time_s,
        "local_gen_time_s": local_gen_time_s,
        "remote_wait_time_s": payload.trainer_bubble_time_s,
        "response_length_mean": response_length_mean,
    });
    
    log::info!("Load balance adjustment: total_gen={}s, local_gen={}s, total_step={}s, remote_wait={}s, response_len_mean={:.1}, new_max_gen_s={}", 
        total_gen_time_s, local_gen_time_s, payload.step_time_s, payload.trainer_bubble_time_s, response_length_mean, new_max_gen_s);
    
    (StatusCode::OK, Json(response)).into_response()
}

pub async fn abort_local_requests_helper(
    state: &AppState,
) -> Vec<Value> {
    let mut results = Vec::new();

    let local_instances: Vec<_> = state.local_instances.iter()
        .map(|entry| entry.value().instance)
        .collect();
    
    if local_instances.is_empty() {
        return results;
    }
    
    log::info!("Aborting requests on {} local instances", local_instances.len());
    
    for local_instance in local_instances {
        let url = format!("{}/abort_request", local_instance.endpoint());
        let abort_payload = serde_json::json!({
            "rid": "",
            "abort_all": true
        });

        log::debug!("Try to abort requests on {}", local_instance.endpoint());
        
        match state.client.post(&url).json(&abort_payload).send().await {
            Ok(res) => {
                let status = res.status();
                results.push(serde_json::json!({
                    "instance_id": local_instance.id,
                    "endpoint": local_instance.endpoint(),
                    "status_code": status.as_u16(),
                    "success": status.is_success()
                }));
                
                if status.is_success() {
                    log::debug!("Successfully aborted requests on {}", local_instance.endpoint());
                } else {
                    log::warn!("Failed to abort requests on {}: status {}", local_instance.endpoint(), status);
                }
            }
            Err(e) => {
                log::error!("Failed to send abort request to {}: {}", local_instance.endpoint(), e);
                results.push(serde_json::json!({
                    "instance_id": local_instance.id,
                    "endpoint": local_instance.endpoint(),
                    "status_code": 0,
                    "success": false,
                    "error": format!("connection failed: {}", e)
                }));
            }
        }
    }
    return results;
}

pub async fn abort_local_requests(
    State(state): State<AppState>,
) -> impl IntoResponse {
    let results = abort_local_requests_helper(&state).await;
    
    let successful_count = results.iter()
        .filter(|r| r.get("success").and_then(|s| s.as_bool()).unwrap_or(false))
        .count();
    
    (StatusCode::OK, Json(serde_json::json!({
        "success": true,
        "message": format!("aborted requests on {}/{} local instances", successful_count, results.len()),
        "results": results
    })))
}