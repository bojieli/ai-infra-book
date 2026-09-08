
use std::sync::{Arc, atomic::{AtomicUsize, AtomicBool, AtomicU64, Ordering}};
use std::net::SocketAddr;
use tokio::sync::{RwLock, Notify};
use dashmap::{DashMap, DashSet};
use crate::models::{Instance, Config};
use crate::balance::LoadBalanceState;

pub struct InstanceState {
    pub instance: Instance,
    pub pending_batches: AtomicUsize, // pending batches are number of uncompleted response groups
    pub running_samples: AtomicUsize, // running samples are abs number of running responses on the instance
    pub queue_samples: AtomicUsize, // queue samples are abs number of queued responses on the instance
    pub last_gen_throughput: AtomicU64, // last gen throughput in tokens per second
    pub updating_weight: AtomicBool,
    pub current_weight_version: AtomicU64,
}

pub struct LocalInstanceState {
    pub instance: Instance,
    pub pending_batches: AtomicUsize,
    pub running_samples: AtomicUsize,
    pub queue_samples: AtomicUsize,
    pub last_gen_throughput: AtomicU64,
}

#[derive(Clone)]
pub struct AppState {
    // Core instance management
    pub instances: Arc<DashMap<SocketAddr, InstanceState>>,
    pub pending_instances: Arc<DashSet<SocketAddr>>,
    
    // Round-robin counter for load balancing
    pub rr_counter: Arc<AtomicUsize>,
    pub assigned_batches: Arc<AtomicUsize>,
    
    // Configuration
    pub config: Arc<RwLock<Config>>,
    
    // Weight sender management  
    pub weight_sender_counter: Arc<AtomicUsize>,
    
    // HTTP client
    pub client: reqwest::Client,
    
    pub instances_available_notify: Arc<Notify>, // For instance registration and availability
    pub weight_sender_register_notify: Arc<Notify>, // For weight sender updates
    
    // Active remote instances
    pub latest_weight_version: Arc<AtomicU64>,
    pub active_instances: Arc<RwLock<Vec<Instance>>>, // Active instances available for requests
    
    // Local instances management
    pub local_instances: Arc<DashMap<SocketAddr, LocalInstanceState>>,
    
    // Load balancing state
    pub load_balance_state: Arc<LoadBalanceState>,
}

impl AppState {
    pub fn new(config: Config) -> Self {
        Self {
            instances: Arc::new(DashMap::new()),
            pending_instances: Arc::new(DashSet::new()),
            rr_counter: Arc::new(AtomicUsize::new(0)),
            assigned_batches: Arc::new(AtomicUsize::new(0)),
            config: Arc::new(RwLock::new(config)),
            weight_sender_counter: Arc::new(AtomicUsize::new(0)),
            client: reqwest::Client::builder()
                .tcp_keepalive(std::time::Duration::from_secs(30))
                .timeout(std::time::Duration::from_secs(3000))
                .build()
                .expect("failed building reqwest client"),
            instances_available_notify: Arc::new(Notify::new()),
            weight_sender_register_notify: Arc::new(Notify::new()),
            latest_weight_version: Arc::new(AtomicU64::new(0)),
            active_instances: Arc::new(RwLock::new(Vec::new())),
            local_instances: Arc::new(DashMap::new()),
            load_balance_state: Arc::new(LoadBalanceState::new(150)),
        }
    }


