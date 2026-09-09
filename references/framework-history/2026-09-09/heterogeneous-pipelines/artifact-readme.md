# Artifact Evaluation for Helix - Reproducibility

We assume that the environment has already been set up based on the `readme.md` in the
root directory of the repository. Please ask the AE chairs for access to the 24-node
cluster we provide. You can use the host machine in the cluster to run
simulator experiments. You will need the whole cluster of 24 machines to run the
experiments for the prototype system. A copy of the artifact is stored in `~/helix`. 
Before starting artifact evaluation for reproducibility, run the following command to
activate the conda environment:

```bash
conda activate runtime
cd ~/helix
```

> **Important Note:** For the experiments below, we provide a copy of the results we get after running
> them **in the exact same path as they are generated**. 

> **Important Note:** For all the commends below, if not otherwise specified, please
> **run them on the host**.

> **Important Note:** In order to facilitate artifact evaluation, we use ray to launch scripts
> remotely on the worker machines. We have already set up the ray cluster for you. On the host
> machine, you can run the following command to check the status of the ray cluster:
> ```bash
> ray status
> ```
> You will see a log like this (notice that 24 GPUs means that all 24 machines are connected):
> ```
> Usage:
> 0.0/590.0 CPU
> 0.0/24.0 GPU
> 0B/1.60TiB memory
> 0B/705.98GiB object_store_memory
> ```
> If the ray cluster is not running, you can manually start it with the following command:
> ```bash
> ray start --head --port=8888  # on the host machine
> ```
> And run the following command on the worker machines to connect to the ray cluster:
> ```bash
> ray start --address='10.128.0.31:8888'  # on all 24 worker machines
> ```

## Section 6.3 Single Cluster

All files related to this group of experiments are located in `artifact_evaluation/single_cluster`.
Start from the root directory of the repository:
```bash
cd artifact_evaluation/single_cluster
```

### Step 1: Generate Cluster Config Files
Run the following command to generate cluster config files:
```bash
python step1_gen_cluster.py
```
It will automatically generate the config file that represents a cluster with 24 machines 
(4 1xA100 machines, 8 1xL4 machines, 12 1xT4 machines) in `config/cluster24.ini`. It will
also generate the three sub-cluster config files with each type of machine: `config/a100.ini`,
`config/l4.ini` and `config/t4.ini`.

### Step 2: Model Placement

The next step is to generate the model placement for the cluster. Run the following commands
to generate model placements for LLaMA-1 30B and LLaMA-2 70B using different model placement
methods. 

Notice that before running Helix's MILP-based model placement planner, you need to
**backup and empty** the `./layout_llama30b/ilp` and `./layout_llama70b/ilp` directories,
which currently contains the result we get. If the directories are not empty, you will get
an error from the model placement planner saying that the directory is not empty. After you
have finished evaluating Helix's model placement planner, you can restore the two directories
to facilitate the evaluation of later steps.

Also, for `llama70b`, you need to run `petals` before running Helix's MILP model placement
planner, as we bootstrap the solver with `petals`' solution.

> **Notes:** We notice that Gurobi produces completely different optimization traces when
> using **different licenses, even when using the same random seed**. When using the default
> limited license, the optimization performance is much worse than that of using the academic
> license. (objective value = 952 v.s. 1289) Unfortunately, we are not allowed and unable to
> bind our academic Gurobi license to the cluster provided. Note that this is an issue with
> Gurobi **licensing** instead of our system, and we provide our optimization trace in
> `./layout_llama70b/ilp/trace.txt` for you to compare against.

> **Notes:** Running Helix to search for a model placement for LLaMA 70B may take a long time.
> We set the max running time to 10 hours, but you can stop the solver at any time with `ctrl +c`. 
> In our experiments, on a machine with 14 cores and academic license, we manually early-stop
> the solver at round 10 minutes. This solution at this point already has good quality. The
> objective value (Incumbent) equals to 1289.

```bash
# Generate model placement using heuristic method Petals
python step2_gen_layout.py petals llama30b
python step2_gen_layout.py petals llama70b
# Generate model placement using heuristic method Swarm
python step2_gen_layout.py swarm llama30b
python step2_gen_layout.py swarm llama70b
# Generate model placement using heuristic method separate pipelines
python step2_gen_layout.py separate llama30b
python step2_gen_layout.py separate llama70b
# Generate model placement using Helix's MILP-based method
python step2_gen_layout.py ilp llama30b  # empty ./layout_llama30b/ilp before running
python step2_gen_layout.py ilp llama70b  # empty ./layout_llama70b/ilp before running
```

After running the commands above, you will get model placement files located in:
+ **petals & llama 30b**: `./layout_llama30b/petals` (`petals_sol.ini` and `simulator_cluster.ini`)
+ **petals & llama 70b**: `./layout_llama70b/petals` (`petals_sol.ini` and `simulator_cluster.ini`)
+ **swarm & llama 30b**: `./layout_llama30b/swarm` (`swarm_sol.ini` and `simulator_cluster.ini`)
+ **swarm & llama 70b**: `./layout_llama70b/swarm` (`swarm_sol.ini` and `simulator_cluster.ini`)
+ **separate & llama 30b**: `./layout_llama30b/separate` (6 manually created files)
+ **separate & llama 70b**: `./layout_llama70b/separate` (6 manually created files)
+ **ilp & llama 30b**: `./layout_llama30b/ilp/a100`, `./layout_llama30b/ilp/l4`, `./layout_llama30b/ilp/t4`, each containing the model placement for a sub-cluster
+ **ilp & llama 70b**: `./layout_llama70b/ilp` (`ilp_sol.ini` and `simulator_cluster.ini`, and 3 other files that records information about the MILP problem)

### Step 3: Run Simulation
With the model placement files generated, we can run the simulation and reproduce the results in the
paper.

> **Notes:** Before running simulation, you can restore the `./layout_llama30b/ilp` and
> `./layout_llama70b/ilp` directories you just backed up.

(1) Run LLaMA 30B in offline setup using Helix and observe its decode throughput. This
corresponds to Figure 5(a)'s Simulation - Helix in the paper.
```bash
python step3_simulation.py helix llama30b offline
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa30B offline simulation results: Helix
Total decode throughput: 339.6 tokens/s
************************************************************
```

(2) Run LLaMA 30B in offline setup using Swarm and observe its decode throughput. This
corresponds to Figure 5(a)'s Simulation - Swarm in the paper.
```bash
python step3_simulation.py swarm llama30b offline
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa30B offline simulation results: Swarm
Total decode throughput: 151.6 tokens/s
************************************************************
```

(3) Run LLaMA 30B in offline setup using Separate Pipelines and observe its decode 
throughput. This corresponds to Figure 5(a)'s Simulation - Separate Pipelines (SP) in the paper.
```bash
python step3_simulation.py separate llama30b offline
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa30B offline simulation results: Separate
Total decode throughput: 309.0 tokens/s
************************************************************
```

(4) Run LLaMA 30B in online setup using Helix and observe its decode throughput, prompt latency
and decode latency. The decode throughput corresponds to Figure 5(b)'s Simulation - Helix; the
prompt latency corresponds to Figure 5(e)'s Simulation - Helix; the decode latency corresponds
to Figure 5(f)'s Simulation - Helix.
```bash
python step3_simulation.py helix llama30b online
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa30B online simulation results: Helix
Total decode throughput: 216.7 tokens/s
Prompt latency:
Latency 5th percentile: 0.10 s
Latency 25th percentile: 0.17 s
Latency 50th percentile: 0.43 s
Latency 75th percentile: 0.99 s
Latency 95th percentile: 2.95 s
Decode latency:
Latency 5th percentile: 0.06 s
Latency 25th percentile: 0.08 s
Latency 50th percentile: 0.13 s
Latency 75th percentile: 0.37 s
Latency 95th percentile: 0.70 s
************************************************************
```
We also store the raw latency distribution files as pickle files in
`./simulation_llama30b/ilp_online`. You can refer to `analyze_latency` in `step3_simulation.py`
if you want to parse and check them.

(5) Run LLaMA 30B in online setup using Swarm and observe its decode throughput, prompt latency
and decode latency. The decode throughput corresponds to Figure 5(b)'s Simulation - Swarm; the
prompt latency corresponds to Figure 5(e)'s Simulation - Swarm; the decode latency corresponds
to Figure 5(f)'s Simulation - Swarm.
```bash
python step3_simulation.py swarm llama30b online
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa30B online simulation results: Swarm
Total decode throughput: 104.9 tokens/s
Prompt latency:
Latency 5th percentile: 0.42 s
Latency 25th percentile: 0.71 s
Latency 50th percentile: 1.42 s
Latency 75th percentile: 1.75 s
Latency 95th percentile: 2.28 s
Decode latency:
Latency 5th percentile: 0.22 s
Latency 25th percentile: 0.25 s
Latency 50th percentile: 0.26 s
Latency 75th percentile: 0.29 s
Latency 95th percentile: 0.47 s
************************************************************
```
We also store the raw latency distribution files as pickle files in
`./simulation_llama30b/swarm_online`. You can refer to `analyze_latency` in `step3_simulation.py`
if you want to parse and check them.

(6) Run LLaMA 30B in online setup using Separate Pipelines and observe its decode throughput,
prompt latency and decode latency. The decode throughput corresponds to Figure 5(b)'s Simulation -
Separate Pipelines (SP); the prompt latency corresponds to Figure 5(e)'s Simulation - Separate
Pipelines (SP); the decode latency corresponds to Figure 5(f)'s Simulation - Separate Pipelines (SP).
```bash
python step3_simulation.py separate llama30b online
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa30B online simulation results: Separate
Total decode throughput: 189.8 tokens/s
Prompt latency:
Latency 5th percentile: 0.09 s
Latency 25th percentile: 0.16 s
Latency 50th percentile: 0.42 s
Latency 75th percentile: 1.07 s
Latency 95th percentile: 2.99 s
Decode latency:
Latency 5th percentile: 0.06 s
Latency 25th percentile: 0.08 s
Latency 50th percentile: 0.11 s
Latency 75th percentile: 0.33 s
Latency 95th percentile: 0.57 s
************************************************************
```
We also store the raw latency distribution files as pickle files in
`./simulation_llama30b/separate_online`. You can refer to `analyze_latency` in `step3_simulation.py`
if you want to parse and check them.

(7) Run LLaMA 70B in offline setup using Helix and observe its decode throughput. This
corresponds to Figure 5(c)'s Simulation - Helix in the paper.
```bash
python step3_simulation.py helix llama70b offline
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B offline simulation results: Helix
Total decode throughput: 252.1 tokens/s
************************************************************
```

(8) Run LLaMA 70B in offline setup using Swarm and observe its decode throughput. This
corresponds to Figure 5(c)'s Simulation - Swarm in the paper.
```bash
python step3_simulation.py swarm llama70b offline
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B offline simulation results: Swarm
Total decode throughput: 124.7 tokens/s
************************************************************
```

