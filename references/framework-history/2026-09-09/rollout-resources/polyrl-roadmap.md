
## Roadmap (subject to change)

### Release v1: Elastic and auto-balanced resource management

Goal:
1. [**Cost Efficiency**] It harvests resources with dynamic availability (e.g. spot instances in cloud) for rollout to reduce the cost of reinforcement learning. 
2. [**Adaptivity**] It employs a progressive workload balance algorithm to adaptively offload rollout tasks to available remote rollout engines. The algorithm estimate the workload gap between training and rollout based on recent steps, thus it adapts to length changes and dynamic resource availability. 
3. [**Fault Tolerance**] It handles failures of rollout instances with negligible overhead via token-level tracking and continuous generation. 
4. [**Utilization**] It also applies server-based local rollout engine so that the rollout manager can balance workload holistically between reserved and preemptible resources, which maximizes resource utilization. 

- Intra-stage (rollout) balance
  - Rollout workload balance, start from homogenous rollout instances.
    - [x] Token-level tracking and workload balance.
- Inter-stage (rollout vs. training) balance
  - Rollout offload
    - [x] Estimate workload gap between training and rollout in seconds.
    - [x] Adaptively offload rollout workloads to remote rollout engines.
    - [x] Fine-grained workload partition (request -> time).
  - Dynamic rollout instances allocation
    - [x] Add rollout instances at runtime when rollout time extend.
- Pack sequences in rollout manager
  - [x] Send rollout prompts to manager in a batch.
  - [x] Rollout manager decompose into per-sample requests and send to rollout instances. 
  - [x] Manage the order of rollout results and pack into micro-batches.
  - [x] Dynamic batch size with a lower bound (block if under; return all when asked).
- Fault tolerance 
  - Handle multiple failure cases
    - [x] Spot instance preemption
    - [ ] Failure during weight transfer
    - [x] Failure during rollout
- Weight compression
  - [ ] Quantization+lossless compression to reduce the size of weight before transfer.
- Off-policy support
  - [ ] Unlock weight update of rollout engines.


### Release-v0: Basic disaggregated RL system

Goal: 
1. Rollout instances running on dynamic independent hardware. 
2. Rollout instances stream results to training engine via async-efficient manager process. 
3. Weight update via TCP&RDMA aggregated channel.

- Rollout
  - Decouple rollout and update
    - [x] Training engine send requests to SGLang server via API.
    - [x] Rank-zero send all generation requests and skip local generation.
    - [x] Wrap rollout results streaming into an iterator.
  - Multiple rollout instances management
    - Rollout manager in Rust
      - [x] Rollout instance register request via API.
      - [x] Relay requests from training engine to rollout instances.
      - [x] Interface of algorithm-driven request scheduling.
  - Rollout instances dynamic in-n-out
    - [x] Active new rollout instance register during runtime.
    - [x] Shutdown connection when rollout instance goes down. 
- Training
  - From batch process to stream process 
    - [x] Align micro-batch size along rollout-actor-critic.
    - [x] Reward, KL, advantage in micro-batch.
    - [x] Critic and actor for/backward in micro-batch and update in mini-batch.
    - [x] Align runtime metric collection with micro-batch processing.
- Weight transfer
  - TCP&RDMA aggregated interface
    - [x] Integrate Mooncake transfer engine.
    - [x] Weight transfer agent for each instance.
  - Model weight gather and re-shard
    - [x] Rank-zero gathers weights from FSDP ranks and call agent to transfer.
    - [x] Support weight resharding on TP>1 rollout instances.
  - Compression interface
    - [x] Encode and decode weight interface to support compressed weight update.
    - [x] Asynchronous full weight update interface.
