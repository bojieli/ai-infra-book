// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

use serde_json;
use std::net::IpAddr;
use ipnetwork::IpNetwork;

pub fn merge_arrays(first: &serde_json::Value, second: &mut serde_json::Value, key_path: &[&str]) {
    let mut first_val = first;
    let mut second_val = second;
    for (i, key) in key_path.iter().enumerate() {
        if i == key_path.len() - 1 {
            if let (Some(first_arr), Some(second_arr)) = (
                first_val.get(key).and_then(|v| v.as_array()),
                second_val.get_mut(key).and_then(|v| v.as_array_mut()),
            ) {
                let mut combined = first_arr.clone();
                combined.extend(second_arr.clone());
                second_val[key] = serde_json::json!(combined);
            }
        } else {
            first_val = match first_val.get(key) {
                Some(v) => v,
                None => return,
            };
            second_val = match second_val.get_mut(key) {
                Some(v) => v,
                None => return,
            };
        }
    }
}

pub fn merge_responses(first: &serde_json::Value, second: &mut serde_json::Value) {
    merge_arrays(first, second, &["meta_info", "output_token_logprobs"]);
    
    let first_completion_tokens = first.get("meta_info")
        .and_then(|m| m.get("completion_tokens"))
        .and_then(|t| t.as_u64())
        .unwrap_or(0);
    
    let second_completion_tokens = second.get("meta_info")
        .and_then(|m| m.get("completion_tokens"))
        .and_then(|t| t.as_u64())
        .unwrap_or(0);
    
    let total_tokens = first_completion_tokens + second_completion_tokens;
    
    if let Some(meta_info) = second.get_mut("meta_info") {
        if let Some(meta_obj) = meta_info.as_object_mut() {
            meta_obj.insert("completion_tokens".to_string(), serde_json::json!(total_tokens));
        }
    }
}

pub fn build_final_response(
    last_response: serde_json::Value,
    accumulated_response: Option<serde_json::Value>,
) -> serde_json::Value {
    let mut current = last_response;
    if let Some(previous) = accumulated_response {
        if current.is_array() && previous.is_array() {
            if let (Some(current_arr), Some(prev_arr)) = (current.as_array_mut(), previous.as_array()) {
                for (i, current_item) in current_arr.iter_mut().enumerate() {
                    if let Some(prev_item) = prev_arr.get(i) {
                        merge_responses(prev_item, current_item);
                    }
                }
            }
        } else if !current.is_array() && !previous.is_array() {
            merge_responses(&previous, &mut current);
        }
    }
    current
}

pub fn count_output_tokens(response: &serde_json::Value, sum: bool) -> usize {
    if let Some(array) = response.as_array() {
        if sum {
            array.iter().map(count_single_response_tokens).sum()
        } else {
            array.iter().map(count_single_response_tokens).min().unwrap_or(0)
        }
    } else {
        count_single_response_tokens(response)
    }
}

// pub fn count_output_max_tokens(response: &serde_json::Value) -> usize {
//     if let Some(array) = response.as_array() {
//         array.iter().map(count_single_response_tokens).max().unwrap_or(0)
//     } else {
//         count_single_response_tokens(response)
//     }
// }

fn count_single_response_tokens(response: &serde_json::Value) -> usize {
    response
        .get("meta_info")
        .and_then(|m| m.get("output_token_logprobs"))
        .and_then(|v| v.as_array())
        .map(|arr| arr.len())
        .unwrap_or(0)
    // response.get("meta_info")
    //     .and_then(|m| m.get("completion_tokens"))
    //     .and_then(|t| t.as_u64())
    //     .unwrap_or(0) as usize
}

pub fn build_partial_current_response(
    is_batch_input: bool,
    current_received_responses: &Vec<Option<serde_json::Value>>,
) -> serde_json::Value {
    if is_batch_input {
        serde_json::json!(
            current_received_responses
                .iter()
                .map(|r| r.clone().unwrap_or(serde_json::json!({})))
                .collect::<Vec<_>>()
        )
    } else {
        current_received_responses
            .get(0)
            .and_then(|r| r.clone())
            .unwrap_or(serde_json::json!({}))
    }
}

pub fn extend_input_ids_with_response_tokens(
    input_ids_val: &mut serde_json::Value,
    prev_response: &serde_json::Value,
) {
    if let Some(input_ids_top) = input_ids_val.as_array_mut() {
        let is_batch_input_ids = input_ids_top.first().map(|v| v.is_array()).unwrap_or(false);
        if is_batch_input_ids {
            if let Some(prev_arr) = prev_response.as_array() {
                for (i, input_ids_elem) in input_ids_top.iter_mut().enumerate() {
                    if let (Some(arr), Some(prev_item)) = (input_ids_elem.as_array_mut(), prev_arr.get(i)) {
                        if let Some(logprobs) = prev_item
                            .get("meta_info")
                            .and_then(|m| m.get("output_token_logprobs"))
                            .and_then(|l| l.as_array())
                        {
                            let token_ids: Vec<serde_json::Value> = logprobs
                                .iter()
                                .filter_map(|token| token.as_array().and_then(|a| a.get(1)).cloned())
                                .collect();
                            arr.extend(token_ids);
                        }
                    }
                }
            } else {
                panic!("prev_response is not an array");
            }
        } else {
            if let Some(logprobs) = prev_response
                .get("meta_info")
                .and_then(|m| m.get("output_token_logprobs"))
                .and_then(|l| l.as_array())
            {
                let token_ids: Vec<serde_json::Value> = logprobs
                    .iter()
                    .filter_map(|token| token.as_array().and_then(|a| a.get(1)).cloned())
                    .collect();
                input_ids_top.extend(token_ids);
            } else {
                panic!("prev_response is not a single response");
            }
        }
    }
}

