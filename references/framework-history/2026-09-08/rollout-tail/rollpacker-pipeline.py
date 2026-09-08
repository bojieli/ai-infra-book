import copy
import json
import math
import os
from functools import partial
from typing import Any, Dict, List

import time
import datasets
import ray
import torch
from codetiming import Timer
from ray.util.scheduling_strategies import NodeAffinitySchedulingStrategy
from ray.util.timer import _Timer
from ray.actor import ActorHandle

from roll.datasets.chat_template import get_chat_template
from roll.datasets.collator import DataCollatorWithPaddingForPaddedKeys
from roll.distributed.executor.cluster import Cluster
from roll.distributed.scheduler.generate_scheduler import DynamicSamplingScheduler
from roll.distributed.scheduler.async_generate_scheduler import AsyncDynamicSamplingScheduler
from roll.distributed.scheduler.multi_async_generate_scheduler import MultiAsyncDynamicSamplingScheduler
from roll.distributed.scheduler.protocol import DataProto
from roll.models.model_providers import default_tokenizer_provider
from roll.pipeline.base_pipeline import BasePipeline
from roll.pipeline.rlvr.rlvr_config import RLVRConfig
from roll.utils.functionals import (
    compute_advantage,
    reduce_metrics,
    RunningMoments,
    get_sample_level_mask,
    reward_postprocess,
    compute_token_reward,
    agg_loss,
)
from roll.utils.kl_controller import get_kl_controller
from roll.utils.logging import get_logger
from roll.utils.metrics.metrics_manager import MetricsManager
import asyncio
import threading
from .tracker import GPUTracker


logger = get_logger()


def preprocess_dataset(dataset, prompt_len, encode_function, num_proc):
    # 处理数据
    print(f"Begin : {dataset}")
    dataset = dataset.map(
        encode_function,
        batched=True,
        num_proc=num_proc,
        desc="Encoding dataset",
        load_from_cache_file=False,
    )
    # 过滤cutoff
    dataset = dataset.filter(
        lambda data_i: 5 < len(data_i["input_ids"]) <= prompt_len,
        num_proc=num_proc,
        desc="Filtering dataset",
    )
    print(f"Filtering prompt len: {dataset}")
    print(f"Encoding: {dataset}")
    return dataset


def get_encode_function(template_name, tokenizer):
    chat_template_func = get_chat_template(template_name, tokenizer)

    def encode_function(data_i):
        text_list = []
        if "messages" in data_i:
            for messages in data_i["messages"]:
                if isinstance(messages, str):
                    messages = json.loads(messages)
                text_list.append(chat_template_func(messages))
        elif "prompt" in data_i:
            for prompt in data_i["prompt"]:
                text_list.append(prompt)
        encodings = tokenizer(text_list)
        return encodings

    return encode_function

def update_dataset_domain(tag_2_domain: Dict[str, set[str]], row):
    if 'domain' in row and row['domain'] is not None:
        return row
    row["domain"] = tag_2_domain.get(row["tag"], "math_rule")
    return row

def query_filter_fn(data_list: List[DataProto], config: RLVRConfig) -> bool:
    """
    各domain的过滤规则可以自定义
    """
    response_level_rewards = [data.batch["response_level_rewards"] for data in data_list]
    if len(response_level_rewards) == 1:
        return True
    rewards = torch.cat(response_level_rewards, dim=0)

    domain = data_list[0].non_tensor_batch["domain"][0]
    query_filter_config = config.rewards[domain].query_filter_config

    if query_filter_config.type == "no_filter":
        return True
    elif query_filter_config.type == "mean_filter":
        threshold_up = query_filter_config.filter_args.get("threshold_up", math.inf)
        threshold_down = query_filter_config.filter_args.get("threshold_down", -1)
        if torch.mean(rewards) <= threshold_down or torch.mean(rewards) >= threshold_up:
            return False
    elif query_filter_config.type == "std_filter":
        std_threshold = query_filter_config.filter_args.get("std_threshold", -1)
        if torch.std(rewards) <= std_threshold:
            return False
    return True


def pre_pass_query_filter_fn(data_list: List[DataProto], config: RLVRConfig) -> bool:
    """
    各domain的过滤规则可以自定义
    """
    response_level_rewards = [data.batch["response_level_rewards"] for data in data_list]
    if len(response_level_rewards) == 1:
        return False # differ from query_filter_fn, we cannot ensure anything when only having one example
    rewards = torch.cat(response_level_rewards, dim=0)

    domain = data_list[0].non_tensor_batch["domain"][0]
    query_filter_config = config.rewards[domain].query_filter_config

    if query_filter_config.type == "no_filter":
        return True
    elif query_filter_config.type == "mean_filter":
        threshold_up = query_filter_config.filter_args.get("threshold_up", math.inf)
        threshold_down = query_filter_config.filter_args.get("threshold_down", -1)
        # print('rewards mean {}, return {}'.format(torch.mean(rewards), not (torch.mean(rewards) <= threshold_down or torch.mean(rewards) >= threshold_up)), flush=True)
        return not (torch.mean(rewards) <= threshold_down or torch.mean(rewards) >= threshold_up)
    
    elif query_filter_config.type == "std_filter":
        std_threshold = query_filter_config.filter_args.get("std_threshold", -1)
        if torch.std(rewards) <= std_threshold:
            return False
    return True


