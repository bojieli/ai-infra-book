# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import os
import uuid
import json
import torch
import torch.multiprocessing as mp
import requests
from torch.distributed._tensor import DTensor
import toml

from .sender_config import TransferEngineConfig, TransferAgentConfig
from .sender_agent import start_transfer_agent
from .utils import filter_ips_by_config, get_node_ips

logger = logging.getLogger(__name__)

def wait_for_endpoint_ready(endpoint: str, timeout: int = 300) -> bool:
    """Wait for rollout manager to be ready with timeout."""
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{endpoint}/health", timeout=5)
            if response.status_code == 200:
                logger.info(f"Rollout manager is ready at {endpoint}")
                return True
        except Exception:
            pass
        time.sleep(1)
    
    return False

class FSDPInterface:
    def __init__(self, local_rank: int, global_rank: int, params: dict, rollout_manager_endpoint: str, weight_sender_config_path: str):
        """Initialize the FSDP interface for weight transfer.
        
        Args:
            local_rank: Local rank within the node
            global_rank: Global rank
            params: Model parameters (state dict)
            rollout_manager_endpoint: Endpoint of rollout manager
            weight_sender_config_path: Path to weight sender configuration
        """
        self.local_rank = local_rank
        self.global_rank = global_rank
        self.rollout_manager_endpoint = rollout_manager_endpoint
        
        # Weight transfer related attributes
        self.weight_sender_agent = None
        self.weight_sender_agent_queues = None
        self.weight_sender_agent_buffer = None
        
        # parse weight sender config
        with open(weight_sender_config_path, 'r') as f:
            self.weight_sender_config = self._build_sender_config(toml.load(f))
        
        # return when rollout manager is ready
        self.wait_for_rollout_manager_ready()

        # init agent
        meta_size, tensors_meta = self._get_meta_tensors_from_state_dict(params)

        if self.local_rank == 0:
            self._start_transfer_agent(meta_size, tensors_meta, self.rollout_manager_endpoint)
        
    # polyrl-dev
    def _update_weight_version(self):
        
        rollout_mgr_url = self.rollout_manager_endpoint
        try:
            response = requests.post(f"{rollout_mgr_url.rstrip('/')}/update_weight_version", timeout=60)
            response.raise_for_status()
            result = response.json()
            if result.get("success", False):
                new_version = result.get("new_weight_version", 0)
                logger.info(f"[Weight Transfer] Successfully updated weight version to {new_version}")
            else:
                raise RuntimeError(f"Rollout manager weight version update failed: {response.text}")
        except Exception as e:
            logger.error(f"Error during weight version update call to rollout manager: {e}")
            raise

    def _build_sender_config(self, config):        
        # NOTE(liuxs): get local ips
        all_node_ips = get_node_ips()
        allowed_sender_ips = config.get('allowed_sender_ips', '0.0.0.0/0')
        filtered_ips = filter_ips_by_config(all_node_ips, allowed_sender_ips)
        # TODO(xueshen): fix the config names
        num_engine_groups = config.get('num_mooncake_groups_per_sender', 1)
        num_engines_per_group = config.get('num_mooncake_engines_per_group', 1)
        if not filtered_ips:
            raise RuntimeError(f"No IPs found matching allowed_sender_ips {allowed_sender_ips} from node IPs {all_node_ips}")
        
        if len(filtered_ips) < num_engine_groups:
            weight_sender_ips = (filtered_ips * ((num_engine_groups // len(filtered_ips)) + 1))[:num_engine_groups]
        else:
            weight_sender_ips = filtered_ips[:num_engine_groups]

        
        if len(weight_sender_ips) != num_engine_groups:
            raise ValueError(f"Number of weight sender IPs ({len(weight_sender_ips)}) does not match num_engine_groups ({num_engine_groups})")
        rpyc_bind_port = config.get('rpyc_bind_base_port', 18861)
        base_handshake_port = config.get('mooncake_handshake_port', 19000)
        
        engine_configs = []
        for group_idx, ip in enumerate(weight_sender_ips):
            group_handshake_port = base_handshake_port + group_idx * 1000
            engine_config = TransferEngineConfig(
                local_hostname=ip,
                handshake_port=group_handshake_port,
            )
            engine_configs.append(engine_config)
        global_rank = torch.distributed.get_rank()
        world_size = torch.distributed.get_world_size() 
        # Create and return the sender configuration
        sender_config = TransferAgentConfig(
            trainer_global_rank=global_rank,
            trainer_world_size=world_size,
            engine_configs=engine_configs,
            num_engines_per_group=num_engines_per_group,
            rpyc_bind_port=rpyc_bind_port,
        )
        
        return sender_config

    # polyrl-dev
    def _get_meta_tensors_from_state_dict(self, state_dict):
        meta_size = []
        tensors_meta = []
        for name, param in state_dict.items():
            if isinstance(param, DTensor):
                param = param.full_tensor()
            assert torch.is_tensor(param)
            # meta = torch.empty_like(param, device='meta')
            meta_size.append((name, param.numel() * param.element_size()))

            dtype = str(param.dtype).split('.')[-1]
            shape = list(param.shape)
            tensors_meta.append((name, (shape, dtype)))
        return meta_size, tensors_meta

    # polyrl-dev
    def _start_transfer_agent(self, meta_tensors, tensors_meta, rollout_manager_endpoint):
        mp.set_start_method('spawn', force=True)
        input_queue = mp.Queue()
        output_queue = mp.Queue()
        input_queue.put(meta_tensors)
        input_queue.put(tensors_meta)
        self.weight_sender_agent = start_transfer_agent(
            self.weight_sender_config, 
            input_queue, 
            output_queue,
            rollout_manager_endpoint,
        )
        self.weight_sender_agent_queues = (input_queue, output_queue)
        
        result = output_queue.get(timeout=60)
        if isinstance(result, tuple):
            shm_path, buffer_length = result
            assert isinstance(shm_path, str), "Should receive shared memory path"
            assert isinstance(buffer_length, int), "Should receive buffer length"
            
            from .sender_agent import create_tensor_from_shared_memory
            self.weight_sender_agent_buffer = create_tensor_from_shared_memory(shm_path, buffer_length)
        else:
            buffer = result
            assert torch.is_tensor(buffer)
            assert buffer.is_cpu
            self.weight_sender_agent_buffer = buffer

    # polyrl-dev
    def _copy_weights_to_buffer(self, state_dict):
        offset = 0
        tensors_meta = []
        for name, param in state_dict.items():
            if isinstance(param, DTensor):
                param = param.full_tensor()
            numel = param.numel()
            size_in_bytes = numel * param.element_size()
            
            if self.weight_sender_agent:
                param_data_cpu = param.data.contiguous() # .cpu()
                param_u8 = param_data_cpu.view(-1).view(torch.uint8)
                buffer_slice = self.weight_sender_agent_buffer[offset : offset + size_in_bytes]
                buffer_slice.copy_(param_u8, non_blocking=True)
                offset += size_in_bytes

            dtype = str(param.dtype).split('.')[-1]
            shape = list(param.shape)
            tensors_meta.append((name, (shape, dtype)))
        torch.cuda.synchronize()

        return tensors_meta

    def wait_for_rollout_manager_ready(self):
        """Wait for rollout manager to be ready."""
        if not wait_for_endpoint_ready(self.rollout_manager_endpoint):
            raise RuntimeError("Rollout manager is not ready")

    def update_weights_with_agent(self, params):
        """Main method to update weights using the transfer agent.
        
        NOTE(liuxs): this function must be wrapped with barriers to make sure weights on all training proc are sync
        
        Args:
            params: Model parameters (state dict)
        """
        # Only global rank 0 calls update_weight_version
        if self.global_rank == 0:
            self._update_weight_version()

        # All ranks copy weights to buffer, but only local rank 0s send, most time consuming step
        self._copy_weights_to_buffer(params)

        if self.local_rank == 0:
            assert self.weight_sender_agent, "Weight sender agent should be initialized"
            self.weight_sender_agent_queues[0].put("update_weights")
            status = self.weight_sender_agent_queues[1].get()
            if status != "completed":
                raise RuntimeError(f"Weight update failed: {status}")