(9) Run LLaMA 70B in offline setup using Separate Pipelines and observe its decode throughput.
This corresponds to Figure 5(c)'s Simulation - Separate Pipelines (SP) in the paper.
```bash
python step3_simulation.py separate llama70b offline
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B offline simulation results: Separate
Total decode throughput: 124.3 tokens/s
************************************************************
```

(10) Run LLaMA 70B in online setup using Helix and observe its decode throughput, prompt latency
and decode latency. The decode throughput corresponds to Figure 5(d)'s Simulation - Helix; the
prompt latency corresponds to Figure 5(g)'s Simulation - Helix; the decode latency corresponds
to Figure 5(h)'s Simulation - Helix.
```bash
python step3_simulation.py helix llama70b online
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B online simulation results: Helix
Total decode throughput: 141.6 tokens/s
Prompt latency:
Latency 5th percentile: 0.80 s
Latency 25th percentile: 1.38 s
Latency 50th percentile: 2.64 s
Latency 75th percentile: 3.52 s
Latency 95th percentile: 4.41 s
Decode latency:
Latency 5th percentile: 0.56 s
Latency 25th percentile: 0.76 s
Latency 50th percentile: 0.98 s
Latency 75th percentile: 1.67 s
Latency 95th percentile: 3.19 s
************************************************************
```
We also store the raw latency distribution files as pickle files in
`./simulation_llama70b/ilp_online`. You can refer to `analyze_latency` in `step3_simulation.py`
if you want to parse and check them.

(11) Run LLaMA 70B in online setup using Swarm and observe its decode throughput, prompt latency
and decode latency. The decode throughput corresponds to Figure 5(d)'s Simulation - Swarm; the
prompt latency corresponds to Figure 5(g)'s Simulation - Swarm; the decode latency corresponds
to Figure 5(h)'s Simulation - Swarm.
```bash
python step3_simulation.py swarm llama70b online
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B online simulation results: Swarm
Total decode throughput: 69.8 tokens/s
Prompt latency:
Latency 5th percentile: 0.95 s
Latency 25th percentile: 1.70 s
Latency 50th percentile: 3.32 s
Latency 75th percentile: 4.04 s
Latency 95th percentile: 5.01 s
Decode latency:
Latency 5th percentile: 0.57 s
Latency 25th percentile: 0.82 s
Latency 50th percentile: 1.04 s
Latency 75th percentile: 1.59 s
Latency 95th percentile: 2.51 s
************************************************************
```
We also store the raw latency distribution files as pickle files in
`./simulation_llama70b/swarm_online`. You can refer to `analyze_latency` in `step3_simulation.py`
if you want to parse and check them.

(12) Run LLaMA 70B in online setup using Separate Pipelines and observe its decode throughput,
prompt latency and decode latency. The decode throughput corresponds to Figure 5(d)'s Simulation -
Separate Pipelines (SP); the prompt latency corresponds to Figure 5(g)'s Simulation - Separate
Pipelines (SP); the decode latency corresponds to Figure 5(h)'s Simulation - Separate Pipelines (SP).
```bash
python step3_simulation.py separate llama70b online
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B online simulation results: Separate
Total decode throughput: 84.0 tokens/s
Prompt latency:
Latency 5th percentile: 0.19 s
Latency 25th percentile: 0.36 s
Latency 50th percentile: 0.80 s
Latency 75th percentile: 1.48 s
Latency 95th percentile: 4.19 s
Decode latency:
Latency 5th percentile: 0.14 s
Latency 25th percentile: 0.14 s
Latency 50th percentile: 0.22 s
Latency 75th percentile: 0.69 s
Latency 95th percentile: 1.20 s
************************************************************
```
We also store the raw latency distribution files as pickle files in
`./simulation_llama70b/separate_online`. You can refer to `analyze_latency` in `step3_simulation.py`
if you want to parse and check them.

### Step 4: Run Prototype System Experiments

Now that we have reproduced the results for simulations, we can continue and reproduce the results
for the prototype system experiments.

> **Note:** In order to keep the total expense of artifact evaluation within the budget, we reduce
> the running time for each experiment. For offline experiments, we reduce the running time from 
> 10 minutes to 5 minutes. For online experiments, we reduce the running time from 30 minutes to
> 5 minutes. All results are based on the reduced running time, which might be slightly different
> from the results in the paper.

#### 1. LLaMA 30B + offline + Helix

Run the following command to generate real system config file:
```bash
python step4_gen_sys_config.py helix llama30b
```
This will generate the real system config file in each folder in `./layout_llama30b/ilp`. Next,
we will start running the real system experiments. Since in this setup helix has three sub-clusters,
we need to run three separate experiments.

On two separate terminals of the host machine, run the following command, this tests the A100 sub-cluster:
```bash
python step5_start_host.py helix_a100 llama30b offline          # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama30b maxflow"   # on host machine, terminal 2
```
After running the experiment, the log files are stored in `./real_llama30b/helix_offline/a100`.

> **Note:** Host terminal 1 is used to start the host machine, and host terminal 2 is used to
> start the worker machines remotely. After each experiment, host terminal 1 will automatically
> terminate. However, **you need to manually terminate host terminal 2 after each experiment**.

> **Note** **When a setup only uses a sub-cluster of the whole cluster, you may see some core**
> **dumps on terminal 2. This is normal and expected (unused machines are leaving). Also,**
> **when the host finishes, you will see a core dump on terminal 1. This is normal and does not**
> **affect the result.**

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py helix_a100 llama30b offline
```

You will see results like this
```
./real_llama30b/helix_offline/a100/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.14 s
Latency 25th percentile: 0.20 s
Latency 50th percentile: 0.40 s
Latency 75th percentile: 0.45 s
Latency 95th percentile: 0.66 s
Decode latency:
Latency 5th percentile: 0.11 s
Latency 25th percentile: 0.12 s
Latency 50th percentile: 0.14 s
Latency 75th percentile: 0.16 s
Latency 95th percentile: 0.43 s
Summary:
Avg prompt latency: 0.358s
Avg decode latency: 0.169s
Throughput: 198.9 Tokens/s
```

On two separate terminals of the host machine, run the following command, this tests the L4 sub-cluster:
```bash
python step5_start_host.py helix_l4 llama30b offline            # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama30b maxflow"   # on host machine, terminal 2
```
After running the experiment, the log files are stored in `./real_llama30b/helix_offline/l4`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py helix_l4 llama30b offline
```

You will see results like this
```
./real_llama30b/helix_offline/l4/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.45 s
Latency 25th percentile: 0.57 s
Latency 50th percentile: 0.98 s
Latency 75th percentile: 1.41 s
Latency 95th percentile: 1.65 s
Decode latency:
Latency 5th percentile: 0.39 s
Latency 25th percentile: 0.43 s
Latency 50th percentile: 0.46 s
Latency 75th percentile: 0.51 s
Latency 95th percentile: 1.22 s
Summary:
Avg prompt latency: 1.001s
Avg decode latency: 0.533s
Throughput: 64.8 Tokens/s
```

On two separate terminals of the host machine, run the following command, this tests the T4 sub-cluster:
```bash
python step5_start_host.py helix_t4 llama30b offline            # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama30b maxflow"   # on all 24 worker machines
```

After running the experiment, the log files are stored in `./real_llama30b/helix_offline/t4`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py helix_t4 llama30b offline
```

You will see results like this
```
./real_llama30b/helix_offline/t4/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.55 s
Latency 25th percentile: 1.03 s
Latency 50th percentile: 2.79 s
Latency 75th percentile: 3.51 s
Latency 95th percentile: 6.10 s
Decode latency:
Latency 5th percentile: 0.39 s
Latency 25th percentile: 0.43 s
Latency 50th percentile: 0.46 s
Latency 75th percentile: 0.51 s
Latency 95th percentile: 2.79 s
Summary:
Avg prompt latency: 2.405s
Avg decode latency: 0.697s
Throughput: 57.5 Tokens/s
```

The total decode throughput is 321.2, corresponding to Figure 5(a) Prototype - Helix in the paper.

#### 2. LLaMA 30B + online + Helix

The real system config has already been generated in (1). 
On two separate terminals of the host machine, run the following command, this tests the A100
sub-cluster:
```bash
python step5_start_host.py helix_a100 llama30b online           # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama30b maxflow"   # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama30b/helix_online/a100`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py helix_a100 llama30b online
```

You will see results like this
```
./real_llama30b/helix_online/a100/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.17 s
Latency 25th percentile: 0.21 s
Latency 50th percentile: 0.41 s
Latency 75th percentile: 0.46 s
Latency 95th percentile: 0.63 s
Decode latency:
Latency 5th percentile: 0.10 s
Latency 25th percentile: 0.11 s
Latency 50th percentile: 0.12 s
Latency 75th percentile: 0.13 s
Latency 95th percentile: 0.26 s
Summary:
Avg prompt latency: 0.367s
Avg decode latency: 0.138s
Throughput: 136.4 Tokens/s
```

On two separate terminals of the host machine, run the following command, this tests the L4 sub-cluster:
```bash
python step5_start_host.py helix_l4 llama30b online             # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama30b maxflow"   # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama30b/helix_online/l4`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py helix_l4 llama30b online
```

You will see results like this
```
./real_llama30b/helix_online/l4/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.46 s
Latency 25th percentile: 0.61 s
Latency 50th percentile: 1.24 s
Latency 75th percentile: 1.39 s
Latency 95th percentile: 1.97 s
Decode latency:
Latency 5th percentile: 0.31 s
Latency 25th percentile: 0.34 s
Latency 50th percentile: 0.37 s
Latency 75th percentile: 0.41 s
Latency 95th percentile: 0.57 s
Summary:
Avg prompt latency: 1.077s
Avg decode latency: 0.415s
Throughput: 32.2 Tokens/s
```

On two separate terminals of the host machine, run the following command, this tests the T4 sub-cluster:
```bash
python step5_start_host.py helix_t4 llama30b online             # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama30b maxflow"   # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama30b/helix_online/t4`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py helix_t4 llama30b online
```

You will see results like this
```
./real_llama30b/helix_online/t4/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.55 s
Latency 25th percentile: 0.87 s
Latency 50th percentile: 1.35 s
Latency 75th percentile: 3.03 s
Latency 95th percentile: 5.10 s
Decode latency:
Latency 5th percentile: 0.29 s
Latency 25th percentile: 0.32 s
Latency 50th percentile: 0.35 s
Latency 75th percentile: 0.38 s
Latency 95th percentile: 0.90 s
Summary:
Avg prompt latency: 2.146s
Avg decode latency: 0.472s
Throughput: 29.3 Tokens/s
```

The total decode throughput is 198, corresponding to Figure 5(b) Prototype - Helix in the paper.
The average prompt latency is 0.740, corresponding to Figure 5(e) Prototype - Helix in the paper.
The average decode latency is 0.231, corresponding to Figure 5(f) Prototype - Helix in the paper.

Run the following command to get the aggregated percentile latency distribution for this setup:
```bash
python step7_parse_results.py helix llama30b online
```

You will see the following results that correspond to Figure 5(e) and Figure 5(f) Prototype - 
Helix in the paper:
```
./real_llama30b/helix_online/a100/events.txt (excluding first 60s as warm up)
./real_llama30b/helix_online/l4/events.txt (excluding first 60s as warm up)
./real_llama30b/helix_online/t4/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.18 s
Latency 25th percentile: 0.37 s
Latency 50th percentile: 0.46 s
Latency 75th percentile: 0.84 s
Latency 95th percentile: 2.92 s
Decode latency:
Latency 5th percentile: 0.11 s
Latency 25th percentile: 0.11 s
Latency 50th percentile: 0.13 s
Latency 75th percentile: 0.33 s
Latency 95th percentile: 0.45 s
```

#### 3. LLaMA 30B + offline + Swarm

Generate the real system config file with the following command:
```bash
python step4_gen_sys_config.py swarm llama30b
```
This will generate the real system config file in `./layout_llama30b/swarm`.

On two separate terminals of the host machine, run the following command:
```bash
python step5_start_host.py swarm llama30b offline             # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama30b swarm"   # on all 24 worker machines
```

After running the experiment, the log files are stored in `./real_llama30b/swarm_offline`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py swarm llama30b offline
```