// pub fn build_continuation_inputs_from_responses(
//     original_input_ids: &Vec<serde_json::Value>,
//     responses: &serde_json::Value,
// ) -> (Vec<Vec<serde_json::Value>>, Vec<usize>) {
//     let local_responses = if responses.is_array() {
//         responses.as_array().unwrap().clone()
//     } else {
//         vec![responses.clone()]
//     };

//     let mut continuation_input_ids = Vec::new();
//     let mut unfinished_indices = Vec::new();

//     for (i, sub_response) in local_responses.iter().enumerate() {
//         let finish_reason = sub_response
//             .get("meta_info")
//             .and_then(|m| m.get("finish_reason"))
//             .and_then(|f| f.get("type"))
//             .and_then(|t| t.as_str());

//         if finish_reason == Some("length") || finish_reason == Some("abort") {
//             let output_token_ids: Vec<serde_json::Value> = sub_response
//                 .get("meta_info")
//                 .and_then(|m| m.get("output_token_logprobs"))
//                 .and_then(|v| v.as_array())
//                 .map(|logprobs| {
//                     logprobs
//                         .iter()
//                         .filter_map(|item| item.as_array().and_then(|arr| arr.get(1)).cloned())
//                         .collect()
//                 })
//                 .unwrap_or_else(Vec::new);

//             let mut extended_input = original_input_ids[i].as_array().unwrap().clone();
//             extended_input.extend(output_token_ids);
//             continuation_input_ids.push(extended_input);
//             unfinished_indices.push(i);
//         }
//     }

//     (continuation_input_ids, unfinished_indices)
// }

pub fn trim_response_to_used_tokens(
    prev_response: &mut serde_json::Value,
    used_tokens: usize,
) {
    // trim output_token_logprobs to the used tokens
    if let Some(arr) = prev_response.as_array_mut() {
        // Batched case: Trim each item's logprobs to the length of the shortest one.
        for item in arr {
            if let Some(logprobs) = item
                .get_mut("meta_info")
                .and_then(|m| m.get_mut("output_token_logprobs"))
                .and_then(|v| v.as_array_mut())
            {
                logprobs.truncate(used_tokens);
            }
        }
    } else {
        // Single response case: Trim the logprobs.
        if let Some(logprobs) = prev_response
            .get_mut("meta_info")
            .and_then(|m| m.get_mut("output_token_logprobs"))
            .and_then(|v| v.as_array_mut())
        {
            logprobs.truncate(used_tokens);
        }
    }
    return;
}

pub fn adjust_sampling_params_for_used_tokens(
    sampling_params: &mut serde_json::Value,
    prev_response: &mut serde_json::Value,
) {
    if let Some(max_new_tokens) = sampling_params.get("max_new_tokens").and_then(|v| v.as_u64()) {
        let used_tokens = if prev_response.is_array() {
            prev_response
                .as_array()
                .map(|arr| {
                    arr
                        .iter()
                        .map(|item| {
                            item.get("meta_info")
                                .and_then(|m| m.get("output_token_logprobs"))
                                .and_then(|l| l.as_array())
                                .map(|a| a.len())
                                .unwrap_or(0)
                        })
                        .min() // keep the shortest generation of the batch
                        .unwrap_or(0)
                })
                .unwrap_or(0)
        } else {
            prev_response
                .get("meta_info")
                .and_then(|m| m.get("output_token_logprobs"))
                .and_then(|l| l.as_array())
                .map(|a| a.len())
                .unwrap_or(0)
        };
        trim_response_to_used_tokens(prev_response, used_tokens);
        // because requests in the same batch share the sampling_params, we can only keep the largest remaining tokens
        let remaining_tokens = max_new_tokens.saturating_sub(used_tokens as u64);
        sampling_params["max_new_tokens"] = serde_json::json!(remaining_tokens);
    }
}

// pub fn adjust_sampling_params_subtract_limit(
//     sampling_params: &mut serde_json::Value,
//     limit: u64,
// ) {
//     if let Some(max_new_tokens) = sampling_params.get("max_new_tokens").and_then(|v| v.as_u64()) {
//         let remaining_tokens = max_new_tokens.saturating_sub(limit);
//         sampling_params["max_new_tokens"] = serde_json::json!(remaining_tokens);
//     }
// }

/// Filter IP addresses based on allowed IP configuration
/// Replicates the Python implementation in utils.py
pub fn filter_ips_by_config(all_ips: &[String], allowed_ips_config: &str) -> Vec<String> {
    if allowed_ips_config == "0.0.0.0/0" {
        return all_ips.to_vec();
    }
    
    let allowed_patterns: Vec<&str> = allowed_ips_config
        .split(',')
        .map(|s| s.trim())
        .collect();
    
    let mut filtered_ips = Vec::new();
    
    for ip in all_ips {
        if let Ok(ip_addr) = ip.parse::<IpAddr>() {
            for pattern in &allowed_patterns {
                if pattern.contains('/') {
                    // Handle CIDR notation
                    if let Ok(network) = pattern.parse::<IpNetwork>() {
                        if network.contains(ip_addr) {
                            filtered_ips.push(ip.clone());
                            break;
                        }
                    }
                } else if ip == *pattern {
                    // Handle exact IP match
                    filtered_ips.push(ip.clone());
                    break;
                }
            }
        }
        // Skip invalid IPs (equivalent to Python's except: continue)
    }
    
    filtered_ips
}