    pub async fn next_instance_with_type(&self) -> Option<(Instance, bool)> {
        // loop through active instances
        loop {
            let max_assigned_batches_per_stats_check = {
                let config = self.config.read().await;
                config.max_assigned_batches_per_stats_check
            };
            let active_instances = self.active_instances.read().await;
            
            let available_count = active_instances.len();
                
            if available_count == 0 {
                drop(active_instances);
                log::debug!("No available instances (all are shutting down), waiting for new instances");
                self.instances_available_notify.notified().await;
                continue;
            }
            
            // Atomic fetch-add with overflow check
            let current = self.assigned_batches.fetch_add(1, Ordering::Relaxed);
            if current < max_assigned_batches_per_stats_check {
                // We're under the limit, proceed with work
                let zero_queue_instances: Vec<&Instance> = active_instances.iter()
                    .filter(|instance| {
                        if let Some(instance_state) = self.instances.get(&instance.addr) {
                            let queued = instance_state.queue_samples.load(Ordering::Relaxed);
                            queued == 0
                        } else if let Some(instance_state) = self.local_instances.get(&instance.addr) {
                            let queued = instance_state.queue_samples.load(Ordering::Relaxed);
                            queued == 0
                        } else {
                            log::warn!("{} is neither local or remote", instance.endpoint());
                            false
                        }
                    })
                    .collect();
                
                if !zero_queue_instances.is_empty() {
                    // Round-robin among zero-queue instances
                    let start_idx = self.rr_counter.fetch_add(1, Ordering::Relaxed) % zero_queue_instances.len();
                    let instance = zero_queue_instances[start_idx];
                    
                    self.increment_pending_request(&instance.addr);
                    if instance.mooncake_handshake_addr.is_some() {
                        return Some((*instance, false));
                    } else {
                        return Some((*instance, true));
                    }
                } else {
                    // No zero-queue instances available, need to wait
                    drop(active_instances);
                    log::debug!("No instances with zero queue, waiting for availability");
                    self.instances_available_notify.notified().await;
                    // Note: We've already claimed quota but no instances available
                    // This is acceptable as the quota will be reset on next stats check
                }
            } else {
                // We exceeded the limit, just wait (no rollback needed - counter resets every stats check)
                drop(active_instances);
                log::debug!("Assigned batches limit reached ({}), waiting for stats check reset", max_assigned_batches_per_stats_check);
                self.instances_available_notify.notified().await;
            }
        }
    }
    
    pub async fn get_next_weight_sender(&self) -> (SocketAddr, usize, usize) {
        let config = self.config.read().await;
        if config.weight_sender_rpyc_endpoints.is_empty() {
            panic!("No weight sender endpoints available");
        }
        
        let total_groups = config.weight_sender_rpyc_endpoints.len() * config.num_mooncake_groups_per_sender;
        let counter = self.weight_sender_counter.fetch_add(1, Ordering::Relaxed) % total_groups;
        
        let group_idx = counter / config.weight_sender_rpyc_endpoints.len();
        let endpoint_idx = counter % config.weight_sender_rpyc_endpoints.len();
        
        (config.weight_sender_rpyc_endpoints[endpoint_idx], group_idx, config.num_mooncake_engines_per_group)
    }
    
    pub async fn wait_for_weight_senders(&self) {
        loop {
            let config = self.config.read().await;
            if !config.weight_sender_rpyc_endpoints.is_empty() {
                break;
            }
            drop(config);
            
            // Wait for notification of weight sender update
            self.weight_sender_register_notify.notified().await;
        }
    }
    
    pub fn get_all_instances(&self) -> Vec<Instance> {
        self.instances.iter()
            .map(|entry| entry.value().instance) // Copy instead of clone
            .collect()
    }
    
    pub async fn add_instance_after_health_check(&self, instance: Instance) {
        if self.instances.contains_key(&instance.addr) {
            log::info!("Instance {} already exists, skipping duplicate", instance.endpoint());
            return;
        }
        
        let weight_sender = instance.weight_sender_endpoint.unwrap();
        let addr = instance.addr;
        
        let mut instance_with_weight_sender = instance;
        instance_with_weight_sender.set_weight_sender(weight_sender);
        
        log::info!("Instance {} is now ready and added to instances list (id: {}) with weight sender {}", 
                   instance_with_weight_sender.endpoint(), instance_with_weight_sender.id, weight_sender);
        
        let instance_state = InstanceState {
            instance: instance_with_weight_sender,
            pending_batches: AtomicUsize::new(0),
            running_samples: AtomicUsize::new(0),
            queue_samples: AtomicUsize::new(0),
            last_gen_throughput: AtomicU64::new(0),
            updating_weight: AtomicBool::new(false),
            current_weight_version: AtomicU64::new(0),
        };
        self.instances.insert(addr, instance_state);
        
        self.pending_instances.remove(&addr);
    }
    