You will see results like this
```
./real_llama30b/swarm_offline/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.42 s
Latency 25th percentile: 0.66 s
Latency 50th percentile: 1.36 s
Latency 75th percentile: 1.65 s
Latency 95th percentile: 2.16 s
Decode latency:
Latency 5th percentile: 0.26 s
Latency 25th percentile: 0.29 s
Latency 50th percentile: 0.31 s
Latency 75th percentile: 0.35 s
Latency 95th percentile: 0.58 s
Summary:
Avg prompt latency: 1.237s
Avg decode latency: 0.345s
Throughput: 142.9 Tokens/s
```
The total decode throughput is 142.9, corresponding to Figure 5(a) Prototype - Swarm in the paper.

#### 4. LLaMA 30B + online + Swarm

The real system config has already been generated in (3). On two separate terminals of the host machine, run
the following command:
```bash
python step5_start_host.py swarm llama30b online              # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama30b swarm"   # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama30b/swarm_online`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py swarm llama30b online
```

You will see results like this
```
./real_llama30b/swarm_online/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.43 s
Latency 25th percentile: 0.70 s
Latency 50th percentile: 1.35 s
Latency 75th percentile: 1.65 s
Latency 95th percentile: 2.06 s
Decode latency:
Latency 5th percentile: 0.23 s
Latency 25th percentile: 0.26 s
Latency 50th percentile: 0.28 s
Latency 75th percentile: 0.32 s
Latency 95th percentile: 0.51 s
Summary:
Avg prompt latency: 1.243s
Avg decode latency: 0.309s
Throughput: 102.3 Tokens/s
```

The decode throughput is 102.3, corresponding to Figure 5(b) Prototype - Swarm in the paper.
The average prompt latency is 1.243, corresponding to Figure 5(e) Prototype - Swarm in the paper.
The average decode latency is 0.309, corresponding to Figure 5(f) Prototype - Swarm in the paper.
The prompt and decode latency percentiles correspond to Figure 5(e) and Figure 5(f) Prototype - Swarm in the paper.

#### 5. LLaMA 30B + offline + Separate Pipelines

Generate the real system config file with the following command:
```bash
python step4_gen_sys_config.py separate llama30b
```
This will generate the real system config file in each folder in `./layout_llama30b/separate`.

On two separate terminals of the host machine, run the following command, this tests the A100 sub-cluster:
```bash
python step5_start_host.py separate_a100 llama30b offline       # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama30b random"    # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama30b/separate_offline/a100`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py separate_a100 llama30b offline
```

You will see results like this
```
./real_llama30b/separate_offline/a100/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.13 s
Latency 25th percentile: 0.20 s
Latency 50th percentile: 0.40 s
Latency 75th percentile: 0.46 s
Latency 95th percentile: 0.66 s
Decode latency:
Latency 5th percentile: 0.10 s
Latency 25th percentile: 0.12 s
Latency 50th percentile: 0.14 s
Latency 75th percentile: 0.14 s
Latency 95th percentile: 0.41 s
Summary:
Avg prompt latency: 0.357s
Avg decode latency: 0.159s
Throughput: 187.3 Tokens/s
```

On two separate terminals of the host machine, run the following command, this tests the L4 sub-cluster:
```bash
python step5_start_host.py separate_l4 llama30b offline         # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama30b random"    # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama30b/separate_offline/l4`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py separate_l4 llama30b offline
```

You will see results like this
```
./real_llama30b/separate_offline/l4/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.44 s
Latency 25th percentile: 0.55 s
Latency 50th percentile: 1.22 s
Latency 75th percentile: 1.41 s
Latency 95th percentile: 1.68 s
Decode latency:
Latency 5th percentile: 0.37 s
Latency 25th percentile: 0.43 s
Latency 50th percentile: 0.44 s
Latency 75th percentile: 0.48 s
Latency 95th percentile: 1.11 s
Summary:
Avg prompt latency: 1.039s
Avg decode latency: 0.507s
Throughput: 58.6 Tokens/s
```

On two separate terminals of the host machine, run the following command, this tests the T4 sub-cluster:
```bash
python step5_start_host.py separate_t4 llama30b offline         # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama30b random"    # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama30b/separate_offline/t4`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py separate_t4 llama30b offline
```

You will see results like this
```
./real_llama30b/separate_offline/t4/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.51 s
Latency 25th percentile: 0.83 s
Latency 50th percentile: 1.14 s
Latency 75th percentile: 3.06 s
Latency 95th percentile: 4.01 s
Decode latency:
Latency 5th percentile: 0.36 s
Latency 25th percentile: 0.40 s
Latency 50th percentile: 0.43 s
Latency 75th percentile: 0.47 s
Latency 95th percentile: 2.42 s
Summary:
Avg prompt latency: 1.896s
Avg decode latency: 0.601s
Throughput: 49.2 Tokens/s
```

The total decode throughput is 295.1, corresponding to Figure 5(a) Prototype - Separate Pipelines (SP) in the paper.

#### 6. LLaMA 30B + online + Separate Pipelines

The real system config has already been generated in (5). 
On two separate terminals of the host machine, run
the following command, this tests the A100 sub-cluster:
```bash
python step5_start_host.py separate_a100 llama30b online        # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama30b random"    # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama30b/separate_online/a100`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py separate_a100 llama30b online
```

You will see results like this
```
./real_llama30b/separate_online/a100/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.13 s
Latency 25th percentile: 0.21 s
Latency 50th percentile: 0.41 s
Latency 75th percentile: 0.45 s
Latency 95th percentile: 0.63 s
Decode latency:
Latency 5th percentile: 0.09 s
Latency 25th percentile: 0.10 s
Latency 50th percentile: 0.11 s
Latency 75th percentile: 0.12 s
Latency 95th percentile: 0.18 s
Summary:
Avg prompt latency: 0.359s
Avg decode latency: 0.126s
Throughput: 118.9 Tokens/s
```

On two separate terminals of the host machine, run the following command, this tests the L4 sub-cluster:
```bash
python step5_start_host.py separate_l4 llama30b online          # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama30b random"    # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama30b/separate_online/l4`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py separate_l4 llama30b online
```

You will see results like this
```
./real_llama30b/separate_online/l4/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.44 s
Latency 25th percentile: 0.61 s
Latency 50th percentile: 0.74 s
Latency 75th percentile: 1.38 s
Latency 95th percentile: 1.63 s
Decode latency:
Latency 5th percentile: 0.28 s
Latency 25th percentile: 0.32 s
Latency 50th percentile: 0.33 s
Latency 75th percentile: 0.36 s
Latency 95th percentile: 0.47 s
Summary:
Avg prompt latency: 0.999s
Avg decode latency: 0.368s
Throughput: 27.8 Tokens/s
```

On two separate terminals of the host machine, run the following command, this tests the T4 sub-cluster:
```bash
python step5_start_host.py separate_t4 llama30b online         # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama30b random"   # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama30b/separate_online/t4`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py separate_t4 llama30b online
```

You will see results like this
```
./real_llama30b/separate_online/t4/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.53 s
Latency 25th percentile: 0.86 s
Latency 50th percentile: 1.35 s
Latency 75th percentile: 3.01 s
Latency 95th percentile: 4.21 s
Decode latency:
Latency 5th percentile: 0.29 s
Latency 25th percentile: 0.29 s
Latency 50th percentile: 0.32 s
Latency 75th percentile: 0.34 s
Latency 95th percentile: 0.74 s
Summary:
Avg prompt latency: 2.042s
Avg decode latency: 0.416s
Throughput: 26.4 Tokens/s
```

The total decode throughput is 173.1, corresponding to Figure 5(b) Prototype - Separate Pipelines (SP) in the paper.
The average prompt latency is 0.719, corresponding to Figure 5(e) Prototype - Separate Pipelines (SP) in the paper.
The average decode latency is 0.209, corresponding to Figure 5(f) Prototype - Separate Pipelines (SP) in the paper.

Run the following command to get the aggregated percentile latency distribution for this setup:
```bash
python step7_parse_results.py separate llama30b online
```

You will see the following results that correspond to Figure 5(e) and Figure 5(f) Prototype -
Separate Pipelines (SP) in the paper:
```
./real_llama30b/separate_online/a100/events.txt (excluding first 60s as warm up)
./real_llama30b/separate_online/l4/events.txt (excluding first 60s as warm up)
./real_llama30b/separate_online/t4/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.14 s
Latency 25th percentile: 0.36 s
Latency 50th percentile: 0.45 s
Latency 75th percentile: 0.77 s
Latency 95th percentile: 2.97 s
Decode latency:
Latency 5th percentile: 0.09 s
Latency 25th percentile: 0.11 s
Latency 50th percentile: 0.12 s
Latency 75th percentile: 0.31 s
Latency 95th percentile: 0.40 s
```

#### 7. LLaMA 70B + offline + Helix

Generate the real system config file with the following command:
```bash
python step4_gen_sys_config.py helix llama70b
```

This will generate the real system config file in each folder in `./layout_llama70b/ilp`. Next,
we will start running the real system experiments.

On two separate terminals of the host machine, run the following command:
```bash
python step5_start_host.py helix llama70b offline               # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama70b maxflow"   # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama70b/helix_offline`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py helix llama70b offline
```

You will see results like this
```
./real_llama70b/helix_offline/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 1.02 s
Latency 25th percentile: 1.78 s
Latency 50th percentile: 3.24 s
Latency 75th percentile: 4.16 s
Latency 95th percentile: 5.35 s
Decode latency:
Latency 5th percentile: 0.69 s
Latency 25th percentile: 1.00 s
Latency 50th percentile: 1.42 s
Latency 75th percentile: 2.23 s
Latency 95th percentile: 3.76 s
Summary:
Avg prompt latency: 3.147s
Avg decode latency: 1.750s
Throughput: 223.4 Tokens/s
```

The total decode throughput is 223.4, corresponding to Figure 5(c) Prototype - Helix in the paper.

#### 8. LLaMA 70B + online + Helix

The real system config has already been generated in (7). 
On two separate terminals of the host machine, run
the following command:
```bash
python step5_start_host.py helix llama70b online                # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama70b maxflow"   # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama70b/helix_online`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py helix llama70b online
```

You will see results like this
```
./real_llama70b/helix_online/events.txt (excluding first 200s as warm up)
Prompt latency:
Latency 5th percentile: 1.03 s
Latency 25th percentile: 1.60 s
Latency 50th percentile: 2.86 s
Latency 75th percentile: 3.58 s
Latency 95th percentile: 4.33 s
Decode latency:
Latency 5th percentile: 0.78 s
Latency 25th percentile: 1.13 s
Latency 50th percentile: 1.80 s
Latency 75th percentile: 2.87 s
Latency 95th percentile: 3.60 s
Summary:
Avg prompt latency: 2.660s
Avg decode latency: 2.020s
Throughput: 148.3 Tokens/s
```

The decode throughput is 148.3, corresponding to Figure 5(d) Prototype - Helix in the paper.
The average prompt latency is 2.660, corresponding to Figure 5(g) Prototype - Helix in the paper.
The average decode latency is 2.020, corresponding to Figure 5(h) Prototype - Helix in the paper.
The prompt and decode latency percentiles correspond to Figure 5(g) and Figure 5(h) Prototype - Helix in the paper.

#### 9. LLaMA 70B + offline + Swarm

Generate the real system config file with the following command:
```bash
python step4_gen_sys_config.py swarm llama70b
```

This will generate the real system config file in each folder in `./layout_llama70b/swarm`. Next,
we will start running the real system experiments.

On two separate terminals of the host machine, run the following command:
```bash
python step5_start_host.py swarm llama70b offline             # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama70b swarm"   # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama70b/swarm_offline`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py swarm llama70b offline
```

You will see results like this
```
./real_llama70b/swarm_offline/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 1.04 s
Latency 25th percentile: 1.64 s
Latency 50th percentile: 3.47 s
Latency 75th percentile: 4.04 s
Latency 95th percentile: 5.18 s
Decode latency:
Latency 5th percentile: 0.73 s
Latency 25th percentile: 0.97 s
Latency 50th percentile: 1.49 s
Latency 75th percentile: 1.93 s
Latency 95th percentile: 3.23 s
Summary:
Avg prompt latency: 3.060s
Avg decode latency: 1.598s
Throughput: 111.7 Tokens/s
```

The total decode throughput is 111.7, corresponding to Figure 5(c) Prototype - Swarm in the paper.

#### 10. LLaMA 70B + online + Swarm

The real system config has already been generated in (9). 
On two separate terminals of the host machine, run
the following command:
```bash
python step5_start_host.py swarm llama70b online              # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama70b swarm"   # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama70b/swarm_online`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py swarm llama70b online
```

You will see results like this
```
./real_llama70b/swarm_online/events.txt (excluding first 200s as warm up)
Prompt latency:
Latency 5th percentile: 0.99 s
Latency 25th percentile: 1.82 s
Latency 50th percentile: 3.53 s
Latency 75th percentile: 4.04 s
Latency 95th percentile: 4.37 s
Decode latency:
Latency 5th percentile: 0.76 s
Latency 25th percentile: 1.16 s
Latency 50th percentile: 1.52 s
Latency 75th percentile: 1.98 s
Latency 95th percentile: 3.19 s
Summary:
Avg prompt latency: 3.022s
Avg decode latency: 1.639s
Throughput: 81.1 Tokens/s
```

The decode throughput is 81.1, corresponding to Figure 5(d) Prototype - Swarm in the paper.
The average prompt latency is 3.022, corresponding to Figure 5(g) Prototype - Swarm in the paper.
The average decode latency is 1.639, corresponding to Figure 5(h) Prototype - Swarm in the paper.
The prompt and decode latency percentiles correspond to Figure 5(g) and Figure 5(h) Prototype - Swarm in the paper.

#### 11. LLaMA 70B + offline + Separate Pipelines

We manually generated the real system config file for the separate pipelines method. The config
files are located in `./layout_llama70b/separate`. Next, we will start running the real system
experiments.

On two separate terminals of the host machine, run the following command, this tests the A100 sub-cluster:
```bash
python step5_start_host.py separate_a100 llama70b offline         # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama70b random 0.9"  # on host machine, terminal 2
```
We need to set vLLM's max vram usage to 0.9 to avoid out-of-memory errors. This is because the number
of layers assigned to each GPU is larger than the recommended value, reflecting that the model placement
is not optimal.

After running the experiment, the log files are stored in `./real_llama70b/separate_offline/a100`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py separate_a100 llama70b offline
```

