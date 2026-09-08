use serde::{Deserialize, Serialize, Serializer};
use uuid::Uuid;
use std::net::SocketAddr;


fn serialize_socket_addr_as_endpoint<S>(addr: &SocketAddr, serializer: S) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    let endpoint = format!("http://{}", addr);
    serializer.serialize_str(&endpoint)
}

fn serialize_optional_socket_addr_as_string<S>(addr: &Option<SocketAddr>, serializer: S) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    match addr {
        Some(addr) => serializer.serialize_some(&addr.to_string()),
        None => serializer.serialize_none(),
    }
}

#[derive(Debug, Deserialize)]
pub struct RegisterRequest {
    pub host: String,
    pub port: u16,
    pub mooncake_handshake_port: Option<u16>,
}

#[derive(Debug, Serialize, Clone)]
pub struct RegisterResponse {
    pub mooncake_transfer_device_name: String,
    pub mooncake_transfer_protocol: String,
    pub weight_sender_rpyc_endpoint: SocketAddr,
    pub sender_group_idx: usize,
    pub num_mooncake_engines_per_group: usize,
}

#[derive(Debug, Deserialize)]
pub struct GenerateRequest(pub serde_json::Value);

#[derive(Debug, Deserialize)]
pub struct BatchGenerationRequest(pub Vec<(u64, GenerateRequest)>);

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct UpdateWeightsFromAgentRequest {
    pub tensors_meta: Vec<(String, (Vec<i64>, String))>,
    pub load_format: Option<String>,
    pub flush_cache: Option<bool>,
    pub bootstrap: bool,
}

#[derive(Debug, Deserialize)]
pub struct UpdateWeightSendersRequest {
    // list of list: each inner list contains ips of a single node
    pub weight_sender_ips: Vec<Vec<String>>,
    pub num_mooncake_groups_per_sender: Option<usize>,
    pub num_mooncake_engines_per_group: Option<usize>,
}

#[derive(Debug, Deserialize)]
pub struct ShutdownInstancesRequest {
    pub endpoints: Vec<SocketAddr>,
    #[serde(default)]
    pub check_weight_update: bool,
}

#[derive(Debug, Deserialize)]
pub struct GetReceiveInstancesRequest {
    pub weight_sender_endpoint: SocketAddr,
    pub sender_weight_version: u64,
}

#[derive(Debug, Clone, Copy, Serialize)]
pub struct Instance {
    pub id: Uuid,
    #[serde(rename = "endpoint", serialize_with = "serialize_socket_addr_as_endpoint")]
    pub addr: SocketAddr, // host:port
    #[serde(rename = "mooncake_handshake_addr", serialize_with = "serialize_optional_socket_addr_as_string")]
    pub mooncake_handshake_addr: Option<SocketAddr>, // host:port for mooncake handshake, None for local instance
    #[serde(serialize_with = "serialize_optional_socket_addr_as_string")]
    pub weight_sender_endpoint: Option<SocketAddr>, // weight sender endpoint assigned to this instance, None for local instance
}

impl Instance {
    pub fn new(id: Uuid, addr: SocketAddr, mooncake_handshake_addr: Option<SocketAddr>) -> Self {
        Self {
            id,
            addr,
            mooncake_handshake_addr,
            weight_sender_endpoint: None,
        }
    }
    
    pub fn endpoint(&self) -> String {
        format!("http://{}", self.addr)
    }
    
    pub fn set_weight_sender(&mut self, weight_sender_endpoint: SocketAddr) {
        self.weight_sender_endpoint = Some(weight_sender_endpoint);
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub mooncake_transfer_device_name: String,
    pub mooncake_transfer_protocol: String,
    pub allowed_sender_ips: String,
    pub weight_sender_rpyc_endpoints: Vec<SocketAddr>,
    pub weight_sender_rpyc_base_port: usize,
    pub num_mooncake_groups_per_sender: usize,
    pub num_mooncake_engines_per_group: usize,
    pub max_assigned_batches_per_stats_check: usize,
    pub train_batch_size: Option<usize>,
}

#[derive(Debug, Serialize)]
pub struct GetReceiveInstancesResponse {
    pub instances: Vec<InstanceWithVersion>,
}

#[derive(Debug, Serialize)]
pub struct InstanceWithVersion {
    pub instance: Instance,
    pub current_weight_version: u64,
}

// #[derive(Debug, Clone, Copy, Serialize)]
// pub struct LocalInstance {
//     pub id: Uuid,
//     #[serde(rename = "endpoint", serialize_with = "serialize_socket_addr_as_endpoint")]
//     pub addr: SocketAddr,
// }

// impl LocalInstance {
//     pub fn new(id: Uuid, addr: SocketAddr) -> Self {
//         Self { id, addr }
//     }
    
//     pub fn endpoint(&self) -> String {
//         format!("http://{}", self.addr)
//     }
// }

#[derive(Debug, Deserialize)]
pub struct RegisterLocalInstancesRequest(pub Vec<(String, u16)>);

#[derive(Debug, Deserialize)]
pub struct UpdateMetricsRequest {
    pub step_time_s: u64,
    pub trainer_bubble_time_s: u64,
    pub step_throughput: f64,
}

#[derive(Debug, Deserialize)]
pub struct UpdateWeightsRequest {
    pub instance_endpoints: Vec<SocketAddr>,
    pub weight_version: u64,
    pub tensors_meta: Vec<(String, (Vec<i64>, String))>,
    pub load_format: Option<String>,
    pub flush_cache: Option<bool>,
    pub bootstrap: bool,
}