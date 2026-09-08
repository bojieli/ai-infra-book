# To run PolyRL training pipeline

## To launch the training process

Below is a step-by-step guide to launch an example training pipeline.

- Algorithm: GRPO
- Model: Qwen3-1.7B
- Dataset: OpenR1-Math-220k
- Train: veRL
- Rollout: SGLang

### Configure the rollout manager

The default configuration of the rollout manager is in [`rollout-manager/config.toml`](rollout-manager/config.toml). You can modify it to fit your needs.

Update the `allowed_sender_ips` to the range of network interfaces that you want to use for weight transfer.

> For example, if you want to use the subnet network interfaces `192.168.0.1` and `192.168.0.2` for weight transfer, you can set the `allowed_sender_ips` to `192.168.0.0/16`.

To maximize the bandwidth utilization, update the `num_mooncake_groups_per_sender` and `num_mooncake_engines_per_group`. A sender can have multiple groups, and each group will shard the model weight to `num_mooncake_engines_per_group` pieces and transfer them in parallel.

> For example, if the manager detect 2 network interfaces for weight transfer, you can specify `num_mooncake_groups_per_sender` to 2 and `num_mooncake_engines_per_group` to 8, then there will be 4 groups and each group will transfer 8 pieces of the model weight in parallel. 

> It is recommend the total number of groups equals to the max number of rollout instances you want to harvest. If you launched 5 rollout instances, the 5th rollout instance will be assigned to the 1st group (Round-robin).

### Data Preparation

Download `OpenR1-Math-220k` dataset,
```
python examples/data_preprocess/openr1.py --local_dir "~/data/openr1"
```

### Launch an RL trainer

PolyRL will automatically compile and launch the rollout manager on the **RANK_ZERO** of the trainer. 

The default port of the rollout manager is `5000` and it will use the configurations in [`rollout-manager/config.toml`](rollout-manager/config.toml). Refer to [rollout.yaml](rlboost/verl_stream/trainer/config/rollout/rollout.yaml) to see how it is defined.

If you want to change rollout manager port or path to the config file, you can specify via
```bash
PYTHONUNBUFFERED=1 python3 -m rlboost.verl_stream.trainer.main_stream \
 ... # Other training parameters
 actor_rollout_ref.rollout.rollout_manager.port="<PORT>" \
 actor_rollout_ref.rollout.rollout_manager.config_path="<PATH_TO_CONFIG_FILE>" \
 ...
```

### Launch a rollout instance.

Update the address in `launch_sglang.sh` 
```bash
ROLLOUT_MANAGER_ADDR="http://<ROLLOUT_MANAGER_IP>:<PORT>" # Address of the head node of trainer
```

On each remote rollout engine, launch
```bash
bash examples/scripts/launch_sglang.sh
```

The script assumes each rollout engine is an independent instance. If you want to launch multiple rollout instances on the same machine, please update the `port` and `transfer-agent-handshake-port` in the script to different values.

> **Note**: The gap between `transfer-agent-handshake-port` should be big enough to avoid port conflicts.

For example, on the second rollout engine, you may run the following command:
```bash
python -m sglang.launch_server \
    ...
    --port 40001 \
    --transfer-agent-handshake-port 21000 \
    ...
```

## To run the colocated RL baseline

Launch a veRL training process with the same configuration

```bash
bash examples/scripts/run_sync_grpo_default.sh
```

# Known Issue

- Remember to clear up `/dev/shm/verl*` if you keep encountering OOM error. 
