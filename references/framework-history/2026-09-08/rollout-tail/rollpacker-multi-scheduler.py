import copy
import itertools
import queue
import random
import threading
import time
import hashlib
import base64
from collections import defaultdict
from typing import Any, Union, Optional, Dict, List, Set
import json
import numpy as np
import ray
import torch
from datasets import Dataset
from tensordict import TensorDict
from torch.nn.utils.rnn import pad_sequence
from tqdm import tqdm
from transformers import set_seed
import os

from roll.utils.constants import FixedTimeOut

from roll.distributed.executor.cluster import Cluster
from roll.distributed.scheduler.protocol import DataProto, collate_fn
from roll.models.model_providers import default_tokenizer_provider
from roll.utils.constants import RAY_NAMESPACE
from roll.utils.functionals import (
    postprocess_generate,
    reduce_metrics,
    concatenate_input_and_output,
    GenerateRequestType,
)
from roll.utils.logging import get_logger
from roll.utils.multi_thread_utils import ThreadSafeDict

from roll.utils.functionals import (
    compute_advantage,
    reduce_metrics,
    RunningMoments,
    get_sample_level_mask,
    reward_postprocess,
    compute_token_reward,
    agg_loss,
)

logger = get_logger()



def batch_compute_rewards(batch: DataProto, pipeline_config, running, kl_ctrl):
    compute_rewards_start = time.time()
    batch_grouped = batch.group_by('domain')
    batch_list = list()
    for domain, domain_batch in batch_grouped.items():
        domain_start = time.time()
        # 1. 处理mask相关策略， 获取sample level mask
        domain_batch, _ = get_sample_level_mask(domain_batch, pipeline_config)

        # 2. 处理reward相关策略
        domain_batch, __cached__ = reward_postprocess(
            domain_batch, pipeline_config, running,
        )

        # 3. 计算token level rewards
        domain_batch, _ = compute_token_reward(
            domain_batch, pipeline_config, kl_ctrl
        )

        # 4. 计算advantage
        final_response_mask = domain_batch.batch["final_response_mask"].clone()
        domain_batch = compute_advantage(
            data=domain_batch,
            gamma=pipeline_config.gamma,
            lambd=pipeline_config.lambd,
            adv_estimator=pipeline_config.adv_estimator,
            advantage_clip=pipeline_config.advantage_clip,
            whiten_advantages=pipeline_config.whiten_advantages,
            whiten_rewards=pipeline_config.whiten_rewards,
            response_mask=final_response_mask,
        )
        batch_list.append(domain_batch)
        print(f"[domain reward compute]: {time.time() - domain_start}")
    batch_with_rewards = DataProto.concat(batch_list)
    batch_with_rewards.reorder(indices=torch.argsort(batch_with_rewards.batch["prompt_id"]))
    print(f"[batch_compute_rewards]: {time.time() - compute_rewards_start}")
    return batch_with_rewards