You will see results like this
```
./real_llama70b/separate_offline/a100/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.31 s
Latency 25th percentile: 5.80 s
Latency 50th percentile: 19.25 s
Latency 75th percentile: 65.52 s
Latency 95th percentile: 85.37 s
Decode latency:
Latency 5th percentile: 0.16 s
Latency 25th percentile: 0.19 s
Latency 50th percentile: 0.21 s
Latency 75th percentile: 0.22 s
Latency 95th percentile: 0.40 s
Summary:
Avg prompt latency: 31.670s
Avg decode latency: 0.284s
Throughput: 68.7 Tokens/s
```

On two separate terminals of the host machine, run the following command, this tests the L4 sub-cluster:
```bash
python step5_start_host.py separate_l4 llama70b offline           # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama70b random 0.9"  # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama70b/separate_offline/l4`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py separate_l4 llama70b offline
```

You will see results like this
```
./real_llama70b/separate_offline/l4/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.88 s
Latency 25th percentile: 1.26 s
Latency 50th percentile: 1.33 s
Latency 75th percentile: 2.87 s
Latency 95th percentile: 3.46 s
Decode latency:
Latency 5th percentile: 0.71 s
Latency 25th percentile: 0.83 s
Latency 50th percentile: 0.89 s
Latency 75th percentile: 1.05 s
Latency 95th percentile: 2.50 s
Summary:
Avg prompt latency: 1.984s
Avg decode latency: 1.048s
Throughput: 37.9 Tokens/s
```

On two separate terminals of the host machine, run the following command, this tests the T4 sub-cluster:
```bash
python step5_start_host.py separate_t4 llama70b offline             # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama70b random 0.9"    # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama70b/separate_offline/t4`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py separate_t4 llama70b offline
```

You will see results like this
```
./real_llama70b/separate_offline/t4/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.91 s
Latency 25th percentile: 2.17 s
Latency 50th percentile: 2.22 s
Latency 75th percentile: 6.56 s
Latency 95th percentile: 6.56 s
Decode latency:
Latency 5th percentile: 0.57 s
Latency 25th percentile: 0.57 s
Latency 50th percentile: 0.57 s
Latency 75th percentile: 0.58 s
Latency 95th percentile: 0.59 s
Summary:
Avg prompt latency: 2.964s
Avg decode latency: 0.614s
Throughput: 3.4 Tokens/s
```

The total decode throughput is 110.0, corresponding to Figure 5(c) Prototype - Separate Pipelines (SP) in the paper.


#### 12. LLaMA 70B + online + Separate Pipelines

The real system config has already been generated in (11). 
On two separate terminals of the host machine, run
the following command, this tests the A100 sub-cluster:
```bash
python step5_start_host.py separate_a100 llama70b online          # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama70b random 0.9"  # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama70b/separate_online/a100`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py separate_a100 llama70b online
```

You will see results like this
```
./real_llama70b/separate_online/a100/events.txt (excluding first 200s as warm up)
Prompt latency:
Latency 5th percentile: 0.26 s
Latency 25th percentile: 0.37 s
Latency 50th percentile: 0.71 s
Latency 75th percentile: 0.77 s
Latency 95th percentile: 0.83 s
Decode latency:
Latency 5th percentile: 0.18 s
Latency 25th percentile: 0.18 s
Latency 50th percentile: 0.21 s
Latency 75th percentile: 0.22 s
Latency 95th percentile: 0.25 s
Summary:
Avg prompt latency: 0.571s
Avg decode latency: 0.212s
Throughput: 57.8 Tokens/s
```

On two separate terminals of the host machine, run the following command, this tests the L4 sub-cluster:
```bash
python step5_start_host.py separate_l4 llama70b online            # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama70b random 0.9"  # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama70b/separate_online/l4`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py separate_l4 llama70b online
```

You will see results like this
```
./real_llama70b/separate_online/l4/events.txt (excluding first 200s as warm up)
Prompt latency:
Latency 5th percentile: 0.88 s
Latency 25th percentile: 1.32 s
Latency 50th percentile: 2.82 s
Latency 75th percentile: 2.87 s
Latency 95th percentile: 3.72 s
Decode latency:
Latency 5th percentile: 0.66 s
Latency 25th percentile: 0.75 s
Latency 50th percentile: 0.82 s
Latency 75th percentile: 0.88 s
Latency 95th percentile: 2.20 s
Summary:
Avg prompt latency: 2.282s
Avg decode latency: 0.915s
Throughput: 18.9 Tokens/s
```

On two separate terminals of the host machine, run the following command, this tests the T4 sub-cluster:
```bash
python step5_start_host.py separate_t4 llama70b online            # on host machine, terminal 1
python remote_run.py "step6_start_worker.py llama70b random 0.9"  # on host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_llama70b/separate_online/t4`.

Parse the results with the following command on the host machine:
```bash
python step7_parse_results.py separate_t4 llama70b online
```

You will see results like this
```
./real_llama70b/separate_online/t4/events.txt (excluding first 200s as warm up)
Prompt latency:
Latency 5th percentile: 3.27 s
Latency 25th percentile: 3.27 s
Latency 50th percentile: 3.27 s
Latency 75th percentile: 3.27 s
Latency 95th percentile: 3.27 s
Decode latency:
Latency 5th percentile: 0.58 s
Latency 25th percentile: 0.58 s
Latency 50th percentile: 0.58 s
Latency 75th percentile: 0.58 s
Latency 95th percentile: 0.59 s
Summary:
Avg prompt latency: 3.266s
Avg decode latency: 0.599s
Throughput: 3.4 Tokens/s
```

The total decode throughput is 80.1, corresponding to Figure 5(d) Prototype - Separate Pipelines (SP) in the paper.
The average prompt latency is 1.119, corresponding to Figure 5(g) Prototype - Separate Pipelines (SP) in the paper.
The average decode latency is 0.401, corresponding to Figure 5(h) Prototype - Separate Pipelines (SP) in the paper.

Run the following command to get the aggregated percentile latency distribution for this setup:
```bash
python step7_parse_results.py separate llama70b online
```

