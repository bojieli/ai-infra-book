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

// Implemetation of workload balancing between rollout workers and training engine

// use std::intrinsics::saturating_sub;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;
use std::sync::Mutex;
use std::collections::HashMap;

const ALPHA: f64 = 0.8;
const BETA: f64 = 0.2; // last step peak

#[derive(Debug)]
pub struct LoadBalanceState {
    pub max_local_instance_gen_s: AtomicU64,
    pub last_local_gen_time_s: AtomicU64,
    last_trainer_bubble_time_s: AtomicU64,
    pub last_total_gen_time_s: AtomicU64,
    peak_throughput_local_gen_s: AtomicU64,
    last_response_length_mean: AtomicU64, // Store as f64 bits

    // New fields for optimal generation step tracking
    /// Stores the optimal local generation steps found for a given number of rollout instances.
    /// Key: number of rollout instances, Value: optimal local gen_s
    optimal_local_gen_s: Mutex<HashMap<u64, u64>>,
    /// Stores the throughput from the last cycle to detect increases or decreases.
    last_throughput: Mutex<f64>,
    /// Stores the number of rollout instances from the last cycle.
    last_num_rollout_instances: AtomicU64,
}

impl LoadBalanceState {
    pub fn new(initial_gen_s: u64) -> Self {
        Self {
            max_local_instance_gen_s: AtomicU64::new(initial_gen_s),
            last_local_gen_time_s: AtomicU64::new(0),
            last_trainer_bubble_time_s: AtomicU64::new(0),
            last_total_gen_time_s: AtomicU64::new(0),
            peak_throughput_local_gen_s: AtomicU64::new(0),
            last_response_length_mean: AtomicU64::new(0),
            // optimal_local_gen_s: Mutex::new(HashMap::new()),
            // Initialize new fields
            // 8b
            optimal_local_gen_s: Mutex::new(HashMap::from([
                (1, 190),
                (2, 160),
                (3, 105),
                (4, 70),
            ])),
            // 14b
            // optimal_local_gen_s: Mutex::new(HashMap::from([
            //     (1, 346),
            //     (2, 212),
            //     (3, 145),
            //     (4, 60),
            //     (5, 8),
            //     (6, 5),
            // ])),
            last_throughput: Mutex::new(0.0),
            last_num_rollout_instances: AtomicU64::new(0),
        }
    }

    pub fn get_max_local_instance_gen_s(&self) -> u64 {
        self.max_local_instance_gen_s.load(Ordering::Relaxed)
    }

    pub fn update_generation_stats(&self, total_gen_time_s: u64, response_length_mean: f64, local_gen_time_s: u64) {
        self.last_total_gen_time_s.store(total_gen_time_s, Ordering::Relaxed);
        self.last_local_gen_time_s.store(local_gen_time_s, Ordering::Relaxed);
        self.last_response_length_mean.store(response_length_mean.to_bits(), Ordering::Relaxed);
    }

    pub fn get_last_response_length_mean(&self) -> f64 {
        f64::from_bits(self.last_response_length_mean.load(Ordering::Relaxed))
    }