    pub fn remove_from_pending(&self, endpoint: &SocketAddr) {
        self.pending_instances.remove(endpoint);
    }
    
    pub fn is_pending(&self, endpoint: &SocketAddr) -> bool {
        self.pending_instances.contains(endpoint)
    }
    
    pub fn add_to_pending(&self, endpoint: &SocketAddr) {
        self.pending_instances.insert(*endpoint);
    }

    pub async fn shutdown_instances(&self, endpoints: &[SocketAddr], check_weight_update: bool) -> Vec<SocketAddr> {
        let mut instances_to_shutdown = Vec::new();
        let mut shutdown_endpoints = Vec::new();
        
        // Batch collect instances to shutdown and remove from instances map
        for endpoint in endpoints {
            match self.instances.try_entry(*endpoint) {
                Some(dashmap::mapref::entry::Entry::Occupied(entry)) => {
                                if check_weight_update {
                                    let is_updating = entry.get().updating_weight.load(Ordering::Acquire);
                                    if is_updating {
                                        log::warn!("Instance {} is updating weights, skipping shutdown", endpoint);
                                        continue;
                                    }
                                }
                                let instance_state = entry.remove();
                                instances_to_shutdown.push(instance_state.instance);
                                shutdown_endpoints.push(*endpoint);
                                log::info!("Instance {} removed from instances map", endpoint);
                            }
                Some(dashmap::mapref::entry::Entry::Vacant(_)) => {
                                // Instance not found, skip
                            }
                None => tokio::time::sleep(std::time::Duration::from_secs(1)).await,
            }
        }
        
        // Batch remove from active_instances with single lock acquisition
        if !instances_to_shutdown.is_empty() {
            let endpoints_set: std::collections::HashSet<_> = endpoints.iter().collect();
            let mut active_instances = self.active_instances.write().await;
            active_instances.retain(|inst| !endpoints_set.contains(&inst.addr));
            drop(active_instances); // Release lock early
            
            log::info!("Removed {} instances from active pool", instances_to_shutdown.len());
        }
        
        // Send shutdown commands asynchronously for all instances
        for instance in instances_to_shutdown {
            tokio::spawn(async move {
                let url = format!("{}/shutdown?graceful=false", instance.endpoint());
                let _ = reqwest::Client::new().post(&url).send().await;
            });
        }
        
        shutdown_endpoints
    }
    
    pub fn increment_pending_request(&self, endpoint: &SocketAddr) {
        if let Some(instance_state) = self.instances.get(endpoint) {
            instance_state.pending_batches.fetch_add(1, Ordering::Relaxed);
        } else if let Some(local_instance_state) = self.local_instances.get(endpoint) {
            local_instance_state.pending_batches.fetch_add(1, Ordering::Relaxed);
        } else {
            panic!("Instance {} not found", endpoint);
        }
    }
    
    pub async fn decrement_pending_request(&self, endpoint: &SocketAddr) {
        // Decrement pending batch count
        if let Some(instance_state) = self.instances.get(endpoint) {
            let prev = instance_state.pending_batches.fetch_sub(1, Ordering::Relaxed);
            log::debug!("Instance {} pending batches decremented to {}", endpoint, prev - 1);
        } else if let Some(local_instance_state) = self.local_instances.get(endpoint) {
            let prev = local_instance_state.pending_batches.fetch_sub(1, Ordering::Relaxed);
            log::debug!("Instance {} pending batches decremented to {}", endpoint, prev - 1);
        } 
    }
    
    
    pub async fn register_local_instances(&self, local_instances: Vec<Instance>) {
        for local_instance in local_instances.iter() {
            let local_instance_state = LocalInstanceState {
                instance: *local_instance,
                pending_batches: AtomicUsize::new(0),
                running_samples: AtomicUsize::new(0),
                queue_samples: AtomicUsize::new(0),
                last_gen_throughput: AtomicU64::new(0),
            };
            self.local_instances.insert(local_instance_state.instance.addr, local_instance_state);
        }
        
        log::info!("Registered {} new local instances, total: {}", local_instances.len(), self.local_instances.len());
    }

}