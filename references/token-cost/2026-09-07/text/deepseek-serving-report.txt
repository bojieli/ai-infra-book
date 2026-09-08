# Day 6: One More Thing, DeepSeek-V3/R1 Inference System Overview
## System Design Principles
The optimization objectives of serving DeepSeek-V3/R1 inference are: **higher throughput and lower latency.**

To optimize these two objectives, our solution employs cross-node Expert Parallelism (EP).
- First, EP significantly scales the batch size, enhancing GPU matrix computation efficiency and boosting throughput.
- Second, EP distributes experts across GPUs, with each GPU processing only a small subset of experts (reducing memory access demands), thereby lowering latency.

However, EP increases system complexity, primarily in two aspects:
  1. EP introduces cross-node communication. To optimize throughput, appropriate computational workflows must be designed to overlap communication with computation.
  2. EP involves multiple nodes, thereby inherently requiring Data Parallelism (DP) and necessitating load balancing between different DP instances.

This article focuses on how we address these challenges by:
- leveraging EP to scale batch size,
- hiding communication latency behind computation, and
- performing load balancing. 

### Large-scale Cross-node Expert Parallelism (EP)
Due to the large number of experts in DeepSeek-V3/R1—where only 8 out of 256 experts per layer are activated—the model’s high sparsity necessitates an extremely large overall batch size. This ensures sufficient batch size per expert, enabling higher throughput and lower latency. Large-scale cross-node EP is essential.

As we have adopted prefill-decode disaggregation architecture, we employ different degrees of parallelisms during the prefill and decode phases:
- **Prefilling Phase [Routed Expert EP32, MLA/Shared Expert DP32]**:  Each deployment unit spans 4 nodes with 32 redundant routed experts, where each GPU handles 9 routed experts and 1 shared expert.
- **Decoding Phase [Routed Expert EP144, MLA/Shared Expert DP144]**:  Each deployment unit spans 18 nodes with 32 redundant routed experts, where each GPU manages 2 routed experts and 1 shared expert.

### Computation-Communication Overlapping
Large-scale cross-node EP introduces significant communication overhead. To mitigate this, we employ a dual-batch overlap strategy to hide communication costs and improve overall throughput by splitting a batch of requests into two microbatches. 
During the prefilling phase, these two microbatches executed alternately and the communication cost of one microbatch is hide behind the computation of the other.

![Communication-Computation Overlapping during Prefilling Phase.png](figures/Communication-Computation%20Overlapping%20during%20Prefilling%20Phase.png)
*Communication-Computation Overlapping during Prefilling Phase*

During the decoding phase, the execution durations of different stages are unbalanced. Hence, we subdivide the attention layer into two steps and use a 5-stage pipeline to achieve a seamless communication-computation overlapping.
![Communication-Computation Overlapping during Decoding Phase.png](figures/Communication-Computation%20Overlapping%20during%20Decoding%20Phase.png)
*Communication-Computation Overlapping during Decoding Phase*

More details about our communication-computation overlapping mechanism can be found at https://github.com/deepseek-ai/profile-data.

### Achieving Optimal Load Balancing
The large-scale parallelism (including DP and EP) introduces a critical challenge: if a single GPU is overloaded with computation or communication, it becomes a performance bottleneck, slowing the entire system while leaving other GPUs idle. To maximize resource utilization, we strive to balance computational and communication loads across all GPUs.

#### 1. Prefill Load Balancer
  - Key Issue: Varying request counts and sequence lengths across DP instances lead to imbalanced core-attention computation and dispatch send load.
  - Optimization Objectives:
    - Balance core-attention computation across GPUs (core-attention computational load balancing).
    - Equalize input token counts per GPU (dispatch send load balancing), preventing prolonged processing on specific GPUs.
#### 2. Decode Load Balancer
  - Key Issue: Uneven request counts and sequence lengths across DP instances cause disparities in core-attention computation (linked to KVCache usage) and dispatch send load.
  - Optimization Objectives:
    - Balance KVCache usage across GPUs (core-attention computational load balancing).
    - Equalize request counts per GPU (dispatch send load balancing).
#### 3. Expert-Parallel Load Balancer
  - Key Issue: For a given MoE model, there exist inherently high-load experts, resulting in an imbalance in expert computational workloads across different GPUs.
  - Optimization Objective: 
    - Balance expert computation on each GPU (i.e., minimize the maximum dispatch receive load across all GPUs).

### Diagram of DeepSeek's Online Inference System
![Diagram of DeepSeek's Online Inference System.jpg](figures/Diagram%20of%20DeepSeek%27s%20Online%20Inference%20System.jpg)
*Diagram of DeepSeek's Online Inference System*

### Statistics of DeepSeek's Online Service
All DeepSeek-V3/R1 inference services are served on H800 GPUs with precision consistent with training. 
Specifically, matrix multiplications and dispatch transmissions adopt the FP8 format aligned with training, 
while core MLA computations and combine transmissions use the BF16 format, ensuring optimal service performance.

Additionally, due to high service load during the day and low load at night, we implemented a mechanism to deploy inference services across all nodes during peak daytime hours. 
During low-load nighttime periods, we reduce inference nodes and allocate resources to research and training. 
Over the past 24 hours (UTC+8 02/27/2025 12:00 PM to 02/28/2025 12:00 PM), the combined peak node occupancy for V3 and R1 inference services reached 278, with an average occupancy of 226.75 nodes (each node contains 8 H800 GPUs). 
Assuming the leasing cost of one H800 GPU is $2 per hour, the total daily cost amounts to $87,072.

![H800 Node Count For Inference Service.jpg](figures/H800%20Node%20Count%20For%20Inference%20Service.jpg)
*H800 Node Count For Inference Service.png*

Within the 24-hour statistical period (UTC+8 02/27/2025 12:00 PM to 02/28/2025 12:00 PM), V3 and R1:
- Total input tokens: 608B, of which 342B tokens (56.3%) hit the on-disk KV cache.
- Total output tokens: 168B. The average output speed was 20–22 tokens per second, and the average kvcache length per output token was 4,989 tokens.
- Each H800 node delivers an average throughput of ~73.7k tokens/s input (including cache hits) during prefilling or ~14.8k tokens/s output during decoding.
  
The above statistics include all user requests from web, APP, and API. If all tokens were billed at DeepSeek-R1’s pricing (*), the total daily revenue would be $562,027, with a cost profit margin of 545%.        

_(*) R1 Pricing: \$0.14/M input tokens (cache hit), \$0.55/M input tokens (cache miss), $2.19/M output tokens._

However, our actual revenue is substantially lower for the following reasons:
- DeepSeek-V3’s pricing is significantly lower than R1,
- Only a subset of services are monetized (web and APP access remain free),
- Nighttime discounts are automatically applied during off-peak hours.

![Cost And Theoretical Income.jpg](figures/Cost%20And%20Theoretical%20Income.jpg)
*Cost And Theoretical Income*