    /// Adjusts the number of local generation steps based on system load and throughput.
    /// This function is called every cycle.
    pub fn adjust_local_instances_gen_s(
        &self,
        total_gen_time_s: u64,
        step_time_s: u64,
        trainer_bubble_time_s: u64,
        num_rollout_instances: u64, // the number of instance at current moment
        throughput: f64,
    ) -> u64 {
        let mut last_throughput_guard = self.last_throughput.lock().unwrap();
        let last_num_instances = self.last_num_rollout_instances.load(Ordering::Relaxed);
        let current_local_max_gen_s = self.max_local_instance_gen_s.load(Ordering::Relaxed);

        if num_rollout_instances != last_num_instances {
            *last_throughput_guard = 0.0; // Reset to zero so that next step is always increase
            // --- Logic for changed number of rollout instances ---
            let mut optimal_map = self.optimal_local_gen_s.lock().unwrap();

            // update the latest gen_s of the last_num_instances if the optimal map is empty
            let new_optimum = self.peak_throughput_local_gen_s.load(Ordering::Relaxed);

            // insert the latest gen_s if the optimal map is empty
            // optimal_map.entry(last_num_instances).or_insert(new_optimum);
            // Use the entry API to either insert a new value or update an existing one with EMA.
            optimal_map.entry(last_num_instances)
                .and_modify(|prev_optimum| {
                    // **Apply exponential moving average if the entry exists**
                    let updated_value = (1.0 - BETA) * (*prev_optimum as f64) + BETA * (new_optimum as f64);
                    *prev_optimum = updated_value.round() as u64;
                    log::info!(
                        "Instance count changed to {}. Updating optimal gen_s for {} instances to {} (EMA).",
                        num_rollout_instances, last_num_instances, *prev_optimum
                    );
                })
                .or_insert_with(|| {
                    // **Insert the value directly if it's the first time**
                    log::info!(
                        "Instance count changed to {}. Storing initial optimal gen_s: {} for {} instances.",
                        num_rollout_instances, new_optimum, last_num_instances
                    );
                    new_optimum
                });

            if let Some(&optimal_gen_s) = optimal_map.get(&num_rollout_instances) {
                // We have a known optimal value for this number of instances. Use it directly.
                log::info!(
                    "Instance count changed to {}. Using stored optimal gen_s: {}.",
                    num_rollout_instances, optimal_gen_s
                );

                // Update state for the next cycle with the new configuration
                self.last_num_rollout_instances.store(num_rollout_instances, Ordering::Relaxed);
                self.max_local_instance_gen_s.store(optimal_gen_s, Ordering::Relaxed);
                self.peak_throughput_local_gen_s.store(optimal_gen_s, Ordering::Relaxed);
                self.last_trainer_bubble_time_s.store(trainer_bubble_time_s, Ordering::Relaxed);

                return optimal_gen_s;
            } else {
                // If no entry exists, we fall through to the adjustment logic below to find a new optimum.
                log::info!(
                    "Instance count changed to {}. No stored optimal gen_s, fallback to elastic adjustment.",
                    num_rollout_instances
                );
            }
        } else { 
            // --- Logic for stable or new number of rollout instances ---
            if throughput <= *last_throughput_guard {
                // if throughput stopped growing, store the last local_gen_s
                let mut optimal_map = self.optimal_local_gen_s.lock().unwrap();
                let new_optimum = self.peak_throughput_local_gen_s.load(Ordering::Relaxed);

                // Use the entry API to either insert a new value or update an existing one with EMA.
                optimal_map.entry(last_num_instances)
                    .and_modify(|prev_optimum| {
                        // **Apply exponential moving average if the entry exists**
                        let updated_value = (1.0 - ALPHA) * (*prev_optimum as f64) + ALPHA * (new_optimum as f64);
                        *prev_optimum = updated_value.round() as u64;
                        log::info!(
                            "Throughput decreased. Updating optimal gen_s for {} instances to {} (EMA).",
                            last_num_instances, *prev_optimum
                        );
                    })
                    .or_insert_with(|| {
                        // **Insert the value directly if it's the first time**
                        log::info!(
                            "Throughput decreased. Storing initial optimal gen_s: {} for {} instances.",
                            new_optimum, last_num_instances
                        );
                        new_optimum
                    });
            } else {
                // if the throughput is growing, update the peak local_gen
                self.peak_throughput_local_gen_s.store(current_local_max_gen_s, Ordering::Relaxed);
                log::info!(
                    "Throughput grew. Updating peak throughput local gen time to: {} for {} instances.",
                    current_local_max_gen_s, last_num_instances
                );
            }
            *last_throughput_guard = throughput;
        }

        // `remote_bubble_time_s` is the time the rollout process waits for the trainer.
        let remote_bubble_time_s = step_time_s.saturating_sub(total_gen_time_s);

        let new_local_max_gen_s = if trainer_bubble_time_s < remote_bubble_time_s {
            // Trainer is waiting less than rollout; we have spare time in the trainer.
            // Reduce local generation to free up hardware sooner.
            let reduce_gen_s = remote_bubble_time_s.saturating_sub(trainer_bubble_time_s) / 3;
            current_local_max_gen_s.saturating_sub(reduce_gen_s).max(5)
        } else {
            // Rollout is waiting for the trainer; local generation is the bottleneck.
            // Increase local generation to better utilize the trainer's capacity.
            current_local_max_gen_s + (trainer_bubble_time_s.saturating_sub(remote_bubble_time_s)) / 3
        };

        // Update state for the next cycle
        self.last_num_rollout_instances.store(num_rollout_instances, Ordering::Relaxed);
        self.max_local_instance_gen_s.store(new_local_max_gen_s, Ordering::Relaxed);
        self.last_trainer_bubble_time_s.store(trainer_bubble_time_s, Ordering::Relaxed);

        new_local_max_gen_s
    }
}

pub struct TimingCollector {
    start_time: Option<Instant>,
}

impl TimingCollector {
    pub fn new() -> Self {
        Self { start_time: None }
    }

    pub fn start(&mut self) {
        self.start_time = Some(Instant::now());
    }

    pub fn elapsed_s(&self) -> u64 {
        self.start_time
            .map(|start| start.elapsed().as_secs())
            .unwrap_or(0)
    }

    pub fn duration_s(&self, end_s: Instant) -> u64 {
        self.start_time
            .map(|start| end_s.duration_since(start).as_secs())
            .unwrap_or(0)
    }
}