You will see the following results that correspond to Figure 5(g) and Figure 5(h) Prototype -
Separate Pipelines (SP) in the paper:
```
./real_llama70b/separate_online/a100/events.txt (excluding first 200s as warm up)
./real_llama70b/separate_online/l4/events.txt (excluding first 200s as warm up)
./real_llama70b/separate_online/t4/events.txt (excluding first 200s as warm up)
Prompt latency:
Latency 5th percentile: 0.26 s
Latency 25th percentile: 0.40 s
Latency 50th percentile: 0.77 s
Latency 75th percentile: 1.32 s
Latency 95th percentile: 3.27 s
Decode latency:
Latency 5th percentile: 0.18 s
Latency 25th percentile: 0.18 s
Latency 50th percentile: 0.21 s
Latency 75th percentile: 0.59 s
Latency 95th percentile: 0.89 s
```

## Section 6.4 Geo-Distributed Clusters

All files related to this group of experiments are located in `artifact_evaluation/distributed_clusters`.
Start from the root directory of the repository:
```bash
cd artifact_evaluation/distributed_clusters
```
The workflow is similar to the single cluster experiments.

### Step 1: Generate Cluster Config Files
Run the following command to generate cluster config files:
```bash
python step1_gen_cluster.py
```
This will automatically generate the config file that represents a geo-distributed cluster with
24 machines (4 1xA100 machines, 8 1xL4 machines, 12 1xT4 machines) in `config/3cluster24.ini`.
The cluster contains three regions. In region 1, there are 4 A100 machines; in region 2, there
are 2 L4 machines and 8 T4 machines; in region 3, there are 6 L4 machines and 4 T4 machines.
It also creates the config files that represent the sub-clusters formed by each type of machine:
`config/a100.ini`, `config/l4.ini` and `config/t4.ini`.

### Step 2: Model Placement

The next step is to generate the model placement for the cluster. Run the following commands
to generate model placements for LLaMA-1 30B and LLaMA-2 70B using different model placement
methods. 

Notice that before running Helix's MILP-based model placement planner, you need to
**backup and empty** the `./layout_llama30b/ilp` and `./layout_llama70b/ilp` directories,
which currently contains the result we get. If the directories are not empty, you will get
an error from the model placement planner saying that the directory is not empty. After you
have finished evaluating Helix's model placement planner, you can restore the two directories
to facilitate the evaluation of later steps.

Also, for `llama70b`, you need to run `swarm` before running
Helix's MILP model placement planner, as we bootstrap the solver with `swarm`'s solution.

> **Notes:** We notice that Gurobi produces completely different optimization traces when
> using **different licenses, even when using the same random seed**. When using the default
> limited license, the optimization performance is much worse than that of using the academic
> license. (objective value = 952 v.s. 1212) Unfortunately, we are not allowed and unable to
> bind our academic Gurobi license to the cluster provided. Note that this is an issue with
> Gurobi **licensing** instead of our system, and we provide our optimization trace in
> `./layout_llama70b/ilp/trace.txt` for you to compare against.

> **Notes:** Running Helix to search for a model placement for LLaMA 70B may take a long time.
> We set the max running time to 10 hours, but you can stop the solver at any time with `ctrl +c`. 
> In our experiments, on a machine with 14 cores and academic license, we manually early-stop
> the solver at round 45 minutes. This solution at this point already has good quality. The
> objective value (Incumbent) equals to 1212.

```bash
# Generate model placement using heuristic method Petals
python step2_gen_layout.py petals llama30b
python step2_gen_layout.py petals llama70b
# Generate model placement using heuristic method Swarm
python step2_gen_layout.py swarm llama30b
python step2_gen_layout.py swarm llama70b
# Generate model placement using heuristic method separate pipelines
python step2_gen_layout.py separate llama30b
python step2_gen_layout.py separate llama70b
# Generate model placement using Helix's MILP-based method
python step2_gen_layout.py ilp llama30b  # empty ./layout_llama30b/ilp before running
python step2_gen_layout.py ilp llama70b  # empty ./layout_llama70b/ilp before running
```

After running the commands above, you will get model placement files located in:
+ **petals & llama 30b**: `./layout_llama30b/petals` (`petals_sol.ini` and `simulator_cluster.ini`)
+ **petals & llama 70b**: `./layout_llama70b/petals` (`petals_sol.ini` and `simulator_cluster.ini`)
+ **swarm & llama 30b**: `./layout_llama30b/swarm` (`swarm_sol.ini` and `simulator_cluster.ini`)
+ **swarm & llama 70b**: `./layout_llama70b/swarm` (`swarm_sol.ini` and `simulator_cluster.ini`)
+ **separate & llama 30b**: `./layout_llama30b/separate` (6 manually created files)
+ **separate & llama 70b**: `./layout_llama70b/separate` (6 manually created files)
+ **ilp & llama 30b**: `./layout_llama30b/ilp/a100`, `./layout_llama30b/ilp/l4`, `./layout_llama30b/ilp/t4`, each containing the model placement for a sub-cluster
+ **ilp & llama 70b**: `./layout_llama70b/ilp` (`ilp_sol.ini` and `simulator_cluster.ini`, and 3 other files that records information about the MILP problem)

### Step 3: Run Simulation
With the model placement files generated, we can run the simulation and reproduce the results in the
paper.

> **Notes:** Before running simulation, you can restore the `./layout_llama30b/ilp` and
> `./layout_llama70b/ilp` directories you just backed up.

(1) Run LLaMA 30B in offline setup using Helix and observe its decode throughput. This
corresponds to Figure 7(a)'s offline - Helix in the paper.
```bash
python step3_simulation.py helix llama30b offline
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa30B offline simulation results: Helix
Total decode throughput: 232.7 tokens/s
************************************************************
```
The result here is slightly different from the one in the paper, as the model placement
found is slightly different.

(2) Run LLaMA 30B in offline setup using Swarm and observe its decode throughput. This
corresponds to Figure 7(a)'s offline - Swarm in the paper.
```bash
python step3_simulation.py swarm llama30b offline
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa30B offline simulation results: Swarm
Total decode throughput: 98.7 tokens/s
************************************************************
```

(3) Run LLaMA 30B in offline setup using Separate Pipelines and observe its decode
throughput. This corresponds to Figure 7(a)'s offline - Separate Pipelines (SP) in the paper.
```bash
python step3_simulation.py separate llama30b offline
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa30B offline simulation results: Separate
Total decode throughput: 223.2 tokens/s
************************************************************
```

(4) Run LLaMA 30B in online setup using Helix and observe its decode throughput, prompt latency
and decode latency. The decode throughput corresponds to Figure 7(a)'s online - Helix; the
prompt latency corresponds to Figure 7(c)'s Helix (H); the decode latency corresponds to Figure
7(d)'s Helix (H).
```bash
python step3_simulation.py helix llama30b online
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa30B online simulation results: Helix
Total decode throughput: 183.5 tokens/s
Prompt latency:
Latency 5th percentile: 0.18 s
Latency 25th percentile: 0.25 s
Latency 50th percentile: 0.51 s
Latency 75th percentile: 1.37 s
Latency 95th percentile: 4.41 s
Decode latency:
Latency 5th percentile: 0.16 s
Latency 25th percentile: 0.18 s
Latency 50th percentile: 0.23 s
Latency 75th percentile: 0.47 s
Latency 95th percentile: 0.83 s
************************************************************
```
The result here is slightly different from the one in the paper, as the model placement
found is slightly different.

We also store the raw latency distribution files as pickle files in
`./simulation_llama30b/ilp_online`. You can refer to `analyze_latency` in `step3_simulation.py`
if you want to parse and check them.

(5) Run LLaMA 30B in online setup using Swarm and observe its decode throughput, prompt latency
and decode latency. The decode throughput corresponds to Figure 7(a)'s online - Swarm; the
prompt latency corresponds to Figure 7(c)'s Swarm (S); the decode latency corresponds to Figure
7(d)'s Swarm (S).
```bash
python step3_simulation.py swarm llama30b online
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa30B online simulation results: Swarm
Total decode throughput: 82.1 tokens/s
Prompt latency:
Latency 5th percentile: 0.98 s
Latency 25th percentile: 1.82 s
Latency 50th percentile: 3.25 s
Latency 75th percentile: 5.10 s
Latency 95th percentile: 7.32 s
Decode latency:
Latency 5th percentile: 0.38 s
Latency 25th percentile: 0.43 s
Latency 50th percentile: 0.48 s
Latency 75th percentile: 0.53 s
Latency 95th percentile: 1.12 s
************************************************************
```
We also store the raw latency distribution files as pickle files in
`./simulation_llama30b/swarm_online`. You can refer to `analyze_latency` in `step3_simulation.py`
if you want to parse and check them.

(6) Run LLaMA 30B in online setup using Separate Pipelines and observe its decode throughput,
prompt latency and decode latency. The decode throughput corresponds to Figure 7(a)'s online -
Separate Pipelines (SP); the prompt latency corresponds to Figure 7(c)'s Separate Pipelines (SP);
the decode latency corresponds to Figure 7(d)'s Separate Pipelines (SP).
```bash
python step3_simulation.py separate llama30b online
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa30B online simulation results: Separate
Total decode throughput: 173.8 tokens/s
Prompt latency:
Latency 5th percentile: 0.18 s
Latency 25th percentile: 0.25 s
Latency 50th percentile: 0.50 s
Latency 75th percentile: 1.72 s
Latency 95th percentile: 6.47 s
Decode latency:
Latency 5th percentile: 0.16 s
Latency 25th percentile: 0.18 s
Latency 50th percentile: 0.23 s
Latency 75th percentile: 0.46 s
Latency 95th percentile: 0.92 s
************************************************************
```
We also store the raw latency distribution files as pickle files in
`./simulation_llama30b/separate_online`. You can refer to `analyze_latency` in `step3_simulation.py`
if you want to parse and check them.

(7) Run LLaMA 70B in offline setup using Helix and observe its decode throughput. This
corresponds to Figure 7(b)'s offline - Helix in the paper.
```bash
python step3_simulation.py helix llama70b offline
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B offline simulation results: Helix
Total decode throughput: 98.0 tokens/s
************************************************************
```
    
(8) Run LLaMA 70B in offline setup using Swarm and observe its decode throughput. This
corresponds to Figure 7(b)'s offline - Swarm in the paper.
```bash
python step3_simulation.py swarm llama70b offline
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B offline simulation results: Swarm
Total decode throughput: 51.9 tokens/s
************************************************************
```

(9) Run LLaMA 70B in offline setup using Separate Pipelines and observe its decode throughput.
This corresponds to Figure 7(b)'s offline - Separate Pipelines (SP) in the paper.
```bash
python step3_simulation.py separate llama70b offline
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B offline simulation results: Separate
Total decode throughput: 61.9 tokens/s
************************************************************
```

