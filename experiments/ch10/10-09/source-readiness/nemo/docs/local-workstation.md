# Run on Your Local Workstation

When launching examples locally with `uv`, {py:class}`init_ray() <nemo_rl.distributed.virtual_cluster.init_ray>` will first attempt to connect to an existing cluster. If none is found, it will start a local one and connect to it using all available GPU and CPU resources on your node.

To launch a job outside of a container, simply run:

```sh
uv run examples/run_grpo.py
```

In the logs, you will see that Ray has started a local cluster instance, along with details on the resources made available to it:
```
2025-03-17 13:37:45,360 INFO worker.py:1841 -- Started a local Ray instance.
...
INFO:nemo_rl.distributed.virtual_cluster:Started local cluster with: {'node:__internal_head__': 1.0, 'CPU': 24.0, 'object_store_memory': 80448493977.0, 'accelerator_type:RTX': 1.0, 'memory': 177713152615.0, 'GPU': 1.0, 'node:10.0.0.1': 1.0}
```

To have more precise control over the GPUs Ray uses locally, please use `CUDA_VISIBLE_DEVICES`:

```sh
# Use the 0th and 3rd indexed GPU (for a total of 2 GPUs)
CUDA_VISIBLE_DEVICES=0,3 uv run examples/run_grpo.py
```

We also allow multiple colocated local clusters, which are uniquely identified by the values in
`CUDA_VISIBLE_DEVICES`. Concretely:

```sh
# (1) Start a fresh cluster on GPU=0
CUDA_VISIBLE_DEVICES=0 uv run examples/run_grpo.py

# (2) While (1) is running, this will start a new cluster using GPUs 1 and 2 without interfering with (1)
# Ensure that the CUDA_VISIBLE_DEVICES do not overlap already running jobs.
CUDA_VISIBLE_DEVICES=1,2 uv run examples/run_grpo.py
```