@ray.remote(concurrency_groups={"single_thread": 1, "multi_thread": 1024, "prefetch": 1024})
class MultiAsyncDynamicSamplingScheduler:

    def __init__(self, pipeline_config=None, env_vars={}):
        self.env_vars = env_vars
        self.pipeline_config = pipeline_config
        set_seed(seed=pipeline_config.seed)
        self.progress_bar: Optional[tqdm] = None
        self.request_counter = None
        self.dp_fetch_count = {}
        self.load_balance_coordinator = {}
        self.mp_rank_zero = {}
        # prompt_id to unique prompt hash value
        self.prompt_id_2_hash_str: Dict[int, str] = {}
        self.request_id_2_prompt_id: Dict[str, int] = {}
        self.prompt_id_2_request_ids: Dict[int, set] = defaultdict(set)
        self.prompt_id_2_domain: Dict[int, str] = {}
        self.response_batch_size: Optional[int] = None
        self.abort_request_ids: set[str] = set()
        self.request_id_2_dp_rank = {}
        self.requests_buffers: Dict[str, DataProto] = {}
        self.lock = threading.Lock()
        self.migrate_lock = threading.Lock()
        self.post_process_lock = threading.Lock()
        self.last_alive_check = time.time()
        self.dataset_iter_count = 0
        self.exception_queue = queue.Queue()
        self.running = False
        self.dataset_epoch = 0
        self.migrate_waiting_reqs = list()
        self.pre_pass_query_prompts: Dict[int, bool] = {}

        # Flow control measures. max_running_requests limits the maximum number of concurrent requests for each dp.
        # max_additional_running_prompts limits the number of prompts running simultaneously to avoid excessive consumption of prompts.
        self.dynamic_sampling = self.pipeline_config.dynamic_sampling
        self.is_use_pre_pass_filter = self.pipeline_config.is_use_pre_pass_filter
        self.max_running_requests = self.pipeline_config.max_running_requests
        self.max_additional_running_prompts = self.pipeline_config.max_additional_running_prompts
        self.is_use_additional_prompts = self.pipeline_config.is_use_additional_prompts
        self.alive_check_interval = self.pipeline_config.alive_check_interval

        # NOTE: redundant sampling v2 configs
        self.max_prompts_ratio = 1
        self.max_num_return_sequences = self.pipeline_config.max_num_return_sequences
        self.fetch_long_prompts = False
        self.promp_hash_to_request_data: Dict[str, DataProto] = {}

        self.actor_cluster = None
        self.reward_clusters = None
        self.reward_worker_iters = None
        self.dataset = None
        self.indices = []
        self.batch_size_of_all_domains = None
        self.dataset_iter = None
        self.collect_fn_cls = None
        self.collect_fn_kwargs = None
        self.collect_fn = None
        self.tokenizer = None
        self.response_filter_fn = None
        self.query_filter_fn = None
        self.pre_pass_query_filter_fn = None
        self.response_callback_fn = None
        self.generation_config = None

        self.completed_buffers = None
        self.query_group_buffers = None
        self.reward_times = None

        self.query_filter_count = dict()
        self.response_filter_count = dict()
        self.running_prompts = dict()
        self.response_cache: Dict[str, List] = None
        self.prompt_use_count = dict()
        
        self.response_filter_count_of_all_domains = 0
        self.query_filter_count_of_all_domains = 0
        self.running_prompts_of_all_domains = 0
        self.prompt_use_count_of_all_domains = 0

        self.has_scaled_down = False 
        self.stop_second_half_servers = False
        # NOTE: metrics for judge scaling down
        self.judge_reward_working_scaling_down = False
        self.reward_worker_loads = []
        self.stop_all_servers = False
        self.infer_scaling_down_progress_ratio = self.pipeline_config.infer_scaling_down_progress_ratio 
        self.scaling_down_train_batch_size = self.pipeline_config.scaling_down_train_batch_size
        self.progress_profile = (self.pipeline_config.record_time_profiler_log_dir is not None)
        self.domains = dict()
        self.init_record_time()

        from tools.timer import Timer
        self.timer = Timer()

    def init_record_time(self, ):
        if self.progress_profile: 
            self.start_time = time.time() 
            self.record_time_list = list() 
    
    def set_scheduler(
        self,
        actor_cluster: Union[Any, Cluster],
        reward_clusters: Dict[str, Union[Any, Cluster]],
        domain2dataset: Dict[str, Dataset],
        collect_fn_cls,
        collect_fn_kwargs,
        response_filter_fn=None,
        query_filter_fn=None,
        response_callback_fn=None,
        state: Dict[str, Any] = None,
        migrate_callback_fn=None,
        pre_pass_query_filter_fn=None,
    ):
        """
        GenerateScheduler可以由多个实例，不再局限于单例
        """
        self.actor_cluster = actor_cluster
        self.reward_clusters = reward_clusters
        self.reward_worker_iters = {}
        for domain, cluster in reward_clusters.items():
            self.reward_worker_iters[domain] = itertools.cycle(cluster.workers)
            if domain == 'llm_judge':
                self.reward_worker_loads = [0] * len(cluster.workers)

        self.domain2dataset = domain2dataset
        self.domain2indices = {domain:list(range(len(dataset))) for domain, dataset in self.domain2dataset.items()}

        if state is not None and state.get("dataset_iter_count", 0) > 0:
            for _ in range(state["dataset_iter_count"]):
                self.get_next_dataset_item()

        self.collect_fn_cls = collect_fn_cls
        self.collect_fn_kwargs = collect_fn_kwargs
        self.tokenizer = default_tokenizer_provider(model_args=self.actor_cluster.worker_config.model_args)
        self.collect_fn = self.collect_fn_cls(tokenizer=self.tokenizer, **self.collect_fn_kwargs)

        if self.is_use_additional_prompts:
            self.response_filter_fn = response_filter_fn
            self.query_filter_fn = query_filter_fn
            self.pre_pass_query_filter_fn = pre_pass_query_filter_fn
        else:
            self.response_filter_fn = lambda data_list, config: True
            self.query_filter_fn = lambda data_list, config: True
            self.pre_pass_query_filter_fn = lambda data_list, config: True
            logger.info(f"use_additional_prompts is False, disable query and response filtering.")

        if not self.is_use_pre_pass_filter: 
            self.pre_pass_query_filter_fn = None
        
        self.response_callback_fn = response_callback_fn
        self.migrate_callback_fn = migrate_callback_fn
        dp_ranks: List[int] = [rank_info.dp_rank for rank_info in self.actor_cluster.worker_rank_info]
        self.dp_rank_to_global_ranks = dict()
        for i, dp_rank in enumerate(dp_ranks):
            rank_info = self.actor_cluster.get_rank_info(rank=i)
            if rank_info.tp_rank == 0 and rank_info.pp_rank == 0 and rank_info.cp_rank == 0:
                self.mp_rank_zero[dp_rank] = self.actor_cluster.workers[i]
                self.dp_rank_to_global_ranks[dp_rank] = rank_info.rank * self.pipeline_config.actor_infer.strategy_args.strategy_config.get('tensor_parallel_size', 1)
        print(f"self.mp_rank_zero is {self.mp_rank_zero}", flush=True)
        print(f"self.dp_rank_to_global_ranks is {self.dp_rank_to_global_ranks}", flush=True)

        self.request_counter = GlobalCounter.options(
            name=f"MultiDynamicSchedulerRequestCounter",
            get_if_exists=True,
            namespace=RAY_NAMESPACE,
        ).remote()
        self.domains = list(self.domain2dataset.keys())
        
        # used for prefetch
        self.number_of_prefetch_completed_prompts = 0
        self.max_number_of_preftch_completed_prompts = 0

    # NOTE: multi-tp rollout switch
    def reset_actor_cluster(self, actor_cluster: Union[Any, Cluster], tensor_parallel_size: int):
        self.actor_cluster = actor_cluster
        self.tokenizer = default_tokenizer_provider(model_args=self.actor_cluster.worker_config.model_args)
        dp_ranks: List[int] = [rank_info.dp_rank for rank_info in self.actor_cluster.worker_rank_info]
        self.mp_rank_zero = {}
        self.dp_rank_to_global_ranks = {}
        for i, dp_rank in enumerate(dp_ranks):
            rank_info = self.actor_cluster.get_rank_info(rank=i)
            if rank_info.tp_rank == 0 and rank_info.pp_rank == 0 and rank_info.cp_rank == 0:
                self.mp_rank_zero[dp_rank] = self.actor_cluster.workers[i]
                self.dp_rank_to_global_ranks[dp_rank] = rank_info.rank * tensor_parallel_size

    def reset_pipeline_config(self, pipeline_config):
        self.pipeline_config = pipeline_config

    def reset_status(self, batch_size=None):
        if batch_size: 
            self.batch_size_of_all_domains = batch_size
        # NOTE: {domain: {prompt_id: [finished requests]}}
        self.completed_buffers: Dict[int, List[DataProto]] = defaultdict(list)
        self.query_group_buffers: Dict[str, Dict[int, List[DataProto]]] = defaultdict(lambda: defaultdict(list))
        self.reward_times: Dict[int, List[DataProto]] = defaultdict(list)

        self.dp_fetch_count = {dp_rank: 0 for dp_rank in self.mp_rank_zero.keys()}
        self.load_balance_coordinator = {dp_rank: 0 for dp_rank in self.mp_rank_zero.keys()}
        self.request_id_2_prompt_id.clear()
        self.prompt_id_2_request_ids.clear()
        self.prompt_id_2_domain.clear()
        self.prompt_id_2_hash_str.clear()
        self.abort_request_ids.clear()
        self.request_id_2_dp_rank.clear()
        self.requests_buffers.clear()
        self.pre_pass_query_prompts.clear() 

        # modified for a multi-task generate scheduler
        self.response_filter_count = {domain:0 for domain in self.domain2dataset.keys()}
        self.query_filter_count = {domain:0 for domain in self.domain2dataset.keys()}
        self.running_prompts = {domain:0 for domain in self.domain2dataset.keys()}
        self.prompt_use_count = {domain:0 for domain in self.domain2dataset.keys()}

        self.response_filter_count_of_all_domains = 0
        self.query_filter_count_of_all_domains = 0
        self.running_prompts_of_all_domains = 0
        self.prompt_use_count_of_all_domains = 0

        self.response_cache = defaultdict(list)
        self.exception_queue = queue.Queue()
        bar_name = "-".join(self.reward_clusters.keys())
        self.progress_bar = tqdm(
            total=self.batch_size_of_all_domains,
            desc=f"{bar_name} generate progress(prompt)",
            mininterval=int(self.batch_size_of_all_domains * 0.1) + 1,
        )
        self.has_scaled_down = False
        self.num_finished_prompts = 0
        self.migrate_completion_ranks = dict()
        self.stop_second_half_servers = False 
        self.force_max_new_tokens = None
        self.prefetch_tags = defaultdict(bool)
        self.stop_all_servers = False
        self.disable_preftch_requests = False
        self.domain_counters = {d: 0 for d in self.domains}
        # NOTE: restore reward scaling metrics
        if 'llm_judge' in self.reward_clusters:
            judge_cluster = self.reward_clusters['llm_judge']
            self.reward_worker_loads = [0] * len(judge_cluster.workers)
            self.reward_worker_iters['llm_judge'] = itertools.cycle(judge_cluster.workers)
        self.judge_reward_working_scaling_down = False

        self.max_prompts_ratio = 1
        # avoid preftch all prompts 
        self.number_of_prefetch_completed_prompts = 0
        self.max_number_of_preftch_completed_prompts = self.batch_size_of_all_domains - self.pipeline_config.actor_train.world_size
        assert len(self.pipeline_config.first_half_ranks) + len(self.pipeline_config.second_half_ranks) > 0
        self.first_half_ranks = sorted([dp_rank for dp_rank, rank in self.dp_rank_to_global_ranks.items() if rank in self.pipeline_config.first_half_ranks])
        self.second_half_ranks = sorted([dp_rank for dp_rank, rank in self.dp_rank_to_global_ranks.items() if rank in self.pipeline_config.second_half_ranks])
        print(f"self.dp_rank_to_global_ranks is {self.dp_rank_to_global_ranks.values()}", flush=True)
        print(f"original ranks {self.pipeline_config.first_half_ranks}, {self.pipeline_config.second_half_ranks}", flush=True)
        print("self.mp_rank_zero.keys() {}, self.first_half_ranks {}, self.second_half_ranks {}".format(self.mp_rank_zero.keys(), self.first_half_ranks, self.second_half_ranks))
        print("[DEBUG] reset_status, first_half_ranks {}, second_half_ranks {}".format(self.first_half_ranks, self.second_half_ranks))
        if self.pipeline_config.autoscaling == True: 
            assert len(self.second_half_ranks) == len(self.first_half_ranks), f'the length of {self.first_half_ranks} and {self.second_half_ranks} should be equal.'


        # fake prefetch behavior 
        self.one_shot_prefetch_completed_requests_called_times = self.pipeline_config.scaling_down_train_batch_size
        self.indexes = 0 

    def _submit_request_with_allocate_dp(
        self, prompt_id, prompt_hash, 
        request_data_list, domain, first_half=False
    ):
        print(f"[get_batch_{domain}] submit start")

        dp_rank_requests_dict = defaultdict(list)
        length = len(self.load_balance_coordinator)
        # filter_keys = sorted(self.mp_rank_zero.keys())[:length//2] if first_half else sorted(self.mp_rank_zero.keys()) # deprecated
        filter_keys = sorted(self.first_half_ranks) if first_half else sorted(self.mp_rank_zero.keys())
        for req in request_data_list:
            # TODO: 这里需要写的优雅些，目前没有考虑yeild这里的排队实现，会导致死锁，需要平衡下submit的性能和排队的设计。
            dp_rank = sorted(
                filter_keys, 
                key=lambda rank: (self.load_balance_coordinator[rank], rank)
            )[0]
            request_id = ray.get(self.request_counter.get_value.remote())
            req.meta_info["request_id"] = f"{request_id}"
            req.meta_info["response_callback_fn"] = self.response_callback_fn
            self.request_id_2_prompt_id[req.meta_info["request_id"]] = prompt_id
            self.request_id_2_dp_rank[req.meta_info["request_id"]] = dp_rank
            self.prompt_id_2_request_ids[prompt_id].add(req.meta_info["request_id"])
            self.requests_buffers[req.meta_info["request_id"]] = req
            print(f"ABABABABBABABAB: {int(self.env_vars.get('REPORT_LENGTH_AND_REWARDS', '0'))}")
            if int(self.env_vars.get("REPORT_LENGTH_AND_REWARDS", "0")):
                self.prompt_id_2_hash_str[prompt_id] = prompt_hash
            # print(f"[get_batch_{domain}] submit {prompt_hash} request_id {request_id} to dp_rank {dp_rank}, {time.time()}")
            dp_rank_requests_dict[dp_rank].append(req)
            self.load_balance_coordinator[dp_rank] += 1
            self.dp_fetch_count[dp_rank] += 1
            rollout_start_time = time.time()
            self.timer.update_kv(str(request_id), "rollout_start_time", time.time())
            
        for dp_rank, data_list in dp_rank_requests_dict.items():
            self.actor_cluster.workers[dp_rank].add_batched_request.remote(
                command=GenerateRequestType.ADD, data_list=data_list
            )

    def get_batch(self, data: DataProto, batch_size_of_all_domains: int, first_half: bool=False, disable_stop_server: bool=False) -> DataProto:
        """
        从dataset里，按给定策略sample batch
        1. 常规无过滤
        2. 动态过滤
        """
        print(f"[get_batch] start, epoch {self.dataset_epoch}, {time.time()}")
        get_batch_start_time = time.time()
        self.batch_size_of_all_domains = batch_size_of_all_domains
        self.domain2batchsize = data.meta_info['domain2batchsize']
        self.reset_status(batch_size=self.batch_size_of_all_domains)
        
        print(f"self.max_number_of_preftch_completed_prompts {self.max_number_of_preftch_completed_prompts}, self.number_of_prefetch_completed_prompts {self.number_of_prefetch_completed_prompts}", flush=True)
        print(f"mp_rank_zero is {self.mp_rank_zero}, second ranks {self.second_half_ranks}", flush=True)
        self.running = True
        prompt_id_counter = itertools.count()
        self.generation_config = copy.deepcopy(data.meta_info["generation_config"])
        num_return_sequences = self.generation_config["num_return_sequences"]
        self.meta_info = data.meta_info

        # update the maximum number of prompts to prefetch: 
        self.max_number_of_preftch_completed_prompts = self.batch_size_of_all_domains - self.pipeline_config.actor_train.world_size
        # TODO: 写的优雅一点
        self.domain_running = defaultdict(int)

        # print(f"[DEBUG] Inside get batch")

        
        added_prompts_of_all_domains = 0
        self.fetch_long_prompts = (len(self.promp_hash_to_request_data.keys()) >= self.batch_size_of_all_domains)
        num_submit_sequences = self.pipeline_config.max_num_return_sequences if not self.fetch_long_prompts else num_return_sequences
        self.max_prompts_ratio = self.pipeline_config.max_prompts_ratio if not self.fetch_long_prompts else 1 

        prompts_to_submit = []
        
        iteration_submit_bs = np.sum([int(bs * self.max_prompts_ratio) for bs in self.domain2batchsize.values()]) if not self.fetch_long_prompts else self.batch_size_of_all_domains
        print("CATCH ME!", iteration_submit_bs)
        if self.fetch_long_prompts:
            prompts_to_submit = list(self.promp_hash_to_request_data.keys())[:iteration_submit_bs]
        random.shuffle(prompts_to_submit)

        # print(f"[DEBUG] HERERERE {self.fetch_long_prompts}, {self.promp_hash_to_request_data}")


        self.init_record_time()
        last_time = time.time()
        print_last_time = time.time()
        print_last_time2 = time.time()
        while True:
            with self.lock:
                if np.sum([
                    len(v) >= num_return_sequences for v in list(self.completed_buffers.values())[:]
                ]) == self.batch_size_of_all_domains:
                    self.running = False
                    print(f"[get_batch] finish, epoch {self.dataset_epoch}, {time.time()}")
                    prompt_ids = list(self.prompt_id_2_request_ids.keys())
                    for prompt_id in prompt_ids:
                        if prompt_id in self.prompt_id_2_request_ids:
                            request_ids = self.prompt_id_2_request_ids[prompt_id]
                            if len(request_ids) > 0:
                                self.abort_requests(request_ids, prompt_id)
                                del self.prompt_id_2_request_ids[prompt_id]
                    break
            # number_of_completed_requests = np.sum([
            #         len(v) >= num_return_sequences for v in list(self.completed_buffers.values())[:]
            #     ])

            self.check_worker_alive(self.actor_cluster, first_half=first_half)
            self.check_response_callback()
            
            request_data_list: List[DataProto] = []
            # print(f"self.num_finished_prompts == {self.num_finished_prompts}, int(self.batch_size_of_all_domains * self.infer_scaling_down_progress_ratio) {int(self.batch_size_of_all_domains * self.infer_scaling_down_progress_ratio)}", flush=True)
            if not self.has_scaled_down and self.infer_scaling_down_progress_ratio > 0 and \
                    self.num_finished_prompts >= int(self.batch_size_of_all_domains * self.infer_scaling_down_progress_ratio): 
                print('[DEBUG_get_batch] num_finished_prompts {}'.format(self.num_finished_prompts), flush=True)
                # sorted(self.mp_rank_zero.keys()) # you cannot use self.load_balance_coordinator to fetch dp_ranks, it will change during rollout stage
                # NOTE: 目前写死的直接砍半吗？
                # length = len(dp_ranks) // 2
                for dp_rank in self.second_half_ranks:
                    self.migrate_requests(request_id=None, dp_rank=dp_rank)
                    
                # self.actor_cluster.stop_server_second_half() 
                # TODO: clean up remaining things 
                # 1. wait for a signal: that all requests has been migrated to somewhere 
                # 2. we can stop this server
                # 3. signal main process half of servers has been completed 
                self.has_scaled_down = True
                first_half = True
                # TODO: offload reward cluster if colocate
                print(f"SCALE DOWN START {time.time()}")
                continue 
            
            # print("[DEBUG] HERERERE2, self.has_scaled_down {}, migrate_completion_ranks {}, mp_rank_zero {}".format(self.has_scaled_down, self.migrate_completion_ranks, len(self.mp_rank_zero)), flush=True)
            if self.has_scaled_down and (not self.stop_second_half_servers) and len(self.migrate_completion_ranks) == len(self.mp_rank_zero) // 2: 
                if False: #deprecated
                    dp_ranks = sorted(self.mp_rank_zero.keys())
                    length = len(dp_ranks) // 2
                    for dp_rank in dp_ranks[length:]: 
                        self.load_balance_coordinator.pop(dp_rank)
                else:
                    for dp_rank in self.second_half_ranks: 
                        self.load_balance_coordinator.pop(dp_rank)
                
                # TODO: 这里要看下multi_tp切换是否有问题
                self.actor_cluster.stop_server_second_half(_ranks=copy.deepcopy(self.second_half_ranks))
                with self.lock:
                    self.stop_second_half_servers = True
                    judge_domain = 'llm_judge'
                    if judge_domain in self.reward_clusters:
                        self.judge_reward_working_scaling_down = True
                        judge_cluster = self.reward_clusters[judge_domain]
                        self.reward_worker_iters[judge_domain] = itertools.cycle([w for i, w in enumerate(judge_cluster.workers) if i in self.pipeline_config.first_half_ranks])
            
            if self.judge_reward_working_scaling_down == True:
                # NOTE: check load to offload
                judge_cluster = self.reward_clusters[judge_domain]
                reward_workers_to_offload = [_rank for _rank in self.pipeline_config.second_half_ranks if self.reward_worker_loads[_rank] == 0]
                if len(reward_workers_to_offload) > 0:
                    judge_cluster.offload_states_with_ranks(_ranks=reward_workers_to_offload)
                    for _rank in reward_workers_to_offload:
                        self.reward_worker_loads[_rank] = -1
                    if all(self.reward_worker_loads[r] == -1 for r in self.pipeline_config.second_half_ranks):
                        self.judge_reward_working_scaling_down = False
            
            # print(f"[DEBUG] HERERERE3")

            if len(self.migrate_waiting_reqs) > 0: 
                while self.migrate_waiting_reqs:
                    dp_rank, _ = next(self.get_available_dp_rank(first_half=first_half))
                    with self.migrate_lock:
                        req = self.migrate_waiting_reqs.pop()
                    with self.lock:
                        # self.request_id_2_prompt_id[req.meta_info["request_id"]] = prompt_id
                        # NOTE: 如果没在的话就是abort掉了不用重新打上去
                        if req.meta_info["request_id"] in self.request_id_2_dp_rank:
                            self.request_id_2_dp_rank[req.meta_info["request_id"]] = dp_rank
                            # self.prompt_id_2_request_ids[prompt_id].add(req.meta_info["request_id"])  # 用于replica情况
                            self.requests_buffers[req.meta_info["request_id"]] = req
                            
                            self.actor_cluster.workers[dp_rank].add_request.remote(
                                command=GenerateRequestType.RESUME, data=req
                            )
                            req.meta_info.pop("response_callback_fn")
                            self.load_balance_coordinator[dp_rank] += 1
                            self.dp_fetch_count[dp_rank] += 1
                continue 
            
            # print(f"[DEBUG] HERERERE4")

            # NOTE: add requests for short iterations
            while added_prompts_of_all_domains < iteration_submit_bs:
                if self.fetch_long_prompts:
                    # TODO: check multi-domain logic
                    pass
                else:
                    dataset_item = self.get_next_dataset_item()
                    assert 'domain' in dataset_item
                    prompt_digest = hashlib.md5(dataset_item['domain'].encode() + dataset_item['prompt'].encode() + dataset_item['messages'].encode()).digest()
                    prompt_hash = base64.urlsafe_b64encode(prompt_digest).decode().rstrip('=')
                    domain = dataset_item.get("domain")
                    collect_data = self.collect_fn([dataset_item])
                    request_data: DataProto = DataProto.from_single_dict(collect_data, meta_info=data.meta_info)
                    assert prompt_hash not in self.promp_hash_to_request_data, f"[DUPLICATE HASH] {domain} with existing {self.promp_hash_to_request_data[prompt_hash].non_tensor_batch['domain'][0]}"
                    self.promp_hash_to_request_data[prompt_hash] = request_data
                    prompts_to_submit.append(prompt_hash)
                added_prompts_of_all_domains += 1
            
            # print(f"[DEBUG] HERERERE5 {len(prompts_to_submit)}")

            if len(prompts_to_submit) > 0:
                assert len(prompts_to_submit) == iteration_submit_bs, "Prompt to submit must equal to submit count!"
                with self.lock: 
                    for _ in range(iteration_submit_bs):
                        print(len(prompts_to_submit), iteration_submit_bs, _)
                        prompt_hash = prompts_to_submit[0]
                        prompts_to_submit.remove(prompt_hash)
                        request_data = self.promp_hash_to_request_data[prompt_hash] if not self.fetch_long_prompts else self.promp_hash_to_request_data.pop(prompt_hash)
                        prompt_id = next(prompt_id_counter)
                        assert "domain" in request_data.non_tensor_batch, "Domain information not in request data proto!"
                        domain = request_data.non_tensor_batch['domain'][0]
                        if self.domain_running[domain] == 0:
                            self.domain_running[domain] = self.domain2batchsize[domain]
                            print(f"[SET] {domain}, {self.domain_running[domain]}")
                        self.prompt_id_2_domain[prompt_id] = domain
                        print(f"[get_batch_{domain}] prompt: {prompt_hash}, resp_num: {num_submit_sequences}, time={time.time()}")
                        request_data_list = self.expand_requests(request_data, num_submit_sequences)
                        self.running_prompts_of_all_domains += 1
                        self.prompt_use_count_of_all_domains += 1
                        self.prompt_use_count[domain] += 1
                        self.running_prompts[domain] += 1
                        self._submit_request_with_allocate_dp(prompt_id, prompt_hash, request_data_list, domain, first_half)

        completed_buffers = {k: v for k, v in self.completed_buffers.items()}
        
        if self.progress_profile: 
            self.record_time_list.append(
                {
                    'event_type': 'start_post_process',
                    'duration': time.time() - self.start_time
                }
            )
        
        # 考虑到不同的 domain 的 shceduler 和 async autoscaling 各种复杂条件，这里考虑了不同情况触发条件 stop server;
        # 甚至在pipeline部分也有对应的触发条件 stop server
        # TODO: pipeline里面的stop server需要结合multi-tp修改
        print(f"[Finsih Get Batch] disable_stop_server {disable_stop_server}, stop_second_half_servers {self.stop_second_half_servers}, has_scaled_down {self.has_scaled_down}, first_half {first_half}", flush=True)
        if not disable_stop_server:
            if not first_half:
                print("stop all servers ", flush=True)
                self.actor_cluster.stop_server()
            else: 
                print("finish stop first half servers ", flush=True)
                self.actor_cluster.stop_server_first_half(_ranks=copy.deepcopy(self.first_half_ranks))
        
        if (not self.stop_second_half_servers) and (self.has_scaled_down): 
            if not disable_stop_server:
                print("finish stop second half servers ", flush=True)
                self.actor_cluster.stop_server_second_half(_ranks=copy.deepcopy(self.second_half_ranks))
            self.stop_second_half_servers = True
        
        print("="*40, flush=True)
        print("stop all servers ", flush=True)
        self.stop_all_servers = True 


        return_batch_size = self.batch_size_of_all_domains
        with self.post_process_lock: 
            completed_buffers = {k: v for k, v in self.completed_buffers.items() if len(v) > 0}
            if self.prefetch_tags is not None and len(self.prefetch_tags) > 0:
                completed_buffers = {k: v for k, v in self.completed_buffers.items() if len(v) > 0 and k not in self.prefetch_tags} # the remaining requests has been used to async training 
                return_batch_size = self.batch_size_of_all_domains - len(self.prefetch_tags)
            self.disable_preftch_requests = True
        

        # collect_data = [item for sublist in list(completed_buffers.values())[:] for item in sublist]
        collect_data = [item for _, sublist in sorted(completed_buffers.items()) for item in sublist]
        query_use_count = next(prompt_id_counter)
        logger.info(
            f"total collect data: {len(collect_data)}, collect queries: {len(completed_buffers)} "
            f"used queries: {query_use_count}  query_filter_count: {self.query_filter_count} "
            f"response_filter_count: {self.response_filter_count}"
        )
        # TODO: 这里 len(collect_data) > rollout_batch_size, 可以尝试动态扩大batch_size
        batch = DataProto.concat(collect_data[: return_batch_size * num_return_sequences])

        batch.meta_info.update({'metrics': {}})
        for domain in self.query_filter_count.keys(): 
            batch.meta_info["metrics"][domain] = {
                f"scheduler/query_filter_count": self.query_filter_count[domain],
                f"scheduler/response_filter_count": self.response_filter_count[domain],
                f"scheduler/collect_query_count": len(completed_buffers),
                f"scheduler/query_use_count": query_use_count,
            }

        # 统计全部response metrics
        metrics = {}
        for domain, response_batches in self.response_cache.items():
            response_batch = DataProto.concat(response_batches[:])
            sequence_score = response_batch.batch["scores"]
            metrics[domain] = dict()
            metrics[domain][f"scheduler/{domain}/score/mean"] = torch.mean(sequence_score).detach().item()
            metrics[domain][f"scheduler/{domain}/score/max"] = torch.max(sequence_score).detach().item()
            metrics[domain][f"scheduler/{domain}/score/min"] = torch.min(sequence_score).detach().item()



        batch.meta_info["metrics"].update(metrics)
        if self.progress_profile: 
            self.record_time_list.append(
                {
                    'event_type': 'finish_post_process',
                    'duration': time.time() - self.start_time
                }
            )

        get_batch_end_time = time.time()
        if False:
            # NOTE: move to pipeline async
            get_batch_time = {
                'start_time': get_batch_start_time,
                'end_time': get_batch_end_time,
                'duration': get_batch_end_time - get_batch_start_time,
                'long_iteration': bool(iteration_submit_bs == self.batch_size_of_all_domains)
            }
            get_batch_dir = os.path.join(self.pipeline_config.profiler_output_dir, "time")
            get_batch_dir = os.path.join(self.pipeline_config.profiler_output_dir, "get_batch")
            os.makedirs(get_batch_dir, exist_ok=True)
            filename = f"time-ep{self.dataset_epoch}.jsonl"
            get_batch_time_file = os.path.join(get_batch_dir, filename)
            with open(get_batch_time_file, "a") as f:
                f.write(json.dumps(get_batch_time) + "\n")
        if self.pipeline_config.fixed_async:
            batch.batch["prompt_id"] = torch.arange(batch.batch.batch_size[0], device=batch.batch.device)
            self.completed_batch_proto = batch
            self.tmp_completed_buffers = copy.deepcopy(self.completed_buffers)
        # import pdb; pdb.set_trace()
        print("step 2", flush=True)
        completed_buffers_in_prefetch = {k:v[:num_return_sequences] for (k, v) in sorted(self.completed_buffers.items()) if self.prefetch_tags[k]}
        collect_data_in_prefetch = [item for _, sublist in sorted(completed_buffers_in_prefetch.items()) for item in sublist]

        if len(collect_data_in_prefetch) == 0: 
            batch_in_prefetch = DataProto(meta_info={})
        else: 
            batch_in_prefetch = DataProto.concat(collect_data_in_prefetch)
        return batch, batch_in_prefetch, len(self.promp_hash_to_request_data.keys())

    @ray.method(concurrency_group="prefetch")
    def prefetch_completed_requests(self, running, kl_ctrl, prefetch_prompt_count=-1, div_multipler=0) -> List[DataProto]: 
        prefetch_time_start = time.time()
        print("self.disable_preftch_requests {}, not (self.stop_second_half_servers or self.stop_all_servers) {}".format(self.disable_preftch_requests, not (self.stop_second_half_servers or self.stop_all_servers)), flush=True)
        if self.disable_preftch_requests: 
            return DataProto(meta_info={'disable_preftch_requests': True})
        
        if not (self.stop_second_half_servers or self.stop_all_servers): # useless usually for this condition, just for aysnc stop server and prefetch
            return DataProto(meta_info={'disable_preftch_requests': False})

        if self.number_of_prefetch_completed_prompts >= self.max_number_of_preftch_completed_prompts:
            print(f"prefetch_completed_prompts {self.number_of_prefetch_completed_prompts} >= max_preftch_completed_prompts {self.max_number_of_preftch_completed_prompts}, return empty batch", flush=True)
            return DataProto(meta_info={'disable_preftch_requests': True})

        with self.post_process_lock:
            if self.progress_profile: 
                self.record_time_list.append(
                    {
                        'event_type': 'start_prefetch',
                        'duration': time.time() - self.start_time
                    }
                )
            num_return_sequences = self.generation_config["num_return_sequences"]
            completed_buffers_include_prefetch = {k:v[:num_return_sequences] for (k, v) in sorted(self.completed_buffers.items()) if len(v) >= num_return_sequences}
            total_valid_prompts = sum([len(v) >= num_return_sequences for v in completed_buffers_include_prefetch.values()])
            if self.batch_size_of_all_domains - total_valid_prompts <= 1: 
                return DataProto(meta_info={'disable_preftch_requests': True}) # give some time to post processing and reward computation

            if self.scaling_down_train_batch_size > 0:
                # 这里主要保证 在async autoscaling training 的时候使用一个prompt所有的response，
                # 并且在这个阶段把 #scaling_down_train_batch_size 的prompt 收集起来做部分训练。
                completed_buffers = dict() # used for async training data buffer
                cnt = 0
                indices_in_complete_batch = list()
                key_to_indices = dict()
                for idx, (k, v) in enumerate(sorted(completed_buffers_include_prefetch.items())):
                    if (k in self.prefetch_tags): continue
                    if cnt < self.scaling_down_train_batch_size and len(v) >= num_return_sequences:
                        key_to_indices[k] = list(range(idx*num_return_sequences,(idx+1)*num_return_sequences))
                        completed_buffers[k] = v[:num_return_sequences]
                        cnt += 1
                    if prefetch_prompt_count > 0 and cnt == prefetch_prompt_count: 
                        break

                    if cnt == self.scaling_down_train_batch_size: 
                        break
                
                while div_multipler > 0 and cnt % div_multipler > 0:
                    (key_to_remove, _) = next(iter(completed_buffers.items()))
                    completed_buffers.pop(key_to_remove)
                    key_to_indices.pop(key_to_remove)
                    cnt -= 1
            else: 
                raise NotImplementedError("Scaling down train batch size should be set to a positive value for async training data collection.")
                completed_buffers = {k: v[:num_return_sequences] for k, v in self.completed_buffers.items() if len(v) >= num_return_sequences}

                
            print("length of completed_buffers ", len(completed_buffers), flush=True)
            print("self.num_finished_prompts == ", self.num_finished_prompts, flush=True)
            print("div_multipler == ", div_multipler, flush=True)
            # collect_data = [item for sublist in list(completed_buffers.values())[:] for item in sublist] # Fixed order
            collect_data = [item for _, sublist in sorted(completed_buffers.items()) for item in sublist]
            # self.prefetch_tags = {k: True for k, v in completed_buffers.items() if len(v) > 0}
            self.prefetch_tags.update({k: True for k, v in completed_buffers.items() if len(v) > 0})
            
            # TODO: 这里 len(collect_data) > rollout_batch_size, 可以尝试动态扩大batch_size
            self.number_of_prefetch_completed_prompts += len(completed_buffers)
            print('length of collect_data {}, total prefetch prompts {}, valid prompts {}'.format(len(collect_data), self.number_of_prefetch_completed_prompts, total_valid_prompts), flush=True)
            if len(collect_data) == 0: 
                return DataProto(meta_info={'disable_preftch_requests': False}) # FIXME: it should be false, we can continue prefetch the requests


            
            
            if self.progress_profile: 
                self.record_time_list.append(
                    {
                        'event_type': 'finish_prefetch',
                        'duration': time.time() - self.start_time
                    }
                )
            if True:
                completed_buffers = completed_buffers_include_prefetch
                # collect_data = [item for sublist in list(completed_buffers.values())[:] for item in sublist] # fixed order 
                collect_data = [item for _, sublist in sorted(completed_buffers.items()) for item in sublist]
                return_batch_size = self.batch_size_of_all_domains

                
                collect_data_size = min(return_batch_size * num_return_sequences, len(collect_data))
                batch = DataProto.concat(collect_data[:collect_data_size])
                indices = list()
                for key, value in sorted(key_to_indices.items()): indices.extend(value)
                batch.meta_info["indices"] = indices
                prefetch_batch = batch
            
        return prefetch_batch


    @ray.method(concurrency_group="multi_thread")
    def one_shot_prefetch_completed_requests(self, running, kl_ctrl, prefetch_prompt_count=-1, div_multipler=0, ) -> List[DataProto]: 
        if self.one_shot_prefetch_completed_requests_called_times <= self.indexes:
            return DataProto(meta_info={'disable_preftch_requests': True})
        index = self.indexes
        self.one_shot_prefetch_completed_requests_called_times
        num_return_sequences = self.generation_config["num_return_sequences"]
        self.indexes += self.pipeline_config.oneshot_prompt_count


        completed_buffers = {k: v[:num_return_sequences] for k, v in self.tmp_completed_buffers.items() if len(v) >= num_return_sequences}
        
        # collect_data = [item for sublist in list(completed_buffers.values())[:] for item in sublist]
        collect_data = [item for _, sublist in sorted(completed_buffers.items()) for item in sublist]
        return_batch_size = self.batch_size_of_all_domains

        
        collect_data_size = min(return_batch_size * num_return_sequences, len(collect_data))
        batch = DataProto.concat(collect_data[:collect_data_size])
        batch.batch["prompt_id"] = torch.arange(batch.batch.batch_size[0], device=batch.batch.device)

        tok_len = batch.batch['response_mask'].size(1)
        batch.batch["old_log_probs"] = torch.randn((batch.batch.size(0), tok_len-1))
        batch.batch['ref_log_probs'] = batch.batch["old_log_probs"]

        
        if False: 
            async_batch_data = torch.load('train_async_batch.pt', weights_only=False)
            batch_data = batch_with_rewards
            for key in batch_data.batch.keys(): 
                if key in ['prompt_mask', 'difficulty_mask', 'old_log_probs', 'ref_log_probs']: continue 
                if key in batch_data.batch and key in async_batch_data: 
                    current_scores = batch_data.batch[key]
                    main_scores = async_batch_data[key]
                    if (current_scores - main_scores).sum().item() > 0.1:
                        print("key is ", key, flush=True)
                        print("diff is {}".format((current_scores - main_scores).sum().item()), flush=True)
                        import pdb; pdb.set_trace()
        if self.pipeline_config.autoscaling_reward_method in ['local']: 
            indices = list(range(index * num_return_sequences,(index+self.pipeline_config.oneshot_prompt_count)*num_return_sequences))
            batch_with_rewards = batch.select_idxs(indices)
            selected_batch_with_rewards = batch_compute_rewards(batch=batch_with_rewards, pipeline_config=self.pipeline_config, running=running, kl_ctrl=kl_ctrl)
            selected_batch = self.completed_batch_proto[index * num_return_sequences:(index+self.pipeline_config.oneshot_prompt_count)*num_return_sequences]
        else: 
            batch_with_rewards = batch_compute_rewards(batch=batch, pipeline_config=self.pipeline_config, running=running, kl_ctrl=kl_ctrl)
            selected_batch = self.completed_batch_proto[index * num_return_sequences:(index+self.pipeline_config.oneshot_prompt_count)*num_return_sequences]
            indices = selected_batch.batch["prompt_id"].tolist()
            selected_batch_with_rewards = batch_with_rewards.select_idxs(indices)

        for key in selected_batch_with_rewards.batch.keys():
            if key not in selected_batch.batch: 
                selected_batch.batch[key] = selected_batch_with_rewards.batch[key]
            elif key in ['token_level_rewards']: 
                selected_batch.batch[key] = selected_batch_with_rewards.batch[key]
            # print((selected_batch.batch['input_ids'] - selected_batch_with_rewards.batch['input_ids']).sum())
        # import pdb; pdb.set_trace()
        assert (selected_batch.batch['input_ids'] - selected_batch_with_rewards.batch['input_ids']).sum().item() == 0
        return selected_batch
        
        

    @ray.method(concurrency_group="multi_thread")
    def can_prefetch_requests(self): 
        # return self.has_scaled_down
        print(f"[CHECK CAN PREFETCH REQUESTS SCHEDULER {self.has_scaled_down}] self.stop_second_half_servers: {self.stop_second_half_servers}, self.judge_reward_working_scaling_down: {self.judge_reward_working_scaling_down}, self.stop_all_servers: {self.stop_all_servers}")
        return (self.stop_second_half_servers and not self.judge_reward_working_scaling_down) or self.stop_all_servers


    def migrate_requests(self, request_id: str, dp_rank:int = -1): 
        with self.lock: 
            if dp_rank >= 0: 
                # pop_request_ids = [request_id for request_id, rank in self.request_id_2_dp_rank.items() if rank == dp_rank]
                # for request_id in pop_request_ids:
                #     self.request_id_2_dp_rank.pop(request_id, None)
                print(f"starting migrate dp rank {dp_rank}", flush=True)
                ray.get(
                    self.actor_cluster.workers[dp_rank].add_request.remote(
                        command=GenerateRequestType.MIGRATE_ALL, data=DataProto(meta_info={"migrate_callback_fn": self.migrate_callback_fn, "dp_rank": dp_rank, "request_id": None})
                    )
                )
            # NOTE: 暂时没用到不过如果用的话考虑一下abort
            else: 
                # dp_rank = self.request_id_2_dp_rank[request_id]
                # FIXME: gw to fix bug in report_response@self.load_balance_coordinator[self.request_id_2_dp_rank[request_id]] -= 1
                self.request_id_2_dp_rank.pop(request_id, None)
                ray.get(
                    self.actor_cluster.workers[dp_rank].add_request.remote(
                        command=GenerateRequestType.MIGRATE, data=DataProto(meta_info={"request_id": request_id, "migrate_callback_fn": self.migrate_callback_fn, "dp_rank": -1})
                    )
                )
    
    @ray.method(concurrency_group="multi_thread")
    def migrate_response(self, data: List, dp_rank:int, request_id: str):
        if dp_rank == -1: # not migrate all requests from a single device
            raise NotImplementedError
        else: # migrate all requests in device `dp_rank`
            with self.migrate_lock:
                if self.progress_profile: 
                    self.record_time_list.append(
                        {
                            'event_type': 'start_migration',
                            'duration': time.time() - self.start_time
                        }
                    )
                for req in data: 
                    if isinstance(req, DataProto): 
                        self.migrate_waiting_reqs.append(data)
                    elif isinstance(req, dict):
                        has_generated_tokens = len(req['token_ids']) - req['prompt_length']
                        request_id = req['request_id']
                        ori_request: DataProto = self.requests_buffers.pop(request_id)
                        collect_data = {
                            "input_ids": torch.tensor([req['token_ids']], dtype=torch.int32),
                            "trim_ids": torch.tensor([req['prompt_token_ids']], dtype=torch.int32), # FIXME: @gaowei 
                            "padded_trim_ids": ori_request.batch['input_ids'],
                            "trim_attention_mask": ori_request.batch['attention_mask'],
                            "position_ids": ori_request.batch['position_ids'],
                        }
                        meta_info = copy.deepcopy(self.meta_info)
                        gen_config = copy.deepcopy(self.generation_config)
                        gen_config.update({"num_return_sequences":1})
                        meta_info.update({
                            "request_id": request_id, 
                            "generation_config": gen_config,  # key step, update num_return_sequences
                            "max_new_tokens": (self.generation_config['max_new_tokens'] if self.force_max_new_tokens is None else self.force_max_new_tokens) -  has_generated_tokens, # for debug 
                            "response_callback_fn": self.response_callback_fn,
                        })
                        new_req = DataProto.from_single_dict(collect_data, meta_info=meta_info)
                        new_req.non_tensor_batch = ori_request.non_tensor_batch
                        self.migrate_waiting_reqs.append(new_req)
                    else: 
                        raise NotImplementedError
                self.migrate_completion_ranks[dp_rank] = True 
                print("length of migrate responses is {}".format(len(self.migrate_waiting_reqs), flush=True))
                print(f"complete rank migration {dp_rank}", flush=True)

                if self.progress_profile: 
                    self.record_time_list.append(
                        {
                            'event_type': 'finish_migration',
                            'duration': time.time() - self.start_time
                        }
                    )


    def reload_balance(self, first_half=False):
        length = len(self.mp_rank_zero)
        
        # filter_keys = sorted(self.mp_rank_zero.keys())[:length//2] if first_half else sorted(self.mp_rank_zero.keys()) # deprecated 
        filter_keys = sorted(self.first_half_ranks) if first_half else sorted(self.mp_rank_zero.keys())
        new_load_balance_coordinator = {key:self.load_balance_coordinator[key] for key in filter_keys}
        if max(new_load_balance_coordinator.values()) < 4: 
            return 
        while True:
            max_dp_rank = max(new_load_balance_coordinator, key=lambda k: new_load_balance_coordinator[k])
            min_dp_rank = min(new_load_balance_coordinator, key=lambda k: new_load_balance_coordinator[k])
            if new_load_balance_coordinator[max_dp_rank] < 1.4 * new_load_balance_coordinator[min_dp_rank]: 
                break
            max_request_ids, min_request_ids = list(), list()

            for request_id, dp_rank in self.request_id_2_dp_rank.items(): 
                if dp_rank == max_dp_rank: max_request_ids.append(request_id)
            
            assert len(max_request_ids) == new_load_balance_coordinator[max_dp_rank], 'the length should be equal'
            migrate_cnt = (new_load_balance_coordinator[max_dp_rank] - new_load_balance_coordinator[min_dp_rank]) / 2
            for i in range(migrate_cnt):
                request_id = max_request_ids[i]
                self.actor_cluster.workers[max_dp_rank].add_request.remote(
                    command=GenerateRequestType.MIGRATE, data=DataProto(meta_info={"request_id": request_id, "migrate_callback_fn": self.migrate_callback_fn, "dp_rank": -1})
                )
            break


    @ray.method(concurrency_group="multi_thread")
    def report_response(self, data: DataProto):
        """
        这里需要考虑多线程数据访问
        data 返回可能有多条的
        """

        try:
            rollout_end_time = time.time()
            request_id = data.meta_info["request_id"]
            prompt_id = self.request_id_2_prompt_id.pop(request_id)
            num_return_sequences = self.generation_config["num_return_sequences"]

            batch = self.postprocess_output_ids(data)
            output_count = batch.batch.batch_size[0]
            reward_rank = None
            with self.lock:
                if prompt_id in self.prompt_id_2_request_ids:
                    if request_id in self.prompt_id_2_request_ids[prompt_id]:
                        self.prompt_id_2_request_ids[prompt_id].remove(request_id)
                    # FIXME: 这里是不是做的更优雅检查退出？反正全128会有结束了prompt已经被删掉的
                if request_id not in self.request_id_2_dp_rank:
                    # NOTE: 已经abort了
                    print(f"RESPONSE {request_id} ALREADY ABORTED!!! {prompt_id}")
                    return
                if self.request_id_2_dp_rank[request_id] not in self.load_balance_coordinator: 
                    print("request_id original dp_rank {} not in load balance coordinator, skip in {}".format(self.request_id_2_dp_rank[request_id], self.load_balance_coordinator), flush=True)
                
                if self.request_id_2_dp_rank[request_id] in self.load_balance_coordinator:
                    self.load_balance_coordinator[self.request_id_2_dp_rank[request_id]] -= 1
                domain = "default"
                if "domain" in batch.non_tensor_batch.keys():
                    domain = batch.non_tensor_batch["domain"][0]
                reward_worker = next(self.reward_worker_iters[domain])
                if domain == "llm_judge":
                    reward_rank = ray.get(reward_worker.get_rank_info.remote()).rank
                    self.reward_worker_loads[reward_rank] += 1
            if domain == 'llm_judge':
                print(f"[fin_rollout] {domain}, {self.domain_running} request_id {request_id} in {time.time()}, reward_rank: {reward_rank}")
            else:
                print(f"[fin_rollout] {domain}-{prompt_id}, {self.domain_running} request_id {request_id} in {time.time()}")
            if not self.running or self.domain_running[domain] == 0:
                return

            # call reward
            # reward worker得能支持单条数据计算, dynamic sampling对需要batch计算reward的需要注意...
            # 多域的时候,llm as judge, 需要单独为reward worker分配gpu
            rewards_start = time.time()
            origin_prompt_id = batch.non_tensor_batch["id"]
            logger.info(f"[TIMER][invoke_reward_compute][request_id={request_id}][origin_prompt_id={origin_prompt_id}][time={time.time()}]")
            # self.timer.update_timestamp(request_id, origin_prompt_id[0], "invoke_reward_compute", time.time())
            # self.timer.update_kv(request_id, "domain", domain)
            if domain == "code_sandbox":
                timeout = 0
                rewards = None
                try:
                    reference_time = FixedTimeOut
                    if os.environ.get("ADAPTIVE_TIMEOUT", "0") == "1" and "reference_time" in batch.non_tensor_batch.keys():
                        reference_time = max(batch.non_tensor_batch["reference_time"])
                    timeout = min(max(2 * reference_time, 2), FixedTimeOut) + 10
                    rewards: DataProto = ray.get(reward_worker.compute_rewards.remote(batch), timeout=timeout)
                except Exception as e:
                    token_level_rewards = torch.zeros_like(batch.batch["responses"], dtype=torch.float16)
                    response_level_rewards = torch.zeros(len(batch.non_tensor_batch["id"]), dtype=torch.float16)
                    scores = torch.zeros(len(batch.non_tensor_batch["id"]), dtype=torch.float16)

                    rewards = DataProto.from_dict(
                        tensors={
                            "token_level_rewards": token_level_rewards,
                            "response_level_rewards": response_level_rewards,
                            "scores": scores
                        }
                    )
                    rewards.meta_info = {"worker_name": "None"}
            else:
                rewards: DataProto = ray.get(reward_worker.compute_rewards.remote(batch))
            batch.union(rewards)
            rewards_end = time.time()

            response_buffers: List[DataProto] = []
            batch_expanded = [batch[[idx]] for idx in range(output_count)]

            # response_filter, 不太需要response filter
            for batch_item in batch_expanded:
                if self.response_filter_fn(batch_item, self.pipeline_config):
                    response_buffers.append(batch_item)
                else:
                    self.response_filter_count += 1

            with self.lock:
                if domain != 'math_rule':
                    self.timer.update_timestamp(request_id, origin_prompt_id[0], "invoke_reward_compute", rewards_start)
                    self.timer.update_timestamp(request_id, origin_prompt_id[0], "get_reward", rewards_end)
                    # tensor不能被json序列化，先转成python标量
                    self.timer.update_kv(request_id, "start_compute_reward", rewards.batch["start_compute_reward_list"][0].item() if hasattr(rewards.batch["start_compute_reward_list"][0], "item") else rewards.batch["start_compute_reward_list"][0])
                    self.timer.update_kv(request_id, "end_compute_reward", rewards.batch["end_compute_reward_list"][0].item() if hasattr(rewards.batch["end_compute_reward_list"][0], "item") else rewards.batch["end_compute_reward_list"][0])
                    self.timer.update_kv(request_id, "reward_score", rewards.batch["reward_score_list"][0].item() if hasattr(rewards.batch["reward_score_list"][0], "item") else rewards.batch["reward_score_list"][0])
                    self.timer.update_kv(request_id, "test_cases_length", rewards.batch["test_cases_list"][0].item() if hasattr(rewards.batch["test_cases_list"][0], "item") else rewards.batch["test_cases_list"][0])
                    self.timer.update_kv(request_id, "rollout_end_time", rollout_end_time)
                    self.timer.update_kv(request_id, "worker_name", rewards.meta_info["worker_name"])
                    # self.timer.update_kv(request_id, "start_time_inference", rewards.batch["start_time_inference_list"][0].item() if hasattr(rewards.batch["start_time_inference_list"][0], "item") else rewards.batch["start_time_inference_list"][0])
                    # self.timer.update_kv(request_id, "end_time_inference", rewards.batch["end_time_inference_list"][0].item() if hasattr(rewards.batch["end_time_inference_list"][0], "item") else rewards.batch["end_time_inference_list"][0])

                if reward_rank is not None:
                    self.reward_worker_loads[reward_rank] -= 1
                self.response_cache[domain].extend(batch_expanded)

                if len(response_buffers) == 0:
                    # NOTE: 全filter，这个response level 的 filter貌似还不太完善这里其实不会被调用
                    if len(self.prompt_id_2_request_ids[prompt_id]) == 0:
                        self.running_prompts_of_all_domains -= 1
                        self.running_prompts[domain] -= 1
                        prompt_hash = self.prompt_id_2_hash_str.pop(prompt_id)
                        if prompt_hash in self.promp_hash_to_request_data:
                            self.promp_hash_to_request_data.pop(prompt_hash)
                    return

                if len(self.completed_buffers[prompt_id]) >= num_return_sequences:
                    return

                # expand batch to response
                self.query_group_buffers[domain][prompt_id].extend(response_buffers)
                self.reward_times[prompt_id].append(rewards_end - rewards_start)

                # query_filter, query has n responses
                response_count = len(self.query_group_buffers[domain][prompt_id])
                if response_count == num_return_sequences:

                    if not self.running or self.domain_running[domain] == 0:
                        return

                    self.domain_running[domain] -= 1


                    if not self.query_filter_fn(self.query_group_buffers[domain][prompt_id], self.pipeline_config):
                        self.query_filter_count_of_all_domains += 1
                        self.query_filter_count[domain] += 1
                        del self.query_group_buffers[domain][prompt_id]
                        self.abort_requests(self.prompt_id_2_request_ids[prompt_id], prompt_id)
                        del self.prompt_id_2_request_ids[prompt_id]
                        return
                    
                    assert len(self.query_group_buffers[domain][prompt_id]) >= num_return_sequences, (
                        f"expect to generate {num_return_sequences} results from one prompt, "
                        f"but get {len(self.query_group_buffers[domain][prompt_id])}."
                    )

                    dropped = False
                    if np.sum([
                        len(v) >= num_return_sequences for v in list(self.completed_buffers.values())[:]
                    ]) < self.batch_size_of_all_domains:
                        self.completed_buffers[prompt_id].extend(
                            self.query_group_buffers[domain][prompt_id][:num_return_sequences]
                        )
                    else:
                        dropped = True
                    
                    print(f"ABORT RESPONSES: {prompt_id} {self.prompt_id_2_request_ids[prompt_id]}")
                    self.abort_requests(self.prompt_id_2_request_ids[prompt_id], prompt_id)
                    del self.prompt_id_2_request_ids[prompt_id]
                    
                    self.progress_bar.update()
                    self.num_finished_prompts += 1
                    print("[report_response] prompt_id {}, domain {}, num_finished_prompts {}, running_prompts_of_all_domains {}, time {}".format(
                        prompt_id, domain, self.num_finished_prompts, self.running_prompts_of_all_domains, time.time()
                    ), flush=True)
                    
                    if prompt_id in self.prompt_id_2_hash_str:
                        prompt_hash = self.prompt_id_2_hash_str.pop(prompt_id)
                        if prompt_hash in self.promp_hash_to_request_data and not dropped:
                            self.promp_hash_to_request_data.pop(prompt_hash)
                        if int(self.env_vars.get("REPORT_LENGTH_AND_REWARDS", "0")) and not dropped:
                            # report response level rewards
                            response_level_rewards = [data.batch["response_level_rewards"] for data in self.query_group_buffers[domain][prompt_id]]
                            response_rewards = torch.cat(response_level_rewards, dim=0).long().cpu().tolist()
                            prompt_response_proto = DataProto.concat(self.query_group_buffers[domain][prompt_id][:num_return_sequences])
                            # report response level lengths
                            response_lengths = torch.sum(prompt_response_proto.batch["response_mask"], dim=1).cpu().tolist()

                            print(f"[report_response_{domain}] prompt {prompt_hash}, finish rollout, {time.time()}")
                            print(f"[report_response] max_length: {np.max(response_lengths)}")
                            lengths_and_rewards = {
                                'domain': domain,
                                'prompt_hash': prompt_hash,
                                'response_lengths': response_lengths,
                                'response_rewards': response_rewards,
                                'rewards_times': self.reward_times[prompt_id],
                                'unfinished_prompts': len(self.promp_hash_to_request_data.keys()),
                                'long_iteration': self.fetch_long_prompts
                            }
                            self.reward_times[prompt_id] = []
                            length_dir = os.path.join(self.pipeline_config.profiler_output_dir, "length")
                            os.makedirs(length_dir, exist_ok=True)
                            print(f"report log here!!!, {length_dir}")
                            filename = f"response-length-and-rewards-ep{self.dataset_epoch}.jsonl"
                            length_file_path = os.path.join(length_dir, filename)
                            with open(length_file_path, "a") as f:
                                f.write(json.dumps(lengths_and_rewards) + "\n")

                    if self.progress_profile and hasattr(self, "record_time_list") and prompt_id in self.prompt_id_2_hash_str: # FIXME: later 
                        _prompt_response_proto = DataProto.concat(self.query_group_buffers[domain][prompt_id])
                        _response_mask = _prompt_response_proto.batch["response_mask"]
                        _total_lengths = torch.sum(_response_mask, dim=1).cpu().tolist()
                        _prompt_hash = self.prompt_id_2_hash_str.pop(prompt_id)
                        self.record_time_list.append(
                            {
                                "prompt_id": prompt_id,
                                "start_time": self.start_time,
                                "end_time": time.time(),
                                "duration": time.time() - self.start_time,
                                "domain": domain, 
                                "prompt_hash": _prompt_hash, 
                                "dataset_epoch": self.dataset_epoch, 
                                "total_lengths": _total_lengths
                            }
                        )
                    
        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            logger.info(f"Exception in report_response: {e}\nTraceback:\n{tb_str}")
            self.exception_queue.put(e)


    def get_record_time_list(self):
        """
        获取record time list
        """
        if hasattr(self, "record_time_list"):
            return self.record_time_list
        else:
            return None


    def get_next_dataset_item(self):
        import random

        # 初始化 domains 和当前计数器
        if not hasattr(self, 'domain_counters'):
            self.domain_counters = {d: 0 for d in self.domains}
        
        if not hasattr(self, 'domain_iters'):
            self.domain_iters = {d: None for d in self.domains}
        
        if not hasattr(self, 'domain_epochs'):
            self.domain_epochs = {d: 0 for d in self.domains}

        while True:
            # 动态选择下一个要取样的 domain（优先那些还没达到 batch size 的）
            available_domains = [
                d for d in self.domains 
                if self.domain_counters[d] < self.domain2batchsize[d] * self.max_prompts_ratio
            ]
            random.shuffle(available_domains)
            if not available_domains:
                # 所有 domain 都已经取满，重置 counters
                self.domain_counters = {d: 0 for d in self.domains}

            # 循环尝试获取样本
            for domain in available_domains:
                dataset = self.domain2dataset[domain]

                # 如果当前 domain 的 iter 是空的，重新初始化
                if self.domain_iters[domain] is None:
                    seed = self.pipeline_config.seed + self.domain_epochs[domain]
                    random.seed(seed)
                    indices = list(range(len(dataset)))
                    random.shuffle(indices)
                    self.domain_iters[domain] = iter(indices)
                    self.domain_epochs[domain] += 1
                    logger.info(f"{domain} dataset epoch: {self.domain_epochs[domain]}")

                try:
                    idx = next(self.domain_iters[domain])
                    self.domain_counters[domain] += 1
                    return dataset[idx]
                except StopIteration:
                    self.domain_iters[domain] = None
                    # TODO: maintain epoch of each domain seperately, perhaps in a dict
                

    def get_scheduler_state(self):
        return {"dataset_iter_count": self.dataset_iter_count}


    def abort_requests(self, request_ids: Set[str], prompt_id: int):
        abort_refs = []
        self.running_prompts_of_all_domains -= 1
        domain = self.prompt_id_2_domain[prompt_id]
        self.running_prompts[domain] -= 1

        for request_id in request_ids:
            dp_rank = self.request_id_2_dp_rank.pop(request_id)
            # NOTE: 如果不在就说明已经在migrate list里面了，不需要打ABORT，修改tag就可以了
            if dp_rank in self.load_balance_coordinator:
                self.load_balance_coordinator[dp_rank] -= 1
                abort_refs.append(
                    self.actor_cluster.workers[dp_rank].add_request.remote(
                        command=GenerateRequestType.ABORT, data=DataProto(meta_info={"request_id": request_id})
                    )
                )



    def postprocess_output_ids(self, data: DataProto) -> DataProto:
        # postprocess_generate, input_ids, attention_mask, left pad
        request_id = data.meta_info["request_id"]
        request: DataProto = self.requests_buffers.pop(request_id)
        eos_token_id = data.meta_info["eos_token_id"]
        pad_token_id = data.meta_info["pad_token_id"]
        output_token_ids = data.meta_info["output_token_ids"]
        if 'trim_ids' in request.batch: 
            assert 'padded_trim_ids' in request.batch
            input_ids = request.batch['input_ids'].tolist() 
            trim_ids = request.batch['trim_ids'].tolist()
            previous_round_output_token_ids = [input_id[len(trim_id):] for trim_id, input_id in zip(trim_ids, input_ids)]
            request.batch['input_ids'] = request.batch['padded_trim_ids']
            request.batch['attention_mask'] = request.batch['trim_attention_mask']
            assert len(output_token_ids) == len(previous_round_output_token_ids), '{} {} mismatch in postprocess_output_ids'.format(len(output_token_ids), len(previous_round_output_token_ids))
            # print("post process output_token_ids is {}".format(output_token_ids))
            output_tokens = [torch.tensor(prev_token_ids+list(token_ids)) for prev_token_ids, token_ids in zip(previous_round_output_token_ids, output_token_ids)]
        else: 
            output_tokens = [torch.tensor(token_ids) for token_ids in output_token_ids]
        
        output_tensor = pad_sequence(output_tokens, batch_first=True, padding_value=pad_token_id)
        output_tensor = concatenate_input_and_output(
            input_ids=request.batch["input_ids"], output_ids=output_tensor, num_return_sequences=len(output_tokens)
        )
        output: DataProto = postprocess_generate(
            prompts=request,
            output=output_tensor,
            num_return_sequences=len(output_tokens),
            sequence_length=self.pipeline_config.sequence_length,
            eos_token_id=eos_token_id,
            pad_token_id=pad_token_id,
        )
        request_repeat = request.repeat(repeat_times=len(output_tokens))
        output.non_tensor_batch = request_repeat.non_tensor_batch
        output.meta_info = request_repeat.meta_info
        return output


    def expand_requests(
        self, data: DataProto, 
        generation_num: Optional[int] = None
    ) -> List[DataProto]:
        """
        replica, 以及redundancy
        """
        generate_opt_level = self.pipeline_config.generate_opt_level
        is_num_return_sequences_expand = self.pipeline_config.is_num_return_sequences_expand
        generation_num = self.generation_config["num_return_sequences"] if not generation_num else generation_num

        assert generate_opt_level > 0, (
            f"generate_opt_level {generate_opt_level} should > 0, " f"in dynamic sampling scheduler."
        )
        assert "generation_config" in data.meta_info, f"data {data.meta_info} should have key 'generation_config'"
        # generation_config = data.meta_info["generation_config"]

        target_requests = []
        if is_num_return_sequences_expand:
            # expand enables to process with response level
            data.meta_info["generation_config"]["num_return_sequences"] = 1
            for _ in range(generation_num):
                target_requests.append(copy.deepcopy(data))
        else:
            data.meta_info["generation_config"]["num_return_sequences"] = generation_num
            target_requests.append(copy.deepcopy(data))
        return target_requests

    def check_worker_alive(self, cluster, first_half: bool = False):
        # 探测dp worker是否存活，dp worker的server thread可能由于异常退出，造成hang
        current_time = time.time()
        if current_time - self.last_alive_check >= self.alive_check_interval:
            if not first_half:
                cluster.add_request(command=GenerateRequestType.ALIVE_CHECK, data=DataProto())
            else: 
                cluster.add_request_first_half(
                    command=GenerateRequestType.ALIVE_CHECK, data=DataProto(), _ranks=copy.deepcopy(self.first_half_ranks)
                )
            self.last_alive_check = current_time

    def check_response_callback(self):
        if self.exception_queue.qsize() > 0:
            e = self.exception_queue.get()
            logger.error(f"report_response get exception {e}")
            raise e

    def check_send_new_request(self) -> bool:
        if self.running_prompts_of_all_domains >= (self.batch_size_of_all_domains + self.max_additional_running_prompts):
            return False
        if not self.is_use_additional_prompts and self.prompt_use_count_of_all_domains >= self.batch_size_of_all_domains:
            return False
        return True

    def get_available_dp_rank(self, first_half: bool = False):
        length = len(self.mp_rank_zero)
        # filter_keys = sorted(self.mp_rank_zero.keys())[:length//2] if first_half else sorted(self.mp_rank_zero.keys())
        filter_keys = sorted(self.first_half_ranks) if first_half else sorted(self.mp_rank_zero.keys())
        while True:
            # 负载均衡逻辑，期望各dp 正在处理的条数基本接近
            sorted_ranks = sorted(filter_keys
                , key=lambda rank: (self.load_balance_coordinator[rank], rank)
            )
            # print(f"sorted_ranks is {sorted_ranks}, self.load_balance_coordinator {self.load_balance_coordinator}, first_half {first_half}", flush=True)
            # if sorted_ranks[0] not in self.load_balance_coordinator: 
            #     print(f"sorted_ranks[0] is {sorted_ranks[0]}, self.load_balance_coordinator {self.load_balance_coordinator}, first_half {first_half}", flush=True)
            if self.load_balance_coordinator[sorted_ranks[0]] < self.max_running_requests:
                yield sorted_ranks[0], self.max_running_requests - self.load_balance_coordinator[sorted_ranks[0]]
    
    def reset_autoscaling_scaling_down_progress_ratio(self, scaling_down_progress_ratio): 
        self.infer_scaling_down_progress_ratio = scaling_down_progress_ratio

    def get_timer(self):
        return self.timer

    def clear_timer(self):
        self.timer.clear_timer()

@ray.remote
class GlobalCounter:
    def __init__(self):
        self.value = 9

    def get_value(self):
        self.value += 1
        return self.value