(10) Run LLaMA 70B in online setup using Helix and observe its decode throughput, prompt latency
and decode latency. The decode throughput corresponds to Figure 7(b)'s online - Helix; the
prompt latency corresponds to Figure 7(e)'s Helix (H); the decode latency corresponds to Figure
7(f)'s Helix (H).
```bash
python step3_simulation.py helix llama70b online
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B online simulation results: Helix
Total decode throughput: 59.3 tokens/s
Prompt latency:
Latency 5th percentile: 1.50 s
Latency 25th percentile: 2.63 s
Latency 50th percentile: 5.79 s
Latency 75th percentile: 7.53 s
Latency 95th percentile: 9.41 s
Decode latency:
Latency 5th percentile: 0.60 s
Latency 25th percentile: 0.79 s
Latency 50th percentile: 0.93 s
Latency 75th percentile: 2.34 s
Latency 95th percentile: 7.72 s
************************************************************
```
We also store the raw latency distribution files as pickle files in
`./simulation_llama70b/ilp_online`. You can refer to `analyze_latency` in `step3_simulation.py`
if you want to parse and check them.

(11) Run LLaMA 70B in online setup using Swarm and observe its decode throughput, prompt latency
and decode latency. The decode throughput corresponds to Figure 7(b)'s online - Swarm; the
prompt latency corresponds to Figure 7(e)'s Swarm (S); the decode latency corresponds to Figure
7(f)'s Swarm (S).
```bash
python step3_simulation.py swarm llama70b online
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B online simulation results: Swarm
Total decode throughput: 31.0 tokens/s
Prompt latency:
Latency 5th percentile: 2.11 s
Latency 25th percentile: 3.96 s
Latency 50th percentile: 7.22 s
Latency 75th percentile: 10.71 s
Latency 95th percentile: 14.83 s
Decode latency:
Latency 5th percentile: 0.77 s
Latency 25th percentile: 0.97 s
Latency 50th percentile: 1.23 s
Latency 75th percentile: 2.39 s
Latency 95th percentile: 6.50 s
************************************************************
```
We also store the raw latency distribution files as pickle files in
`./simulation_llama70b/swarm_online`. You can refer to `analyze_latency` in `step3_simulation.py`
if you want to parse and check them.

(12) Run LLaMA 70B in online setup using Separate Pipelines and observe its decode throughput,
prompt latency and decode latency. The decode throughput corresponds to Figure 7(b)'s online -
Separate Pipelines (SP); the prompt latency corresponds to Figure 7(e)'s Separate Pipelines (SP);
the decode latency corresponds to Figure 7(f)'s Separate Pipelines (SP).
```bash
python step3_simulation.py separate llama70b online
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B online simulation results: Separate
Total decode throughput: 33.6 tokens/s
Prompt latency:
Latency 5th percentile: 1.27 s
Latency 25th percentile: 2.20 s
Latency 50th percentile: 4.96 s
Latency 75th percentile: 6.02 s
Latency 95th percentile: 15.82 s
Decode latency:
Latency 5th percentile: 0.71 s
Latency 25th percentile: 0.97 s
Latency 50th percentile: 1.20 s
Latency 75th percentile: 1.37 s
Latency 95th percentile: 5.01 s
************************************************************
```
We also store the raw latency distribution files as pickle files in
`./simulation_llama70b/separate_online`. You can refer to `analyze_latency` in `step3_simulation.py`
if you want to parse and check them.

## Section 6.5 High GPU-Heterogeneity Cluster
All files related to this group of experiments are located in `artifact_evaluation/high_heterogeneity`.
Start from the root directory of the repository:
```bash
cd artifact_evaluation/high_heterogeneity
```
The workflow is similar to the first two groups of experiments.

### Step 1: Generate Cluster Config Files
Run the following command to generate cluster config files:
```bash
python step1_gen_cluster.py
```
This will automatically generate the config file that represents a single cluster with
42 machines (4 1xA100 machines, 6 1xV100 machines, 8 1xL4 machines, 4 2xL4 machines, 10 1xT4 machines,
6 2xT4 machines and 4 4xT4 machines) in `config/cluster42.ini`.

### Step 2: Model Placement

The next step is to generate the model placement for the cluster. Different from the previous
two groups of experiments, we only deploy LLaMA-2 70B in this 42-node cluster. Run the following
commands to generate model placements using different model placement methods.

Notice that before running Helix's MILP-based model placement planner, you need to
**backup and empty** the `./layout_llama70b/ilp` directory,
which currently contains the result we get. If the directory is not empty, you will get
an error from the model placement planner saying that the directory is not empty. After you
have finished evaluating Helix's model placement planner, you can restore the directory
to facilitate the evaluation of later steps.

Also, for `llama70b`, you need to run `swarm` before running Helix's MILP model placement
planner, as we bootstrap the solver with `swarm`'s solution.

> **Notes:** The default limited license for Gurobi has a size limit on the MILP problem. The size
> of the MILP problem for LLaMA 70B on this 42-node cluster exceeds the limit. Gurobi will refuse
> to solve and throw an error: "gurobipy.GurobiError: Model too large for size-limited license;
> visit https://gurobi.com/unrestricted for more information". Note that this is an issue with
> Gurobi **licensing** instead of our system, and we provide our optimization trace in
> `./layout_llama70b/ilp/trace.txt` for you to compare against.

> **Notes:** Running Helix to search for a model placement for LLaMA 70B may take a long time.
> We set the max running time to 10 hours, but you can stop the solver at any time with `ctrl +c`. 
> In our experiments, on a machine with 14 cores and academic license, we manually early-stop
> the solver at round 50 minutes. This solution at this point already has good quality. The
> objective value (Incumbent) equals to 4137.

```bash
# Generate model placement using heuristic method Petals
python step2_gen_layout.py petals
# Generate model placement using heuristic method Swarm
python step2_gen_layout.py swarm
# Generate model placement using heuristic method separate pipelines
python step2_gen_layout.py separate
# Generate model placement using Helix's MILP-based method
python step2_gen_layout.py ilp  # empty ./layout_llama70b/ilp before running
```

After running the commands above, you will get model placement files located in:
+ **petals**: `./layout_llama70b/petals` (`petals_sol.ini` and `simulator_cluster.ini`)
+ **swarm**: `./layout_llama70b/swarm` (`swarm_sol.ini` and `simulator_cluster.ini`)
+ **separate**: `./layout_llama70b/separate` (12 manually created files in 6 directories)
+ **ilp**: `./layout_llama70b/ilp` (`ilp_sol.ini` and `simulator_cluster.ini`, and 4 other files that records information about the MILP problem)

### Step 3: Run Simulation
With the model placement files generated, we can run the simulation and reproduce the results in the
paper.

> **Notes:** Before running simulation, you can restore the `./layout_llama70b/ilp` directory you just backed up.

(1) Run LLaMA 70B in offline setup using Helix and observe its decode throughput. This
corresponds to Figure 8(a)'s offline - Helix in the paper.
```bash
python step3_simulation.py helix offline
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B offline simulation results: Helix
Total decode throughput: 645.6 tokens/s
************************************************************
```
The result here is slightly higher than the result in the paper, because of the slight
difference in the model placement.
    
(2) Run LLaMA 70B in offline setup using Swarm and observe its decode throughput. This
corresponds to Figure 8(a)'s offline - Swarm in the paper.
```bash
python step3_simulation.py swarm offline
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B offline simulation results: Swarm
Total decode throughput: 473.2 tokens/s
************************************************************
```

(3) Run LLaMA 70B in offline setup using Separate Pipelines and observe its decode throughput.
This corresponds to Figure 8(a)'s offline - Separate Pipelines (SP) in the paper.
```bash
python step3_simulation.py separate offline
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B offline simulation results: Separate
Total decode throughput: 219.3 tokens/s
************************************************************
```

(4) Run LLaMA 70B in offline setup using Separate Pipelines Plus and observe its decode throughput.
This corresponds to Figure 8(a)'s offline - Separate Pipelines Plus (SP+) in the paper.
```bash
python step3_simulation.py sp_plus offline
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B offline simulation results: Separate
Total decode throughput: 285.1 tokens/s
************************************************************
```

(5) Run LLaMA 70B in online setup using Helix and observe its decode throughput, prompt latency
and decode latency. The decode throughput corresponds to Figure 8(a)'s online - Helix; the
prompt latency corresponds to Figure 8(b)'s Helix (H); the decode latency corresponds to Figure
8(c)'s Helix (H).
```bash
python step3_simulation.py helix online
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B online simulation results: Helix
Total decode throughput: 459.8 tokens/s
Prompt latency:
Latency 5th percentile: 0.71 s
Latency 25th percentile: 1.20 s
Latency 50th percentile: 2.09 s
Latency 75th percentile: 2.76 s
Latency 95th percentile: 3.51 s
Decode latency:
Latency 5th percentile: 0.36 s
Latency 25th percentile: 0.51 s
Latency 50th percentile: 0.73 s
Latency 75th percentile: 1.22 s
Latency 95th percentile: 2.18 s
************************************************************
```
We also store the raw latency distribution files as pickle files in
`./simulation_llama70b/ilp_online`. You can refer to `analyze_latency` in `step3_simulation.py`
if you want to parse and check them.

(6) Run LLaMA 70B in online setup using Swarm and observe its decode throughput, prompt latency
and decode latency. The decode throughput corresponds to Figure 8(a)'s online - Swarm; the
prompt latency corresponds to Figure 8(b)'s Swarm (S); the decode latency corresponds to Figure
8(c)'s Swarm (S).
```bash
python step3_simulation.py swarm online
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B online simulation results: Swarm
Total decode throughput: 309.6 tokens/s
Prompt latency:
Latency 5th percentile: 0.93 s
Latency 25th percentile: 1.48 s
Latency 50th percentile: 2.70 s
Latency 75th percentile: 3.21 s
Latency 95th percentile: 4.10 s
Decode latency:
Latency 5th percentile: 0.42 s
Latency 25th percentile: 0.51 s
Latency 50th percentile: 0.77 s
Latency 75th percentile: 1.19 s
Latency 95th percentile: 1.74 s
************************************************************
```
We also store the raw latency distribution files as pickle files in
`./simulation_llama70b/swarm_online`. You can refer to `analyze_latency` in `step3_simulation.py`
if you want to parse and check them.

(7) Run LLaMA 70B in online setup using Separate Pipelines and observe its decode throughput,
prompt latency and decode latency. The decode throughput corresponds to Figure 8(a)'s online -
Separate Pipelines (SP); the prompt latency corresponds to Figure 8(b)'s Separate Pipelines (SP);
the decode latency corresponds to Figure 8(c)'s Separate Pipelines (SP).
```bash
python step3_simulation.py separate online
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B online simulation results: Separate
Total decode throughput: 140.2 tokens/s
Prompt latency:
Latency 5th percentile: 0.55 s
Latency 25th percentile: 0.99 s
Latency 50th percentile: 2.21 s
Latency 75th percentile: 2.73 s
Latency 95th percentile: 3.78 s
Decode latency:
Latency 5th percentile: 0.27 s
Latency 25th percentile: 0.44 s
Latency 50th percentile: 0.47 s
Latency 75th percentile: 0.76 s
Latency 95th percentile: 2.49 s
************************************************************
```
We also store the raw latency distribution files as pickle files in
`./simulation_llama70b/separate_online`. You can refer to `analyze_latency` in `step3_simulation.py`
if you want to parse and check them.