def register_autoscaling_ranks(cluster: Cluster, pipeline_config: RLVRConfig): 
    max_dp_rank = max([cluster.get_rank_info(rank=i).dp_rank for i in range(cluster.world_size)]) + 1
    first_half_ranks = [i for i in range(cluster.world_size) if cluster.get_rank_info(rank=i).dp_rank < max_dp_rank // 2]
    second_half_ranks = [i for i in range(cluster.world_size) if cluster.get_rank_info(rank=i).dp_rank >= max_dp_rank // 2]
    pipeline_config.max_dp_rank = max_dp_rank
    pipeline_config.first_half_ranks = first_half_ranks
    pipeline_config.second_half_ranks = second_half_ranks
    # print([self.actor_train.get_rank_info(rank=i) for i in range(self.actor_train.world_size)])
    print([cluster.get_rank_info(rank=i) for i in range(cluster.world_size)])

MULTI_SCHED_NAME='multi_sched'

class RLVRPipelineMegatronAsync(BasePipeline):

    def __init__(self, pipeline_config: RLVRConfig):
        super().__init__(pipeline_config)
        self.pipeline_config = pipeline_config

        self.tokenizer = default_tokenizer_provider(model_args=self.pipeline_config.actor_train.model_args)

        dataset_paths = []
        if self.pipeline_config.actor_train.data_args.file_name:
            dataset_paths.extend(self.pipeline_config.actor_train.data_args.file_name)

        print(f'load_dataset_paths: {chr(10)} {chr(10).join(dataset_paths)}')
        dataset = datasets.load_dataset('json', data_files=dataset_paths)['train']
        if False: 
            from datasets import Dataset
            dataset = Dataset.from_dict(dataset[:256], features=dataset.features)
        
        self.val_dataset = None
        # if self.pipeline_config.validation:
        if self.pipeline_config.validation.data_args:
            val_dataset_paths = self.pipeline_config.validation.data_args.file_name
            self.val_dataset = datasets.load_dataset("json", data_files=val_dataset_paths)["train"]

        # 加上format，然后转ids的func
        template_name = (
            self.pipeline_config.global_template
            if self.pipeline_config.global_template
            else self.pipeline_config.actor_train.data_args.template
        )
        encode_function = get_encode_function(template_name, self.tokenizer)

        dataset = preprocess_dataset(
            dataset,
            self.pipeline_config.prompt_length,
            encode_function,
            num_proc=self.pipeline_config.actor_train.data_args.preprocessing_num_workers,
        )
        # update domain field
        dataset = dataset.map(
            partial(update_dataset_domain, self.pipeline_config.tag_2_domain),
            num_proc=self.pipeline_config.actor_train.data_args.preprocessing_num_workers,
            desc="update_dataset_domain",
            load_from_cache_file=False
        )
        self.domain_datasets: Dict[str, datasets.Dataset] = {}
        for domain in self.pipeline_config.actor_train.data_args.domain_interleave_probs.keys():
            self.domain_datasets[domain] = dataset.filter(
                lambda example, dom: example["domain"] == dom,
                num_proc=self.pipeline_config.actor_train.data_args.preprocessing_num_workers,
                fn_kwargs={"dom": domain},
            )
            print(f"Domain: {domain}, length: {len(self.domain_datasets[domain])}")

            assert len(self.domain_datasets[domain]) > 0, f"domain dataset {domain} has no data"

        if self.val_dataset:
            self.val_dataset = preprocess_dataset(
                self.val_dataset,
                self.pipeline_config.prompt_length,
                encode_function,
                num_proc=self.pipeline_config.actor_train.data_args.preprocessing_num_workers,
            )
            self.val_dataset = self.val_dataset.map(
                partial(update_dataset_domain, self.pipeline_config.tag_2_domain),
                num_proc=self.pipeline_config.actor_train.data_args.preprocessing_num_workers,
                desc="update_val_dataset_domain",
                load_from_cache_file=False
            )

        assert 'domain' in dataset.column_names, "domain field should set in dataset"
        if self.val_dataset:
            assert 'domain' in self.val_dataset.column_names, "domain field should set in val dataset"
        print(dataset)

        self.kl_ctrl = get_kl_controller(
            init_kl_coef=self.pipeline_config.init_kl_coef,
            target_kl=self.pipeline_config.target_kl,
            kl_horizon=self.pipeline_config.kl_horizon,
        )

        assert self.pipeline_config.max_steps > 0, "max_steps must be greater than 0"
        self.pipeline_config.set_max_steps(max_steps=self.pipeline_config.max_steps)

        DEBUG = False 
        if DEBUG:
            self.actor_train = None 
        else: 
            self.actor_train: Any = Cluster(
                name=self.pipeline_config.actor_train.name,
                worker_cls=self.pipeline_config.actor_train.worker_cls,
                resource_manager=self.resource_manager,
                worker_config=self.pipeline_config.actor_train,
            )
        self.actor_infer: Any = Cluster(
            name=self.pipeline_config.actor_infer.name,
            worker_cls=self.pipeline_config.actor_infer.worker_cls,
            resource_manager=self.resource_manager,
            worker_config=self.pipeline_config.actor_infer,
        )

        if self.pipeline_config.multi_infer_tp:
            self.actor_infer_tp = Cluster(
                name=self.pipeline_config.actor_infer_tp.name,
                worker_cls=self.pipeline_config.actor_infer_tp.worker_cls,
                resource_manager=self.resource_manager,
                worker_config=self.pipeline_config.actor_infer_tp,
            )

        self.reference = None
        # if DEBUG: 
        #     self.reference = None
        # else: 
        #     self.reference: Any = Cluster(
        #         name=self.pipeline_config.reference.name,
        #         worker_cls=self.pipeline_config.reference.worker_cls,
        #         resource_manager=self.resource_manager,
        #         worker_config=self.pipeline_config.reference,
        #     )
            
        if self.pipeline_config.adv_estimator == "gae":
            self.critic: Any = Cluster(
                name=self.pipeline_config.critic.name,
                worker_cls=self.pipeline_config.critic.worker_cls,
                resource_manager=self.resource_manager,
                worker_config=self.pipeline_config.critic,
            )
        self.rewards: Dict[str, Any] = {
            key: Cluster(
                name=f"reward-{key}",
                worker_cls=worker_config.worker_cls,
                resource_manager=self.resource_manager,
                worker_config=worker_config,
            )
            for key, worker_config in self.pipeline_config.rewards.items()
        }


        domain_ratios = self.pipeline_config.actor_train.data_args.domain_interleave_probs
        self.generate_schedulers: Dict[str, MultiAsyncDynamicSamplingScheduler] = {}
        self.domain_batch_size = {}
        domain_list = list(domain_ratios.keys())
        accumulated = 0
        assert self.pipeline_config.generate_opt_level in [0, 2], 'we do not optimize the generate scheduler for opt level 1'
        for i, domain in enumerate(domain_list):
            if self.pipeline_config.generate_opt_level not in [0, 1]: continue
            if i == len(domain_list) - 1:
                domain_batch_size = self.pipeline_config.rollout_batch_size - accumulated
            else:
                domain_batch_size = int(domain_ratios[domain] * self.pipeline_config.rollout_batch_size)
            accumulated += domain_batch_size

            if self.pipeline_config.generate_opt_level == 0: 
                raise NotImplementedError("generate_opt_level 0 is not supported in RLVRPipelineAsync")
                generate_scheduler = GenerateScheduler.options(
                    scheduling_strategy=NodeAffinitySchedulingStrategy(
                        node_id=ray.get_runtime_context().get_node_id(),
                        soft=False,
                    )
                ).remote(pipeline_config=self.pipeline_config)
                ray.get(
                    generate_scheduler.set_scheduler.remote(
                        actor_cluster=self.actor_infer,
                        reward_clusters={domain: self.rewards[domain]},
                        dataset=self.domain_datasets[domain],
                        collect_fn_cls=DataCollatorWithPaddingForPaddedKeys,
                        collect_fn_kwargs=dict(max_length=self.pipeline_config.prompt_length, padding="max_length"),
                        response_filter_fn=lambda data_item, config: True,
                        query_filter_fn=query_filter_fn,
                        response_callback_fn=generate_scheduler.report_response.remote,
                        state=self.state.kv.get(f"scheduler_state_{domain}", None),
                    )
                )

            elif self.pipeline_config.generate_opt_level == 1:
                generate_scheduler = AsyncDynamicSamplingScheduler.options(
                # generate_scheduler = DynamicSamplingScheduler.options(
                    scheduling_strategy=NodeAffinitySchedulingStrategy(
                        node_id=ray.get_runtime_context().get_node_id(),
                        soft=False,
                    )
                ).remote(pipeline_config=self.pipeline_config)
                ray.get(
                    generate_scheduler.set_scheduler.remote(
                        actor_cluster=self.actor_infer,
                        reward_clusters={domain: self.rewards[domain]},
                        dataset=self.domain_datasets[domain],
                        collect_fn_cls=DataCollatorWithPaddingForPaddedKeys,
                        collect_fn_kwargs=dict(max_length=self.pipeline_config.prompt_length, padding="max_length"),
                        response_filter_fn=lambda data_item, config: True,
                        query_filter_fn=query_filter_fn,
                        response_callback_fn=generate_scheduler.report_response.remote,
                        state=self.state.kv.get(f"scheduler_state_{domain}", None),
                        pre_pass_query_filter_fn=pre_pass_query_filter_fn,
                        migrate_callback_fn=generate_scheduler.migrate_response.remote,
                    )
                )
            self.generate_schedulers[domain] = generate_scheduler
            self.domain_batch_size[domain] = domain_batch_size

            assert domain_batch_size < len(self.domain_datasets[domain]), (f"domain_batch_size {domain_batch_size} must be "
                                                                           f"less than the number of domain datasets {len(self.domain_datasets[domain])}")

        if self.pipeline_config.generate_opt_level == 2:
            self.domain_batch_size = {}
            accumulated = 0
            for i, domain in enumerate(domain_list):
                if i == len(domain_list) - 1:
                    domain_batch_size = self.pipeline_config.rollout_batch_size - accumulated
                else:
                    domain_batch_size = int(domain_ratios[domain] * self.pipeline_config.rollout_batch_size)
                accumulated += domain_batch_size
                self.domain_batch_size[domain] = domain_batch_size
                assert domain_batch_size < len(self.domain_datasets[domain]), (f"domain_batch_size {domain_batch_size} must be "
                                                                f"less than the number of domain datasets {len(self.domain_datasets[domain])}")

            generate_scheduler = MultiAsyncDynamicSamplingScheduler.options(
                scheduling_strategy=NodeAffinitySchedulingStrategy(
                    node_id=ray.get_runtime_context().get_node_id(),
                    soft=False,
                )
            ).remote(pipeline_config=self.pipeline_config)
            ray.get(
                generate_scheduler.set_scheduler.remote(
                    actor_cluster=self.actor_infer,
                    reward_clusters={domain: self.rewards[domain] for domain in domain_list},
                    domain2dataset={domain: self.domain_datasets[domain] for domain in domain_list},
                    collect_fn_cls=DataCollatorWithPaddingForPaddedKeys,
                    collect_fn_kwargs=dict(max_length=self.pipeline_config.prompt_length, padding="max_length"),
                    response_filter_fn=lambda data_item, config: True,
                    query_filter_fn=query_filter_fn,
                    pre_pass_query_filter_fn=pre_pass_query_filter_fn,
                    response_callback_fn=generate_scheduler.report_response.remote,
                    migrate_callback_fn=generate_scheduler.migrate_response.remote,
                    state=self.state.kv.get(f"scheduler_state_all", None),
                )
            )
            self.generate_schedulers[MULTI_SCHED_NAME] = generate_scheduler


        print('finsihed init generate_schedulers')
        if False:
            val_pipeline_config = copy.deepcopy(self.pipeline_config)
            val_pipeline_config.use_additional_prompts = False
            self.val_generate_scheduler = AsyncDynamicSamplingScheduler.options(
                scheduling_strategy=NodeAffinitySchedulingStrategy(
                    node_id=ray.get_runtime_context().get_node_id(),
                    soft=False,
                )
            ).remote(pipeline_config=val_pipeline_config)
        if False:
            ray.get(
                self.val_generate_scheduler.set_scheduler.remote(
                    actor_cluster=self.actor_infer,
                    reward_clusters=self.rewards,
                    dataset=self.val_dataset,
                    collect_fn_cls=DataCollatorWithPaddingForPaddedKeys,
                    collect_fn_kwargs=dict(max_length=self.pipeline_config.prompt_length, padding="max_length"),
                    response_filter_fn=lambda data_item, config: True,
                    query_filter_fn=lambda data_list, config: True,
                    response_callback_fn=self.val_generate_scheduler.report_response.remote,
                )
            )
        import time 
        start = time.time()
        refs = []
        refs.extend(self.actor_infer.initialize(pipeline_config=self.pipeline_config, blocking=False))
        ray.get(refs)

        print('complete initialize actor_infer cluster, it takes {} seconds'.format(time.time() - start), flush=True)
        start = time.time()

        if self.pipeline_config.multi_infer_tp:
            refs = []
            refs.extend(self.actor_infer_tp.initialize(pipeline_config=self.pipeline_config, blocking=False))
            ray.get(refs)
            print('complete initialize actor_infer_tp cluster, it takes {} seconds'.format(time.time() - start), flush=True)
            start = time.time()

        if self.reference is not None: 
            refs.extend(self.reference.initialize(pipeline_config=self.pipeline_config, blocking=True))
            refs = []
            for key, cluster in self.rewards.items():
                refs.extend(cluster.initialize(pipeline_config=self.pipeline_config, blocking=False))
            ray.get(refs)
        print('complete initialize reference cluster, it takes {} seconds'.format(time.time() - start), flush=True)
        start = time.time()

        if self.actor_train is not None: 
            refs: List[ray.ObjectRef] = []
            refs.extend(self.actor_train.initialize(pipeline_config=self.pipeline_config, blocking=False))
            if self.pipeline_config.adv_estimator == "gae":
                refs.extend(self.critic.initialize(pipeline_config=self.pipeline_config, blocking=False))
            ray.get(refs)
            print('complete initialize actor_train cluster, it takes {} seconds'.format(time.time() - start), flush=True)
        
        start = time.time()
        if self.actor_train is not None: 
            self.set_model_update_pair(
                src_cluster=self.actor_train,
                tgt_cluster=self.actor_infer,
                frequency=self.pipeline_config.actor_train.model_update_frequency,
            )
            print('complete initialize  model update group actor_train-actor_infer, it takes {} seconds'.format(time.time() - start))
            
            if self.pipeline_config.multi_infer_tp:
                self.set_model_update_pair(
                    src_cluster=self.actor_train,
                    tgt_cluster=self.actor_infer_tp,
                    frequency=self.pipeline_config.actor_train.model_update_frequency,
                )
                start = time.time()
                print('complete initialize  model update group actor_train-actor_infer_tp, it takes {} seconds'.format(time.time() - start))

            
            if self.pipeline_config.adv_estimator == "gae":
                self.set_checkpoint_clusters(self.actor_train, self.critic)
            else:
                self.set_checkpoint_clusters(self.actor_train)

        self.running = {}
        for domain in self.rewards.keys():
            self.running[domain] = RunningMoments()


        self.gpu_tracker = GPUTracker(
                    interval=2,
                    output_dir="./logs",
                    filename="gpu_usage.json"
                )
        register_autoscaling_ranks(self.actor_train, self.pipeline_config)
        for name, scheduler in self.generate_schedulers.items(): 
            ray.get(scheduler.reset_pipeline_config.remote(self.pipeline_config))

    @torch.no_grad()
    def run(self):
        # 计算tokens per second 系统吞吐
        loop = asyncio.new_event_loop()

        def run_async():
            asyncio.set_event_loop(loop)
            loop.run_forever()

        # 创建一个专门管理监控指标的类
        metrics_mgr = MetricsManager()

        tps_timer = _Timer(window_size=5)
        actor_infer_timer = _Timer(window_size=5)
        actor_infer_response_timer = _Timer(window_size=5)
        actor_train_timer = _Timer(window_size=5)

        use_large_tp = False

        running_infer_server = self.actor_infer
        next_running_server = self.actor_infer

        for global_step in range(self.pipeline_config.max_steps):
            if global_step <= self.state.step:
                global_step += 1
                continue
            logger.info(f"pipeline step {global_step} start...")

            if False: 
                thread = threading.Thread(target=run_async, daemon=True)
                thread.start()
                asyncio.run_coroutine_threadsafe(self.gpu_tracker.start(), loop)

            # import pdb; pdb.set_trace()
            metrics_mgr.clear_metrics()
            with tps_timer, Timer(name="step_total", logger=None) as step_total_timer:

                # 先model update，resume时不需要保存infer cluster的状态
                if self.pipeline_config.adv_estimator == "gae":
                    self.critic.offload_states(blocking=True)
                if self.actor_train is not None:
                    self.actor_train.offload_states(blocking=True)
                if self.pipeline_config.multi_infer_tp and global_step == 0:
                    print(f"[DEBUG] offload additional infer instance to save GPU memory...")
                    self.actor_infer_tp.offload_states(blocking=True)
                if False: 
                    with Timer(name="step_model_update", logger=None) as step_model_update_timer:
                        model_update_metrics: Dict = self.model_update(global_step)
                        metrics_mgr.add_metrics(model_update_metrics)
                    metrics_mgr.add_metric("time/step_model_update", step_model_update_timer.last)

                if self.val_dataset and global_step % self.pipeline_config.eval_steps == 0:
                    with Timer(name="val_step", logger=None) as val_step_timer:
                        val_metrics = self.val()
                        metrics_mgr.add_metrics(val_metrics)
                    metrics_mgr.add_metric("time/val_step", val_step_timer.last)

                batch: DataProto = DataProto()
                batch.meta_info = {"global_step": global_step}

                
                record_time_list = list()
                # 要按domain group by生成对应的batch

                print(f"[DEBUG] HERE")
                if False: 
                    with actor_infer_timer, actor_infer_response_timer, Timer(
                        name="step_generate", logger=None
                    ) as step_generate_timer:
                        domain_batches = {}
                        batch.meta_info["generation_config"] = running_infer_server.worker_config.generating_args.to_dict()
                        # scale up max length
                        # self.post_process_generating_args(batch.meta_info["generation_config"], self.pipeline_config)
                        if self.pipeline_config.generate_opt_level > 0: 
                            running_infer_server.start_server(data=DataProto(meta_info=batch.meta_info))
                        
                        for reward_cluster in self.rewards.values():
                            reward_cluster.load_states()

                        batch.meta_info["is_offload_states"] = False
                        scheduler_refs = {}
                        
                        
                        disable_stop_server = len(self.generate_schedulers) > 1
                        for domain, scheduler in self.generate_schedulers.items():
                            if self.pipeline_config.generate_opt_level not in [0, 1]: continue
                            if self.pipeline_config.generate_opt_level == 0:
                                batch.meta_info["domain"] = domain
                                batch.meta_info["batch_size"] = self.domain_batch_size[domain]
                                ray.get(scheduler.reset_status.remote(batch_size=self.domain_batch_size[domain]))
                                scheduler_refs[domain] = scheduler.generate.remote(data=batch, pipeline_config=self.pipeline_config)
                            else: 
                                batch.meta_info["domain"] = domain
                                batch.meta_info["batch_size"] = self.domain_batch_size[domain]
                                ray.get(scheduler.reset_status.remote(batch_size=self.domain_batch_size[domain]))
                                scheduler_refs[domain] = scheduler.get_batch.remote(data=batch, batch_size=self.domain_batch_size[domain], first_half=False, disable_stop_server=disable_stop_server)
                        
                        if self.pipeline_config.generate_opt_level == 2:
                            batch.meta_info["domain2batchsize"] = copy.deepcopy(self.domain_batch_size)
                            batch_size_of_all_domains = sum(self.domain_batch_size.values())
                            print(f"[DEBUG] get_batch")
                            domain = MULTI_SCHED_NAME
                            ray.get(scheduler.reset_status.remote(batch_size=batch_size_of_all_domains))
                            scheduler_refs[MULTI_SCHED_NAME] = scheduler.get_batch.remote(data=batch, batch_size_of_all_domains=batch_size_of_all_domains, first_half=False)
                            # FIXME here
                            
                        
                        if self.pipeline_config.autoscaling:
                            can_prefetch = False 
                            while True:
                                try:
                                    can_prefetch = ray.get(self.generate_schedulers[domain].can_prefetch_requests.remote(), timeout=2) # assume only has one domain
                                except ray.exceptions.GetTimeoutError:
                                    print("Timed out waiting for can_prefetch_requests to return.")
                                    continue
                                # print(f"can can_prefetch {can_prefetch}", flush=True)
                                if can_prefetch:
                                    break
                                time.sleep(1)
                            
                            if False: 
                                prefetch_domain_batches = ray.get(self.generate_schedulers[domain].prefetch_completed_requests.remote())

                                prefetch_cnt = len(prefetch_domain_batches.batch) if prefetch_domain_batches.batch is not None else 0
                                metrics_mgr.add_metric("async_time/async_prefetch_count", prefetch_cnt)

                                if prefetch_domain_batches.batch is not None and len(prefetch_domain_batches.batch) > 0:
                                    self.train_second_half(prefetch_domain_batches=prefetch_domain_batches, metrics_mgr=metrics_mgr, record_time_list=record_time_list, _ranks=copy.deepcopy(self.pipeline_config.secod_half_ranks))
                                    print(f"prefetch_domain_batches.batch size {prefetch_domain_batches.batch}", flush=True)
                                else:
                                    pass

                            world_size = self.pipeline_config.actor_train.world_size
                            _ranks = copy.deepcopy(self.pipeline_config.second_half_ranks)
                            print(f"[DEBUG] Train some thing!")
                            self.train_second_half_with_func(meta_data=DataProto(meta_info={"global_step": global_step, "is_offload_states": False}), \
                                                prefetch_actor=self.generate_schedulers[domain], 
                                                metrics_mgr=metrics_mgr,
                                                _ranks=_ranks,
                                                record_time_list=record_time_list)
                        # end of second_half execution
                        
                        self.record_key_metrics(key_event='start_get_scheduler_ref', record_time_list=record_time_list)

                        for domain, scheduler_ref in scheduler_refs.items():
                            if self.pipeline_config.generate_opt_level not in [0, 1]: continue 
                            domain_batch: DataProto = ray.get(scheduler_ref, timeout=self.pipeline_config.rpc_timeout)
                            metrics_mgr.add_domain_metrics(
                                domain, reduce_metrics(domain_batch.meta_info.pop("metrics", {}))
                            )
                            domain_batches[domain] = domain_batch
                            
                            metrics_mgr.add_domain_metrics(
                                domain, domain_batch.meta_info.pop('time/reward_worker_costs')
                            )

                        if self.pipeline_config.generate_opt_level == 2: 
                            domain_batches[MULTI_SCHED_NAME], collected_long_prompts = ray.get(scheduler_refs[MULTI_SCHED_NAME], timeout=self.pipeline_config.rpc_timeout)
                            domain_metrics = domain_batches[MULTI_SCHED_NAME].meta_info.pop('metric', {})
                            for domain in domain_metrics.keys(): 
                                metrics_mgr.add_domain_metrics(
                                    domain, reduce_metrics(domain_metrics[domain])
                                )
                                # FIXME: this might not work
                                metrics_mgr.add_domain_metrics(
                                    domain, domain_batch.meta_info.pop('time/reward_worker_costs')
                                )

                            if collected_long_prompts >= sum(self.domain_batch_size.values()) and self.pipeline_config.multi_infer_tp:
                                use_large_tp = True
                                ray.get(
                                    self.generate_schedulers[MULTI_SCHED_NAME].reset_actor_cluster.remote(
                                        actor_cluster=self.actor_infer_tp
                                    )
                                )
                                next_running_server = self.actor_infer_tp
                                print(f"[INFER ENGINE]: Switch to tp2")
                            elif use_large_tp:
                                use_large_tp = False
                                ray.get(
                                    self.generate_schedulers[MULTI_SCHED_NAME].reset_actor_cluster.remote(
                                        actor_cluster=self.actor_infer
                                    )
                                )
                                next_running_server = self.actor_infer
                                print(f"[INFER ENGINE]: Switch back to tp1")
                            
                        
                        generate_output = DataProto.concat([domain_batch for domain_batch in domain_batches.values()])
                        generate_output.meta_info.pop("is_offload_states", None)

                        self.record_key_metrics(key_event='finish_get_scheduler_ref', record_time_list=record_time_list)

                        if self.pipeline_config.record_time_profiler_log_dir is not None:
                            profiler_log_dir = self.pipeline_config.record_time_profiler_log_dir
                            if not os.path.exists(profiler_log_dir): 
                                os.makedirs(profiler_log_dir)

                            for domain, scheduler_ref in scheduler_refs.items():
                                record_time_list.extend(ray.get(self.generate_schedulers[domain].get_record_time_list.remote()))
                                if record_time_list[-1] is None: 
                                    record_time_list.pop()

                        
                        for reward_cluster in self.rewards.values():
                            reward_cluster.offload_states()
                        
                        if disable_stop_server: 
                            # gen_metrics = self.actor_infer.stop_server()
                            gen_metrics = running_infer_server.stop_server()
                            metrics_mgr.add_domain_metrics(domain, reduce_metrics(gen_metrics.meta_info.pop("metrics", {})))

                    metrics_mgr.add_metric("time/step_generate", step_generate_timer.last)



                if True: 
                    # import pdb; pdb.set_trace()
                    if False:
                        batch.batch = torch.load('batch_train.pt', weights_only=False)['batch']
                        batch.meta_info['global_step'] = global_step
                        prefetch_domain_batches = batch # torch.load('batch_train.pt', weights_only=False)['batch']
                    prefetch_domain_batches = torch.load('batch_train.pt', weights_only=False)['batch']
                    prefetch_domain_batches.meta_info['global_step'] = global_step
                    prefetch_domain_batches = prefetch_domain_batches[:64]

                    if prefetch_domain_batches.batch is not None and len(prefetch_domain_batches.batch) > 0:
                        world_size = self.pipeline_config.actor_train.world_size
                        # _ranks = list(range(world_size // 2, world_size))
                        _ranks = copy.deepcopy(self.pipeline_config.second_half_ranks)
                        print(f"_ranks is {_ranks}", flush=True)
                        self.train_second_half(prefetch_domain_batches=prefetch_domain_batches, metrics_mgr=metrics_mgr, record_time_list=record_time_list, _ranks=_ranks)
                        print(f"prefetch_domain_batches.batch size {prefetch_domain_batches.batch}", flush=True)
                    else:
                        pass

                    if True:
                        pass
                        prefetch_cnt = len(prefetch_domain_batches.batch) if prefetch_domain_batches.batch is not None else 0
                        metrics_mgr.add_metric("async_time/async_prefetch_count", prefetch_cnt)
                        actor_train_metrics_refs = self.actor_train.train_step_full(prefetch_domain_batches, blocking=True)
                        print("pass train_step_full")

                    import pdb; pdb.set_trace()
                    prefetch_domain_batches = torch.load('batch_train.pt', weights_only=False)['batch']
                    print("[DEBUG] prefetch_domain_batches.batch with train_step_full", flush=True)
                    print(f"prefetch_domain_batches.batch size {prefetch_domain_batches.batch}", flush=True)
                    actor_train_metrics_refs = self.actor_train.train_step_full(prefetch_domain_batches, blocking=False)


                # if self.pipeline_config.record_time_profiler_log_dir is not None:
                #     profiler_log_dir = self.pipeline_config.record_time_profiler_log_dir
                #     filename = f'{profiler_log_dir}/gpu_util_iter_{global_step}.json'
                #     self.gpu_tracker.stop(filename=filename)
                #     loop.call_soon_threadsafe(loop.stop)
                #     thread.join()
                    
                import pdb; pdb.set_trace() 
                batch = generate_output
                if self.pipeline_config.autoscaling: 
                    metrics_mgr.add_metric("async_time/async_remaining_count", batch.batch.size(0))
                
                prompt_token_count = batch.batch['prompt_mask'].sum().item()
                response_token_count = batch.batch['response_mask'].sum().item()
                metrics_mgr.add_metric("async_time/async_prompt_tokens", prompt_token_count)
                metrics_mgr.add_metric("async_time/async_response_tokens", response_token_count)
                metrics_mgr.add_metric("async_time/async_total_tokens", prompt_token_count+response_token_count)

                if self.reference is not None:
                    if self.pipeline_config.use_kl_loss: 
                        with Timer(name="cal_ref_log_probs", logger=None) as cal_ref_log_probs_timer:
                            ref_log_probs = self.reference.compute_log_probs(batch, blocking=True)
                            metrics_mgr.add_reduced_metrics(ref_log_probs.meta_info.pop("metrics", {}))
                            ref_log_probs.rename(old_keys="log_probs", new_keys="ref_log_probs")
                            batch = batch.union(ref_log_probs)
                            metrics_mgr.add_metric("time/ref_log_probs_values", cal_ref_log_probs_timer.last)

                self.record_key_metrics(key_event='start_cal_old_log_probs_values', record_time_list=record_time_list)

                if True:
                    with Timer(name="cal_old_log_probs_values", logger=None) as cal_old_logpb_timer:
                        batch.meta_info["is_offload_states"] = False
                        if self.pipeline_config.adv_estimator == "gae":
                            values_refs: List[ray.ObjectRef] = self.critic.compute_values(batch, blocking=False)
                        
                        if self.pipeline_config.fake_old_log_probs:
                            tok_len = batch.batch['response_mask'].size(1)
                            old_log_probs = DataProto.from_dict(tensors={'log_probs':torch.randn((batch.batch.size(0), tok_len-1)), 
                                                                        'entropy':torch.randn((batch.batch.size(0), tok_len-1))})
                        else: 
                            old_log_probs_refs: List[ray.ObjectRef] = self.actor_train.compute_log_probs(batch, blocking=False)
                            old_log_probs = DataProto.materialize_concat(data_refs=old_log_probs_refs)

                        

                        agg_entropy = agg_loss(
                            loss_mat=old_log_probs.batch["entropy"],
                            loss_mask=batch.batch["response_mask"][:, 1:],
                            loss_agg_mode="token-mean",
                        )
                        batch.meta_info["agg_entropy"] = agg_entropy

                        if self.pipeline_config.adv_estimator == "gae":
                            values = DataProto.materialize_concat(data_refs=values_refs)
                            batch = batch.union(values)
                            metrics_mgr.add_reduced_metrics(values.meta_info.pop("metrics", {}))
                        
                        batch.batch["old_log_probs"] = old_log_probs.batch["log_probs"]
                        if not self.pipeline_config.use_kl_loss:
                            batch.batch['ref_log_probs'] = old_log_probs.batch["log_probs"] # for no bug, not use reference model 
                        metrics_mgr.add_reduced_metrics(old_log_probs.meta_info.pop("metrics", {}))
                    metrics_mgr.add_metric("time/old_log_probs", cal_old_logpb_timer.last)
                
                self.record_key_metrics(key_event='finish_cal_old_log_probs_values', record_time_list=record_time_list)
                self.record_key_metrics(key_event='start_domain_processing', record_time_list=record_time_list)

                # 要按domain group by处理reward
                batch.batch["prompt_id"] = torch.arange(batch.batch.batch_size[0], device=batch.batch.device)
                batch_grouped: Dict[str, DataProto] = batch.group_by("domain")
                batch_list = []
                for domain, domain_batch in batch_grouped.items():
                    # 1. 处理mask相关策略， 获取sample level mask
                    with Timer(name="get_sample_level_mask", logger=None) as get_sample_level_mask_timer:
                        domain_batch, mask_metrics = get_sample_level_mask(domain_batch, self.pipeline_config)
                        metrics_mgr.add_metrics(mask_metrics)
                    metrics_mgr.add_metric("time/get_sample_level_mask", get_sample_level_mask_timer.last)

                    # 2. 处理reward相关策略
                    with Timer(name="reward_postprocess", logger=None) as reward_postprocess_timer:
                        domain_batch, response_level_metrics = reward_postprocess(
                            domain_batch, self.pipeline_config, self.running
                        )
                        metrics_mgr.add_metrics(response_level_metrics)
                    metrics_mgr.add_metric("time/reward_postprocess", reward_postprocess_timer.last)

                    # 3. 计算token level rewards
                    with Timer(name="get_token_reward", logger=None) as get_token_reward_timer:
                        domain_batch, token_level_metrics = compute_token_reward(
                            domain_batch, self.pipeline_config, self.kl_ctrl
                        )
                        metrics_mgr.add_metrics(token_level_metrics)
                    metrics_mgr.add_metric("time/get_token_reward", get_token_reward_timer.last)

                    # 4. 计算advantage
                    final_response_mask = domain_batch.batch["final_response_mask"].clone()
                    with Timer(name="compute_advantage", logger=None) as compute_advantage_timer:
                        domain_batch = compute_advantage(
                            data=domain_batch,
                            gamma=self.pipeline_config.gamma,
                            lambd=self.pipeline_config.lambd,
                            adv_estimator=self.pipeline_config.adv_estimator,
                            advantage_clip=self.pipeline_config.advantage_clip,
                            whiten_advantages=self.pipeline_config.whiten_advantages,
                            whiten_rewards=self.pipeline_config.whiten_rewards,
                            response_mask=final_response_mask,
                        )
                        domain_metrics = reduce_metrics(domain_batch.meta_info.pop("metrics", {}))
                        metrics_mgr.add_domain_metrics(domain, domain_metrics)
                        metrics_mgr.add_metric("time/compute_advantage", compute_advantage_timer.last)
                        batch_list.append(domain_batch)

                self.record_key_metrics(key_event='finish_domain_processing', record_time_list=record_time_list)

                batch = DataProto.concat(batch_list)
                batch.reorder(indices=torch.argsort(batch.batch["prompt_id"]))
                batch.pop("prompt_id")
                # self.save_intermediate_output(batch, 'batch_train.pt')
                # if global_step == 0: 
                #     torch.save({'batch':batch.batch}, 'batch_train.pt')
                #     import pdb; pdb.set_trace()

                metrics_mgr.add_all_metrics(
                    global_step,
                    batch,
                    resource_manager=self.resource_manager,
                    actor_infer=running_infer_server,
                    actor_train=self.actor_train,
                )

                running_infer_server = next_running_server
                batch_grouped: Dict[str, DataProto] = batch.group_by("domain")
                metrics_mgr.add_domain_all_metrics(global_step, batch_grouped)

                self.record_key_metrics(key_event='start_step_train', record_time_list=record_time_list)

                with Timer(name="step_train", logger=None) as step_train_timer:
                    if self.pipeline_config.adv_estimator == "gae":
                        critic_train_metrics_refs: List[ray.ObjectRef] = self.critic.train_step(batch, blocking=False)

                    with actor_train_timer:
                        # implement critic warmup
                        if self.pipeline_config.critic_warmup <= global_step:
                            # update actor
                            batch.meta_info['is_offload_states'] = True

                            if self.pipeline_config.autoscaling: 
                                actor_train_metrics_refs = self.actor_train.train_step_full(batch, blocking=False)
                            else:
                                actor_train_metrics_refs = self.actor_train.train_step(batch, blocking=False)
                                

                            actor_train_metrics: DataProto = DataProto.materialize_concat(
                                data_refs=actor_train_metrics_refs
                            )
                            metrics_mgr.add_reduced_metrics(actor_train_metrics.meta_info.pop("metrics", {}))
                            

                    if self.pipeline_config.adv_estimator == "gae":
                        critic_train_metrics = DataProto.materialize_concat(data_refs=critic_train_metrics_refs)
                        metrics_mgr.add_reduced_metrics(critic_train_metrics.meta_info.pop("metrics", {}))

                self.record_key_metrics(key_event='finish_step_train', record_time_list=record_time_list)

                if self.pipeline_config.record_time_profiler_log_dir is not None:
                    profiler_log_dir = self.pipeline_config.record_time_profiler_log_dir
                    with open(f'{profiler_log_dir}/reocord_time_iter_{global_step}.json', 'w') as fd:
                        json.dump(record_time_list, fd)
                    print("log path is {}".format(f'{profiler_log_dir}/reocord_time_iter_{global_step}.json'))
                    
                metrics_mgr.add_metric("time/step_train", step_train_timer.last)

                tps_timer.push_units_processed(n=torch.sum(batch.batch["attention_mask"]).detach().item())
                actor_infer_timer.push_units_processed(n=torch.sum(batch.batch["attention_mask"]).detach().item())
                actor_infer_response_timer.push_units_processed(
                    n=torch.sum(batch.batch["response_mask"]).detach().item()
                )
                actor_train_timer.push_units_processed(n=torch.sum(batch.batch["attention_mask"]).detach().item())

                self.state.step = global_step
                if global_step % self.pipeline_config.logging_steps == 0:
                    if int(os.environ.get("RAY_PROFILING", "0")):
                        timeline_dir = os.path.join(self.pipeline_config.profiler_output_dir, "timeline")
                        os.makedirs(timeline_dir, exist_ok=True)
                        ray.timeline(
                            filename=os.path.join(timeline_dir, f"timeline-step-{global_step}.json"),
                        )

                logger.info(f"pipeline step {global_step} finished")

            metrics_mgr.add_metric("time/step_total", step_total_timer.last)
            metrics = metrics_mgr.get_metrics()

            # do ckpt
            self.state.step = global_step
            self.state.log_history.append(metrics)
            for domain, scheduler in self.generate_schedulers.items():
                self.state.kv[f"scheduler_state_{domain}"] = ray.get(scheduler.get_scheduler_state.remote())
            
            self.do_checkpoint(global_step=global_step)
            
            self.tracker.log(values=metrics, step=global_step)

            global_step += 1

            if (global_step + 1) >= self.pipeline_config.debug_max_steps: 
                break 
        logger.info("pipeline complete!")

    @torch.no_grad()
    def val(self):
        val_metrics_mgr = MetricsManager()
        batch = DataProto()

        with Timer(name="step_generate", logger=None) as step_generate_timer:
            batch.meta_info["is_offload_states"] = False
            batch.meta_info["generation_config"] = self.pipeline_config.validation.generating_args.to_dict()
            if self.pipeline_config.generate_opt_level > 0: 
                self.actor_infer.start_server(data=DataProto(meta_info=batch.meta_info))
            for reward_cluster in self.rewards.values():
                reward_cluster.load_states()
            generate_output: DataProto = ray.get(
                self.val_generate_scheduler.get_batch.remote(data=batch, batch_size=len(self.val_dataset)),
                timeout=self.pipeline_config.rpc_timeout
            )
            if self.pipeline_config.generate_opt_level > 0: 
                self.actor_infer.stop_server()
            generate_output.meta_info.pop("is_offload_states", None)
            for reward_cluster in self.rewards.values():
                reward_cluster.offload_states()
            val_metrics_mgr.add_metric("time/step_generate", step_generate_timer.last)

        batch = generate_output
        val_correct_mean = (batch.batch["scores"] == 1).detach().float().mean().item()
        val_metrics_mgr.add_metric("val_correct/all/mean", val_correct_mean)
        logger.info(json.dumps({"val_correct/all/mean": val_correct_mean}, ensure_ascii=False))

        epoch_batch = batch.pop(batch_keys=["scores"], non_tensor_batch_keys=["tag"])

        grouped_batch = epoch_batch.group_by("tag")
        for group_key, group_batch in grouped_batch.items():
            score_mean = group_batch.batch["scores"].mean().item()
            print(f"{group_key}:  {score_mean}")
            val_metrics_mgr.add_domain_metrics(
                "val_correct", {f"{group_key}/mean": (group_batch.batch["scores"] == 1).detach().float().mean().item()}
            )

        return val_metrics_mgr.get_metrics()

    def train_second_half_with_func(self, meta_data: DataProto, prefetch_actor: ActorHandle, metrics_mgr: MetricsManager, _ranks: list[int], **kwargs):

        print("[DEBUG] train_second_half_with_func start!")
        import time
        prefix = 'async'
        record_time_list = kwargs.get('record_time_list', list())
        self.record_key_metrics(key_event=f"start_{prefix}_step_train_second_half", record_time_list=record_time_list)

        actor_half_train_metrics = self.actor_train.train_step_second_half_with_func(meta_data=meta_data, prefetch_actor=prefetch_actor, running=self.running, kl_ctrl=self.kl_ctrl, _ranks=_ranks, blocking=True)
        metrics_mgr.add_reduced_metrics(actor_half_train_metrics[0].meta_info.pop("metrics", {}))
        self.record_key_metrics(key_event=f"finish_{prefix}_step_train_second_half", record_time_list=record_time_list)

        print("[DEBUG] train_second_half_with_func done!")
    

    def train_second_half(self, prefetch_domain_batches: List[DataProto], metrics_mgr: MetricsManager, _ranks: List[int], **kwargs):
        prefetch_domain_batches.batch["prompt_id"] = torch.arange(prefetch_domain_batches.batch.batch_size[0], device=prefetch_domain_batches.batch.device)
        prefix = 'async'
        record_time_list = kwargs.get('record_time_list', list())
        import time
        with Timer(name=f'{prefix}_step_total', logger=None) as async_step_timer: 
            self.record_key_metrics(key_event=f"start_{prefix}_cal_old_log_probs_values", record_time_list=record_time_list)
            if False: 
                with Timer(name=f"{prefix}_cal_old_log_probs_values", logger=None) as cal_old_logpb_timer:
                    if self.pipeline_config.fake_old_log_probs: 
                        tok_len = prefetch_domain_batches.batch['response_mask'].size(1)
                        prefetch_domain_batches.batch["old_log_probs"] = torch.randn((prefetch_domain_batches.batch.size(0), tok_len-1))
                    else:
                        old_log_probs_refs: List[ray.ObjectRef] = self.actor_train.compute_log_probs_second_half(prefetch_domain_batches, _ranks, blocking=False)
                        old_log_probs = DataProto.materialize_concat(data_refs=old_log_probs_refs)
                        prefetch_domain_batches.batch["old_log_probs"] = old_log_probs
                    prefetch_domain_batches.batch['ref_log_probs'] = prefetch_domain_batches.batch["old_log_probs"]

                    
                metrics_mgr.add_metric(f"{prefix}_time/old_log_probs", cal_old_logpb_timer.last)
                self.record_key_metrics(key_event=f"finish_{prefix}_cal_old_log_probs_values", record_time_list=record_time_list)
                batch_grouped: Dict[str, DataProto] = prefetch_domain_batches.group_by("domain")
                batch_list = []

                for domain, domain_batch in batch_grouped.items():
                    # 1. 处理mask相关策略， 获取sample level mask
                    with Timer(name=f"{prefix}_get_sample_level_mask", logger=None) as get_sample_level_mask_timer:
                        domain_batch, mask_metrics = get_sample_level_mask(domain_batch, self.pipeline_config)
                        metrics_mgr.add_metrics(mask_metrics)
                    metrics_mgr.add_metric(f"{prefix}_time/get_sample_level_mask", get_sample_level_mask_timer.last)

                    # 2. 处理reward相关策略
                    with Timer(name=f"{prefix}_reward_postprocess", logger=None) as reward_postprocess_timer:
                        domain_batch, response_level_metrics = reward_postprocess(
                            domain_batch, self.pipeline_config, self.running
                        )
                        metrics_mgr.add_metrics(response_level_metrics)
                    metrics_mgr.add_metric(f"{prefix}_time/reward_postprocess", reward_postprocess_timer.last)

                    # 3. 计算token level rewards
                    with Timer(name=f"{prefix}_get_token_reward", logger=None) as get_token_reward_timer:
                        domain_batch, token_level_metrics = compute_token_reward(
                            domain_batch, self.pipeline_config, self.kl_ctrl
                        )
                        metrics_mgr.add_metrics(token_level_metrics)
                    metrics_mgr.add_metric(f"{prefix}_time/get_token_reward", get_token_reward_timer.last)

                    # 4. 计算advantage
                    final_response_mask = domain_batch.batch["final_response_mask"].clone()
                    with Timer(name=f"{prefix}_compute_advantage", logger=None) as compute_advantage_timer:
                        domain_batch = compute_advantage(
                            data=domain_batch,
                            gamma=self.pipeline_config.gamma,
                            lambd=self.pipeline_config.lambd,
                            adv_estimator=self.pipeline_config.adv_estimator,
                            advantage_clip=self.pipeline_config.advantage_clip,
                            whiten_advantages=self.pipeline_config.whiten_advantages,
                            whiten_rewards=self.pipeline_config.whiten_rewards,
                            response_mask=final_response_mask,
                        )
                        domain_metrics = reduce_metrics(domain_batch.meta_info.pop("metrics", {}))
                        metrics_mgr.add_domain_metrics(domain, domain_metrics)
                        batch_list.append(domain_batch)
                    metrics_mgr.add_metric(f"{prefix}_time/compute_advantage", compute_advantage_timer.last)

                prefetch_domain_batches = DataProto.concat(batch_list)
                prefetch_domain_batches.reorder(indices=torch.argsort(prefetch_domain_batches.batch["prompt_id"]))
                prefetch_domain_batches.pop("prompt_id")

            with Timer(name=f'{prefix}_step_train_second_half', logger=None) as actor_train_second_half_timer:
                self.actor_train.train_step_second_half(prefetch_domain_batches, _ranks=_ranks, blocking=True)
            metrics_mgr.add_metric('time/async_step_train_second_half', actor_train_second_half_timer.last)
            
            self.record_key_metrics(key_event=f"finish_{prefix}_step_train_second_half", record_time_list=record_time_list)

        metrics_mgr.add_metric("time/async_step_total", async_step_timer.last)
    

    def save_intermediate_output(self, output: DataProto, filename: str): 
        output.batch = output.batch.contiguous()
        output.batch = output.batch.consolidate()
        torch.save({"batch": output}, filename)

    
    def sweep_infer_batch_size(self, batch: DataProto): 
        import pprint 
        import time 
        time_infos = dict() 
        for micro_batch_size in [1, 2, 4, 8]: # , 12]: 
            start = time.time() 
            batch.meta_info['micro_batch_size'] = micro_batch_size
            old_log_probs_refs: List[ray.ObjectRef] = self.actor_train.compute_log_probs(batch, blocking=False)
            old_log_probs = DataProto.materialize_concat(data_refs=old_log_probs_refs)
            print('micro_batch_size {} takes {}'.format(micro_batch_size, time.time() - start))
            time_infos[micro_batch_size] = time.time() - start
            pprint.pprint(time_infos)

        import pprint 
        pprint.pprint(time_infos)


    def sweep_training_batch_size(self, batch: DataProto):
        import pprint
        import time 
        time_infos = dict()
        for per_device_batch_size in [1, 2, 4, 8]: 
            batch.meta_info['per_device_batch_size'] = per_device_batch_size
            start = time.time()
            actor_train_metrics_refs = self.actor_train.train_step(batch, blocking=True) #20GB
            time_infos[per_device_batch_size] = time.time() - start
            print(f'the time infos during training step is {time_infos}', flush=True)

    def post_process_generating_args(self, generating_config: Dict[str, Any], pipeline_config: RLVRConfig, global_step: int):
        schedule_steps = self.pipeline_config.schedule_steps
        max_new_token_ratios = self.pipeline_config.schedule_max_new_token_ratios
        ratio = 1
        for step in schedule_steps: 
            if global_step < step: 
                ratio = max_new_token_ratios[step]
                break
        generating_config["max_new_tokens"] *= ratio
    
    def record_key_metrics(self, key_event, record_time_list): 
        if self.pipeline_config.record_time_profiler_log_dir:
            record_time_list.append(
                {
                    'event_type': key_event, 
                    'absolute_time': time.time(),
                }
            )