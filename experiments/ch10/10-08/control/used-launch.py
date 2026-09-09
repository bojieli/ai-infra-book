"""Bootstrap a private pinned-Ray cluster; run unchanged verl main_ppo entry."""
import os,pathlib,json,sys,socket,shutil
r=pathlib.Path(os.environ['VERLRL_ROOT']);p=pathlib.Path(os.environ['VERLRL_PRIVATE']);out=r/os.environ['VERLRL_RUN']
mode=os.environ.get('VERLRL_MODE','main')
if mode not in ('main','control'):raise ValueError('VERLRL_MODE must be main or control')
args=[
'trainer.use_v1=false','transfer_queue.enable=false',
'data.train_files='+str(r/'train.parquet'),'data.val_files='+str(r/'val.parquet'),
'data.train_batch_size=4','data.max_prompt_length=128','data.max_response_length=16','data.shuffle=false','data.seed=42','data.dataloader_num_workers=0',
'actor_rollout_ref.model.path='+str(p/'model'),'actor_rollout_ref.model.use_remove_padding=false','+actor_rollout_ref.model.override_config.attn_implementation=sdpa',
'actor_rollout_ref.actor.strategy=fsdp','actor_rollout_ref.actor.fsdp_config.use_orig_params=true','actor_rollout_ref.actor.fsdp_config.model_dtype=fp32','actor_rollout_ref.actor.ppo_mini_batch_size=4','actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=1','actor_rollout_ref.actor.ppo_epochs=1','actor_rollout_ref.actor.optim.lr=1e-5','actor_rollout_ref.actor.use_kl_loss=false','actor_rollout_ref.actor.entropy_coeff=0',
'actor_rollout_ref.rollout.name=vllm','actor_rollout_ref.rollout.tensor_model_parallel_size=1','actor_rollout_ref.rollout.gpu_memory_utilization=0.035','actor_rollout_ref.rollout.enforce_eager=true','actor_rollout_ref.rollout.free_cache_engine=true','actor_rollout_ref.rollout.load_format=safetensors','actor_rollout_ref.rollout.n=2','actor_rollout_ref.rollout.temperature=1.0','actor_rollout_ref.rollout.top_p=1.0','actor_rollout_ref.rollout.top_k=-1','actor_rollout_ref.rollout.seed=42','actor_rollout_ref.rollout.max_model_len=144','actor_rollout_ref.rollout.max_num_batched_tokens=144','actor_rollout_ref.rollout.max_num_seqs=8','actor_rollout_ref.rollout.agent.num_workers=1','actor_rollout_ref.rollout.checkpoint_engine.update_weights_bucket_megabytes=32','actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu=1',
'actor_rollout_ref.rollout.val_kwargs.n=1','actor_rollout_ref.rollout.val_kwargs.do_sample=true','actor_rollout_ref.rollout.val_kwargs.temperature=1.0',
'reward.num_workers=1','reward.custom_reward_function.path='+str(r/'reward.py'),'reward.custom_reward_function.name=compute_score',
'algorithm.adv_estimator=grpo','algorithm.use_kl_in_reward=false','trainer.n_gpus_per_node=1','trainer.nnodes=1','trainer.total_training_steps=2','trainer.total_epochs=1','trainer.logger=[console]','trainer.val_before_train=false','trainer.test_freq=2','trainer.save_freq=-1','trainer.resume_mode=disable','trainer.default_local_dir='+str(out/'checkpoints'),'trainer.rollout_data_dir='+str(out/'rollouts'),'trainer.validation_data_dir='+str(out/'validation'),
'+ray_kwargs.ray_init.address=155.103.252.95:6398','ray_kwargs.ray_init.runtime_env.py_executable='+str(p/'verl-project-verl-d040717/.venv/bin/python'),
'hydra.run.dir='+str(out/'hydra')]
if mode=='control':
 args=[x.replace('algorithm.adv_estimator=grpo','algorithm.adv_estimator=reinforce_plus_plus').replace('reward.custom_reward_function.name=compute_score','reward.custom_reward_function.name=compute_control_score') for x in args]
(out/'mode.json').write_text(json.dumps(dict(mode=mode,independent_pretrained_restart=True),indent=2)+'\n')
(out/'overrides.json').write_text(json.dumps(args,indent=2)+'\n')
for name in ['launch.py','run.sh','watchdog.py','observe.py','reward.py','PROTOCOL.md']:
 shutil.copy2(r/name,out/('used-'+name))
with socket.socket() as guard:
 guard.bind(('155.103.252.95',6398))
# RayParams session_name avoids Linux UNIX socket path-length overflow in the authorized deep directory.
# This controls only private cluster startup, no scheduler/training replacements.
from ray._private.parameter import RayParams
from ray._private.node import Node
params=RayParams(node_ip_address='155.103.252.95',gcs_server_port=6398,num_cpus=4,num_gpus=1,include_dashboard=False,object_store_memory=134217728,memory=20*2**30,temp_dir=str(p/'r'),session_name=os.environ['VERLRL_RUN'],min_worker_port=16400,max_worker_port=16499,ray_client_server_port=None)
node=Node(params,head=True,shutdown_at_exit=True,spawn_reaper=True)
(out/'ray-identity.json').write_text(json.dumps(dict(address='155.103.252.95:6398',session=node.session_name,temp_dir=node.temp_dir,session_dir=node.get_session_dir_path(),driver_pid=os.getpid()),indent=2)+'\n')
try:
 sys.argv=['verl.trainer.main_ppo',*args]
 from verl.trainer.main_ppo import main
 main()
finally:
 node.kill_all_processes(check_alive=False,allow_graceful=True)