(8) Run LLaMA 70B in online setup using Separate Pipelines Plus and observe its decode throughput,
prompt latency and decode latency. The decode throughput corresponds to Figure 8(a)'s online -
Separate Pipelines Plus (SP+); the prompt latency corresponds to Figure 8(b)'s Separate Pipelines Plus (SP+);
the decode latency corresponds to Figure 8(c)'s Separate Pipelines Plus (SP+).
```bash
python step3_simulation.py sp_plus online
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B online simulation results: Separate
Total decode throughput: 181.3 tokens/s
Prompt latency:
Latency 5th percentile: 0.56 s
Latency 25th percentile: 1.04 s
Latency 50th percentile: 2.22 s
Latency 75th percentile: 3.13 s
Latency 95th percentile: 4.20 s
Decode latency:
Latency 5th percentile: 0.29 s
Latency 25th percentile: 0.44 s
Latency 50th percentile: 0.57 s
Latency 75th percentile: 0.83 s
Latency 95th percentile: 2.62 s
************************************************************
```
We also store the raw latency distribution files as pickle files in
`./simulation_llama70b/sp_plus_online`. You can refer to `analyze_latency` in `step3_simulation.py`
if you want to parse and check them.

## Section 6.6 Model Placement Deep Dive
All files related to this group of experiments are located in `artifact_evaluation/model_placement`.
Start from the root directory of the repository:
```bash
cd artifact_evaluation/model_placement
```
This section performs the ablation of different model placement method. We will show steps to reproduce
the decode throughput shown in Figure 9(a) in the paper. To start with, we have copied the model
placements to `./layout_single` and `./layout_distributed` (Generated previously in Sec 6.3 and 6.4).
We have also copied the config files to `./config_single` and `./config_distributed`.

### Setup 1: LLaMA 70B Single Cluster (Real System)

#### Model Placement Visualization

First, let's visualize the model placements found by different methods in the single cluster setup.
This corresponds to Figure 9(b) in the paper. Run the following command:
```bash
python setup1_visualization.py helix   # visualize Helix's model placement
python setup1_visualization.py swarm   # visualize Swarm's model placement
python setup1_visualization.py petals  # visualize Petals' model placement
```
The files are store in `./visualization`. Notice that the visualization of Helix's model placement
looks slightly different from the one shown in the paper, because of the slight difference in model
placement found by the solver. Despite the difference, Helix's model placement has higher
GPU utilization (red indicates high utilization), which verifies our claim in the paper.

#### Decode Throughput

(1) First, let's see how the model placement of Helix performs. Run the following command
to generate the real system configuration file on the host machine:
```bash
python setup1_gen_sys_config.py helix
```

Then, on two separate terminals of the host machine, run the following command to start
the real system:
```bash
python setup1_start_host.py helix               # on the host machine, terminal 1
python remote_run.py "setup1_start_worker.py"   # on the host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_sys_results/helix`.

Parse the results with the following command on the host machine:
```bash
python setup1_parse_results.py helix
```

You will see a log like the following:
```
./real_sys_results/helix/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 1.00 s
Latency 25th percentile: 1.79 s
Latency 50th percentile: 3.21 s
Latency 75th percentile: 4.15 s
Latency 95th percentile: 5.62 s
Decode latency:
Latency 5th percentile: 0.69 s
Latency 25th percentile: 0.98 s
Latency 50th percentile: 1.34 s
Latency 75th percentile: 2.20 s
Latency 95th percentile: 3.72 s
Summary:
Avg prompt latency: 3.143s
Avg decode latency: 1.701s
Throughput: 230.8 Tokens/s
```
This corresponds to Figure 9(a)'s Single - Helix in the paper.

(2) Next, let's see how the model placement of Swarm performs. Run the following command
to generate the real system configuration file on the host machine:
```bash
python setup1_gen_sys_config.py swarm
```

Then, on two separate terminals of the host machine, run the following command to start the real system:
```bash
python setup1_start_host.py swarm               # on the host machine, terminal 1
python remote_run.py "setup1_start_worker.py"   # on the host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_sys_results/swarm`.

Parse the results with the following command on the host machine:
```bash
python setup1_parse_results.py swarm
```

You will see a log like the following:
```
./real_sys_results/swarm/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 1.37 s
Latency 25th percentile: 1.88 s
Latency 50th percentile: 3.95 s
Latency 75th percentile: 4.67 s
Latency 95th percentile: 5.91 s
Decode latency:
Latency 5th percentile: 0.71 s
Latency 25th percentile: 0.96 s
Latency 50th percentile: 1.57 s
Latency 75th percentile: 2.44 s
Latency 95th percentile: 4.76 s
Summary:
Avg prompt latency: 3.533s
Avg decode latency: 2.035s
Throughput: 109.4 Tokens/s
```
This corresponds to Figure 9(a)'s Single - Swarm in the paper.

(3) Next, let's see how the model placement of Petals performs. Run the following command
to generate the real system configuration file on the host machine:
```bash
python setup1_gen_sys_config.py petals
```

Then, on two separate terminals of the host machine, run the following command to start the real system:
```bash
python setup1_start_host.py petals                # on the host machine, terminal 1
python remote_run.py "setup1_start_worker.py"     # on the host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_sys_results/petals`.

Parse the results with the following command on the host machine:
```bash
python setup1_parse_results.py petals
```

You will see a log like the following:
```
./real_sys_results/petals/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.68 s
Latency 25th percentile: 1.17 s
Latency 50th percentile: 2.44 s
Latency 75th percentile: 2.89 s
Latency 95th percentile: 3.32 s
Decode latency:
Latency 5th percentile: 0.56 s
Latency 25th percentile: 0.68 s
Latency 50th percentile: 0.84 s
Latency 75th percentile: 1.16 s
Latency 95th percentile: 2.51 s
Summary:
Avg prompt latency: 2.105s
Avg decode latency: 1.062s
Throughput: 194.5 Tokens/s
```
This corresponds to Figure 9(a)'s Single - Petals in the paper.

### Setup 2: LLaMA 70B Distributed Clusters (Simulation)
(1) Run LLaMA 70B in offline setup using Helix's model placement and observe its decode throughput.
This corresponds to Figure 9(a)'s Distributed - Helix in the paper.
```bash
python setup2_distributed.py helix
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa30B offline simulation results: Swarm
Total decode throughput: 98.0 tokens/s
************************************************************
```

(2) Run LLaMA 70B in offline setup using Swarm's model placement and observe its decode throughput.
This corresponds to Figure 9(a)'s Distributed - Swarm in the paper.
```bash
python setup2_distributed.py swarm
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B offline simulation results: Swarm
Total decode throughput: 41.6 tokens/s
************************************************************
```

(3) Run LLaMA 70B in offline setup using Petals' model placement and observe its decode throughput.
This corresponds to Figure 9(a)'s Distributed - Petals in the paper.
```bash
python setup2_distributed.py petals
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B offline simulation results: Petals
Total decode throughput: 66.6 tokens/s
************************************************************
```

## Section 6.7 Request Scheduling
All files related to this group of experiments are located in `artifact_evaluation/request_scheduling`.
Start from the root directory of the repository:
```bash
cd artifact_evaluation/request_scheduling
```
This section performs the ablation of different request scheduling methods. We will show steps to
reproduce the decode throughput shown in Figure 10(a) in the paper. To start with, we have copied
the model placements used in the paper to `./layout_single` and `./layout_distributed`. We have also
copied the config files to `./config_single` and `./config_distributed`.

### Setup 1: LLaMA 70B Single Cluster (Real System)

First, let's generate the real system config file:
```bash
python setup1_gen_sys_config.py
```
Then, we evaluate the performance of different request scheduling methods in the real system.

(1) Helix's Request Scheduling. Run the following command on two separate terminals of the
host machine to start the real system:
```bash
python setup1_start_host.py helix                       # on the host machine, terminal 1
python remote_run.py "setup1_start_worker.py maxflow"   # on the host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_sys_results/helix`.

Parse the results with the following command on the host machine:
```bash
python setup1_parse_results.py helix
```

You will see a log like the following:
```
./real_sys_results/helix/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.93 s
Latency 25th percentile: 2.12 s
Latency 50th percentile: 3.55 s
Latency 75th percentile: 4.35 s
Latency 95th percentile: 5.46 s
Decode latency:
Latency 5th percentile: 0.70 s
Latency 25th percentile: 1.02 s
Latency 50th percentile: 1.47 s
Latency 75th percentile: 2.41 s
Latency 95th percentile: 3.99 s
Summary:
Avg prompt latency: 3.315s
Avg decode latency: 1.839s
Throughput: 214.1 Tokens/s
```
This corresponds to Figure 10(a)'s Single - Helix in the paper.

(2) Swarm's Request Scheduling. Run the following command on two separate terminals of the
host machine to start the real system:
```bash
python setup1_start_host.py swarm                     # on the host machine, terminal 1
python remote_run.py "setup1_start_worker.py swarm"   # on the host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_sys_results/swarm`.

Parse the results with the following command on the host machine:
```bash
python setup1_parse_results.py swarm
```

You will see a log like the following:
```
./real_sys_results/swarm/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.77 s
Latency 25th percentile: 1.49 s
Latency 50th percentile: 2.87 s
Latency 75th percentile: 3.66 s
Latency 95th percentile: 4.45 s
Decode latency:
Latency 5th percentile: 0.58 s
Latency 25th percentile: 0.80 s
Latency 50th percentile: 1.04 s
Latency 75th percentile: 1.79 s
Latency 95th percentile: 3.30 s
Summary:
Avg prompt latency: 2.630s
Avg decode latency: 1.413s
Throughput: 169.4 Tokens/s
```

This corresponds to Figure 10(a)'s Single - Swarm in the paper.

(3) Random Request Scheduling. Run the following command on two separate terminals of the
host machine to start the real system:
```bash
python setup1_start_host.py random                      # on the host machine, terminal 1
python remote_run.py "setup1_start_worker.py random"    # on the host machine, terminal 2
```

After running the experiment, the log files are stored in `./real_sys_results/random`.

Parse the results with the following command on the host machine:
```bash
python setup1_parse_results.py random
```

You will see a log like the following:
```
./real_sys_results/random/events.txt (excluding first 60s as warm up)
Prompt latency:
Latency 5th percentile: 0.89 s
Latency 25th percentile: 1.44 s
Latency 50th percentile: 2.85 s
Latency 75th percentile: 3.65 s
Latency 95th percentile: 4.82 s
Decode latency:
Latency 5th percentile: 0.59 s
Latency 25th percentile: 0.80 s
Latency 50th percentile: 1.04 s
Latency 75th percentile: 1.77 s
Latency 95th percentile: 3.15 s
Summary:
Avg prompt latency: 2.667s
Avg decode latency: 1.402s
Throughput: 169.5 Tokens/s
```

This corresponds to Figure 10(a)'s Single - Random in the paper.

### Setup 2: LLaMA 70B Distributed Clusters (Simulation)
We will show the decode throughput of different request scheduling methods (correspond to
Figure 10 (a)) and the congestion of Swarm and Random scheduling (correspond to Figure 10 (b)).

