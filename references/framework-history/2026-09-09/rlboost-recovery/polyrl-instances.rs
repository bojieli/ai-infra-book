use tokio::time::Duration;
use crate::models::Instance;
use crate::state::AppState;

pub async fn health_check_instance(state: AppState, instance: Instance) {
    let endpoint = instance.endpoint();
    log::info!("Starting health check for instance: {}", endpoint);
    
    // Maximum wait time: 5 minutes
    let max_wait_time = Duration::from_secs(300);
    let check_interval = Duration::from_secs(2);
    let start_time = std::time::Instant::now();
    
    while start_time.elapsed() < max_wait_time {
        let health_url = format!("{}/health_generate", endpoint);
        
        match state.client.get(&health_url).send().await {
            Ok(response) => {
                if response.status().is_success() {
                    log::info!("Health check passed for instance: {}", endpoint);
                    state.add_instance_after_health_check(instance).await;
                    return;
                } else {
                    log::debug!("Health check failed for instance: {} (status: {})", endpoint, response.status());
                }
            }
            Err(e) => {
                log::debug!("Health check request failed for instance: {} (error: {})", endpoint, e);
            }
        }
        
        tokio::time::sleep(check_interval).await;
    }
    
    log::warn!("Health check timed out for instance: {} after {} seconds", endpoint, max_wait_time.as_secs());
    state.remove_from_pending(&instance.addr);
}

pub fn stats_check_worker(state: AppState) {
    tokio::spawn(async move {
        loop {
            // sleep for 2 seconds
            tokio::time::sleep(Duration::from_secs(1)).await;
            log::debug!("Checking stats for all instances");

            // loop through active instances
            let active_instances = state.active_instances.read().await;
            for instance in active_instances.iter() {
                let url = format!("{}/get_server_info", instance.endpoint());
                if let Ok(resp) = state.client.get(&url).timeout(Duration::from_secs(1)).send().await {
                    let response_json = resp.json::<serde_json::Value>().await.unwrap();
                    update_instance_stats(&state, instance, response_json);
                } else {
                    log::warn!("Timeout when query server info at {url}!");
                }
            }
            // Reset assigned batches counter after each stats check cycle
            state.assigned_batches.store(0, std::sync::atomic::Ordering::Relaxed);
            state.instances_available_notify.notify_waiters();
        }
    });
}

pub fn update_instance_stats(state: &AppState, instance: &Instance, response_json: serde_json::Value) {
    let last_gen_throughput = response_json["internal_states"][0]["last_gen_throughput"].as_f64().unwrap_or(0.0) as u64;
    let running_samples = response_json["internal_states"][0]["#running_req"].as_u64().unwrap_or(0) as usize;
    let queue_samples = response_json["internal_states"][0]["#queue_req"].as_u64().unwrap_or(0) as usize;
    if let Some(instance_state) = state.instances.get(&instance.addr) {
        instance_state.running_samples.store(running_samples, std::sync::atomic::Ordering::Relaxed);
        instance_state.queue_samples.store(queue_samples, std::sync::atomic::Ordering::Relaxed);
        instance_state.last_gen_throughput.store(last_gen_throughput, std::sync::atomic::Ordering::Relaxed);
    } else if let Some(instance_state) = state.local_instances.get(&instance.addr) {
        instance_state.running_samples.store(running_samples, std::sync::atomic::Ordering::Relaxed);
        instance_state.queue_samples.store(queue_samples, std::sync::atomic::Ordering::Relaxed);
        instance_state.last_gen_throughput.store(last_gen_throughput, std::sync::atomic::Ordering::Relaxed);
    } else {
        log::warn!("{} is neither local or remote", instance.endpoint());
    }
}   