(1) Run LLaMA 70B in offline setup using Helix's model placement and Helix's request scheduling,
and observe its decode throughput. This corresponds to Figure 10(a)'s Distributed - Helix in the paper.
```bash
python setup2_distributed.py helix
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
LLaMa70B offline simulation results: Helix
Total decode throughput: 99.8 tokens/s
************************************************************
```

(2) Run LLaMA 70B in offline setup using Helix's model placement and Swarm's request scheduling,
and observe its decode throughput. This corresponds to Figure 10(a)'s Distributed - Swarm in the paper.
```bash
python setup2_distributed.py swarm
```
After running the simulation, you will first see a log like the following at the end:
```
************************************************************
Congestion analysis: SchedulingMethod.Swarm
RequestLocation.ComputeNode-13: 10.642573522737315s
RequestLocation.ComputeNode-16: 0.2297687153968934s
RequestLocation.ComputeNode-17: 0.1375851532262901s
RequestLocation.ComputeNode-23: 0.24706526547356375s
RequestLocation.ComputeNode-8: 0.20593923281874615s
RequestLocation.ComputeNode-6: 0.2264234774325119s
RequestLocation.ComputeNode-7: 0.2004372137780166s
RequestLocation.ComputeNode-10: 0.053729825948366346s
RequestLocation.ComputeNode-15: 6.010935175942984s
RequestLocation.ComputeNode-5: 0.07598068956073936s
RequestLocation.ComputeNode-4: 0.07319502782480897s
RequestLocation.ComputeNode-2: 0.07416888513400685s
RequestLocation.ComputeNode-3: 0.06961344295568916s
RequestLocation.ComputeNode-21: 0.03798450119303149s
RequestLocation.ComputeNode-24: 18.768433269215418s
RequestLocation.ComputeNode-12: 0.654829423289039s
RequestLocation.ComputeNode-22: 0.8254657527797614s
RequestLocation.ComputeNode-9: 0.3024842419124777s
RequestLocation.ComputeNode-19: 0.3019372612291324s
RequestLocation.ComputeNode-18: 0.2484524768867684s
RequestLocation.ComputeNode-20: 0.24794287992468222s
************************************************************
```
Notice the high latency on compute node 13, 15 and 24. This indicates the congestion problem
of Swarm's request scheduling method, as shown in Figure 10(b). Then, you will see a log like
the following about the decode throughput:
```
************************************************************
LLaMa70B offline simulation results: Swarm
Total decode throughput: 81.7 tokens/s
************************************************************
```

(3) Run LLaMA 70B in offline setup using Helix's model placement and random request scheduling,
and observe its decode throughput. This corresponds to Figure 10(a)'s Distributed - Random in the paper.
```bash
python setup2_distributed.py random
```
After running the simulation, you will first see a log like the following at the end:
```
************************************************************
Congestion analysis: SchedulingMethod.Naive
RequestLocation.ComputeNode-21: 0.03731661155205453s
RequestLocation.ComputeNode-18: 0.2610173190834541s
RequestLocation.ComputeNode-20: 0.24644899878499654s
RequestLocation.ComputeNode-24: 17.50800780761662s
RequestLocation.ComputeNode-12: 0.6503202400672451s
RequestLocation.ComputeNode-22: 0.7808302135408729s
RequestLocation.ComputeNode-7: 0.20322868913110503s
RequestLocation.ComputeNode-10: 0.05172704352740775s
RequestLocation.ComputeNode-15: 6.482867120339014s
RequestLocation.ComputeNode-5: 0.0725252025756106s
RequestLocation.ComputeNode-4: 0.06983009459878285s
RequestLocation.ComputeNode-2: 0.07228054807078026s
RequestLocation.ComputeNode-3: 0.06768848447426572s
RequestLocation.ComputeNode-13: 15.116493481300573s
RequestLocation.ComputeNode-16: 0.2195493719334298s
RequestLocation.ComputeNode-17: 0.1335675991842193s
RequestLocation.ComputeNode-23: 0.24360117246674284s
RequestLocation.ComputeNode-8: 0.22089513731045193s
RequestLocation.ComputeNode-6: 0.24069865307333366s
RequestLocation.ComputeNode-9: 0.20313929011251647s
RequestLocation.ComputeNode-19: 0.220904070127803s
************************************************************

```
Notice the high latency on compute node 13, 15 and 24 (`SchedulingMethod.Naive` here is random
scheduling). This indicates the congestion problem of random request scheduling method, as shown
in Figure 10(b). Then, you will see a log like the following about the decode throughput:
```
************************************************************
LLaMa70B offline simulation results: Random
Total decode throughput: 87.4 tokens/s
************************************************************
```

(4) Run LLaMA 70B in offline setup using Helix's model placement and shortest queue request
scheduling, and observe its decode throughput. This corresponds to Figure 10(a)'s Distributed - Shortest Queue (SQ) in the paper.
```bash
python setup2_distributed.py shortest_queue
```
After running the simulation, you will see a log like the following at the end:
```
************************************************************
Congestion analysis: SchedulingMethod.ShortestQueue
RequestLocation.ComputeNode-21: 0.040311610792162444s
RequestLocation.ComputeNode-16: 0.20583538196320073s
RequestLocation.ComputeNode-17: 0.13331778900517946s
RequestLocation.ComputeNode-23: 0.2334643636195339s
RequestLocation.ComputeNode-24: 19.255628614498356s
RequestLocation.ComputeNode-12: 0.7354160220899202s
RequestLocation.ComputeNode-22: 0.9397185835397719s
RequestLocation.ComputeNode-7: 0.20336656540062908s
RequestLocation.ComputeNode-10: 0.053327423445625584s
RequestLocation.ComputeNode-15: 7.683681647206574s
RequestLocation.ComputeNode-5: 0.07468962344948517s
RequestLocation.ComputeNode-4: 0.07110484214818696s
RequestLocation.ComputeNode-2: 0.07317778688264566s
RequestLocation.ComputeNode-3: 0.06784204492750039s
RequestLocation.ComputeNode-13: 14.240169586787173s
RequestLocation.ComputeNode-8: 0.20676437891454677s
RequestLocation.ComputeNode-6: 0.21431887796231158s
RequestLocation.ComputeNode-9: 0.2256070874191855s
RequestLocation.ComputeNode-19: 0.2475273211902834s
RequestLocation.ComputeNode-18: 0.25391846234740756s
RequestLocation.ComputeNode-20: 0.2537499534902388s
************************************************************
```
Notice the high latency on compute node 13, 15 and 24. This indicates the congestion problem
of shortest queue request scheduling method, as shown in Figure 10(b). Then, you will see a log like
the following about the decode throughput:
```
************************************************************
LLaMa70B offline simulation results: ShortestQueue
Total decode throughput: 83.6 tokens/s
************************************************************
```

## Section 6.8 Ablation Study on Optimization
In this section, we reproduce the results for ablation study about cluster pruning and initial
values. All files related to this group of experiments are located in `artifact_evaluation/ablation`.
Start from the root directory of the repository:
```bash
cd artifact_evaluation/ablation
```
We have already placed the cluster config files in `./config`.

> **Note:** Before running the experiments below, please first backup and empty `./layouts`.

### Ablation on Cluster Pruning
Previously in reproducing Section 6.4 and 6.5, we have already shown the results when cluster
pruning is enabled, which corresponds to the `w/ prune` results in Figure 11(a). In the figure,
`24-node` corresponds to the setup in Section 6.4, and `42-node` corresponds to the setup in
Section 6.5. You can also get the problem size from the optimization log you got when running
those experiments (corresponds to Table 8 - With Pruning). Now, we will show the performance
without cluster pruning, which corresponds to the `w/o prune` results in Figure 11(a).

> **Note:** Because of Gurobi licensing issues, the results you get might be different from
> ours (especially if you are using limited license). This is an issue with the Gurobi solver
> instead of our system.

(1) First, let's disable cluster pruning and run Helix's model placement planner for the 24
node cluster. Run the following command to generate model placement with Helix:

```bash
python ablation1_pruning.py layout 24
```

You will first see a line like this in the Gurobi output, which corresponds to 24-node without
pruning in Table 8:

```
Optimize a model with 1848 rows, 1376 columns and 13960 nonzeros
```

We terminate the solving process at around 45 minutes and save the optimization trace in
`./layouts/no_prune_24/trace.txt`. Then, we run the simulation:

```bash
python ablation1_pruning.py simulate 24
```

After running the simulation, you will see a log like the following at the end. This
corresponds to Figure 11 (a) - 24-node w/o prune in the paper:
```
************************************************************
Decode throughput for 24-node cluster: 74.92333333333333 (w/o pruning)
************************************************************
```

(2) Next, let's disable cluster pruning for the 42 node cluster. Run the following command to
generate model placement with Helix:

```bash
python ablation1_pruning.py layout 42
```

You will first see a line like this in the Gurobi output, which corresponds to 42-node without
pruning in Table 8:

```
Optimize a model with 5502 rows, 4004 columns and 49546 nonzeros
```

We terminate the solving process at around 75 minutes and save the optimization trace in
`./layouts/no_prune_42/trace.txt`. Then, we run the simulation:

```bash
python ablation1_pruning.py simulate 42
```

After running the simulation, you will see a log like the following at the end. This
corresponds to Figure 11 (a) - 42-node w/o prune in the paper:
```
************************************************************
Decode throughput for 42-node cluster: 574.2383333333333 (w/o pruning)
************************************************************
```

### Ablation on Initial Values

In this part, we show the results of ablation study on initial values. Previously in reproducing
Section 6.4 and 6.5, we have already shown the results when using initial values, which corresponds
to the `heuristic` results in Figure 11(b). Now, we will show the optimizer running time without
initial values, which corresponds to the `raw` results in Figure 11(b).

For the 24 node and 42 node cluster, run:

```bash
python ablation2_initial.py 24   # no initial values for 24 node cluster
python ablation2_initial.py 42   # no initial values for 42 node cluster
```

The two commands will generate the model placements and save them to `./layouts/raw_24`
and `./layouts/raw_42`. For the 24-node cluster, on our side it takes around 85 minutes to find
the model placement with same objective value as the one found in Sec 6.4. For the 42-node
cluster, on our side it takes around 50 minutes to find the model placement with same objective value
as the one found in Sec 6.5. Both are longer than the time needed when starting from heuristic
solutions. This matches our result in the paper. We provide the traces in `./layouts/raw_24/trace.txt`
and `./layouts/raw_42/trace.txt`. 

> **Note:** Because of the difference of Gurobi license and hardware, the running time you get might
> be different from ours. This is an issue with the Gurobi solver instead of our system.

### Model Placement Quality (Section 6.9)

This experiment studies the optimality of Helix's model placement planner on a small cluster that
can be solved optimally. To produce the trace we use to plot Figure 12, run the following command:

```bash
python ablation3_quality.py
```

We save the trace we get after running this command in `./layouts/quality/trace.txt`. This trace
matches the trend in Figure 12.

> **Note:** Because of the difference of Gurobi license and hardware, the trace you get might
> be different from ours. This is an issue with the Gurobi solver instead of our system.
