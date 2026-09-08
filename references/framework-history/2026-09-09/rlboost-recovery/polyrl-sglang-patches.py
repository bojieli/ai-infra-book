import logging
import types
import os
from typing import Tuple, List, Optional
from dataclasses import dataclass

from rlboost.sglang.autopatch import BasePatch

logger = logging.getLogger(__name__)


class ServerArgsPatch(BasePatch):
    def apply(self) -> bool:
        try:
            from sglang.srt import server_args

            ServerArgs = server_args.ServerArgs

            if hasattr(ServerArgs, 'enable_weight_transfer_agent'):
                return True

            ServerArgs.enable_weight_transfer_agent = False
            ServerArgs.transfer_agent_handshake_port = 21000
            ServerArgs.weight_sender_rpyc_endpoint = ""
            ServerArgs.weight_receiver_zmq_bind_host = "0.0.0.0"
            ServerArgs.rollout_manager_address = None
            ServerArgs.transfer_agent_sender_group_idx = 0
            ServerArgs.num_transfer_engines_per_group = 1

            original_add_cli_args = ServerArgs.add_cli_args

            def patched_add_cli_args(parser):
                original_add_cli_args(parser)

                parser.add_argument(
                    "--enable-weight-transfer-agent",
                    action="store_true",
                    help="Enable weight transfer agent for PolyRL.",
                )
                parser.add_argument(
                    "--transfer-agent-handshake-port",
                    type=int,
                    default=ServerArgs.transfer_agent_handshake_port,
                    help="The port used for transfer agent P2P handshake.",
                )
                parser.add_argument(
                    "--weight-sender-rpyc-endpoint",
                    type=str,
                    default=ServerArgs.weight_sender_rpyc_endpoint,
                    help="Weight sender RPyC endpoint for weight transfer.",
                )
                parser.add_argument(
                    "--weight-receiver-zmq-bind-host",
                    type=str,
                    default=ServerArgs.weight_receiver_zmq_bind_host,
                    help="The host address to bind for weight receiver ZMQ sockets.",
                )
                parser.add_argument(
                    "--rollout-manager-address",
                    type=str,
                    default=ServerArgs.rollout_manager_address,
                    help="The address of the rollout manager",
                )
                parser.add_argument(
                    "--transfer-agent-sender-group-idx",
                    type=int,
                    default=ServerArgs.transfer_agent_sender_group_idx,
                    help="The sender group index for weight transfer",
                )
                parser.add_argument(
                    "--num-transfer-engines-per-group",
                    type=int,
                    default=ServerArgs.num_transfer_engines_per_group,
                    help="Number of transfer engines per group",
                )

            self._mark_as_patched(patched_add_cli_args, "add_cli_args")
            ServerArgs.add_cli_args = staticmethod(patched_add_cli_args)

            original_prepare_server_args = server_args.prepare_server_args

            def patched_prepare_server_args(args_list):
                result = original_prepare_server_args(args_list)

                import argparse
                parser = argparse.ArgumentParser()
                ServerArgs.add_cli_args(parser)
                parsed_args = parser.parse_args(args_list)

                result.enable_weight_transfer_agent = parsed_args.enable_weight_transfer_agent
                result.transfer_agent_handshake_port = parsed_args.transfer_agent_handshake_port
                result.weight_sender_rpyc_endpoint = parsed_args.weight_sender_rpyc_endpoint
                result.weight_receiver_zmq_bind_host = parsed_args.weight_receiver_zmq_bind_host
                result.rollout_manager_address = parsed_args.rollout_manager_address
                result.transfer_agent_sender_group_idx = parsed_args.transfer_agent_sender_group_idx
                result.num_transfer_engines_per_group = parsed_args.num_transfer_engines_per_group

                return result

            server_args.prepare_server_args = patched_prepare_server_args

            return True
        except Exception as e:
            logger.error(f"ServerArgsPatch failed: {e}")
            return False


@dataclass
class UpdateWeightsFromAgentReqInput:
    tensors_meta: List[Tuple[str, Tuple[List[int], str]]]
    load_format: Optional[str] = None
    flush_cache: bool = True
    bootstrap: bool = False

@dataclass
class UpdateWeightsFromAgentReqOutput:
    success: bool
    message: str

class IOStructPatch(BasePatch):
    def apply(self) -> bool:
        try:
            from sglang.srt.managers import io_struct

            if hasattr(io_struct, 'UpdateWeightsFromAgentReqInput'):
                return True

            io_struct.UpdateWeightsFromAgentReqInput = UpdateWeightsFromAgentReqInput
            io_struct.UpdateWeightsFromAgentReqOutput = UpdateWeightsFromAgentReqOutput

            return True
        except Exception as e:
            logger.error(f"IOStructPatch failed: {e}")
            return False


class TpWorkerPatch(BasePatch):
    def apply(self) -> bool:
        try:
            from sglang.srt.managers import tp_worker
            import torch
            import torch.multiprocessing as mp
            from rlboost.weight_transfer.receiver_config import TransferEngineConfig, TransferAgentConfig
            from rlboost.weight_transfer.receiver_agent import start_transfer_agent

            BaseTpWorker = tp_worker.BaseTpWorker
            TpModelWorker = tp_worker.TpModelWorker

            if hasattr(BaseTpWorker, 'update_weights_from_agent'):
                return True

            original_init = TpModelWorker.__init__

            def patched_init(self, *args, **kwargs):
                original_init(self, *args, **kwargs)

                server_args = args[0] if args else kwargs.get('server_args')

                if not hasattr(self, 'server_args'):
                    self.server_args = server_args

                if server_args.enable_weight_transfer_agent:
                    self.weight_receiver_config = self._build_weight_receiver_config(server_args)
                    self.weight_receiver_agent = None
                    self.weight_receiver_agent_queues = None
                    self.weight_receiver_agent_buffer = None
                    self.weight_transfer_chunk_size = int(os.getenv('WEIGHT_TRANSFER_CHUNK_SIZE', 2 * 1024 * 1024 * 1024))

            def update_weights_from_agent(self, recv_req):
                from sglang.srt.managers.io_struct import UpdateWeightsFromAgentReqInput

                tensors_meta = recv_req.tensors_meta
                if self.weight_receiver_agent is None and self.tp_rank == 0:
                    assert recv_req.bootstrap
                    meta_tensors = []
                    for name, (shape, dtype) in tensors_meta:
                        dtype = getattr(torch, dtype)
                        meta = torch.empty(shape, dtype=dtype, device='meta')
                        meta_tensors.append((name, meta))
                    self._start_weight_receiver_agent(meta_tensors, self.server_args)
                    return True, "Success"
                elif recv_req.bootstrap:
                    return True, "Success"

                assert recv_req.bootstrap is False
                if self.tp_rank == 0:
                    self.weight_receiver_agent_queues[0].put("receive_weights")
                    status = self.weight_receiver_agent_queues[1].get()
                    if status != "completed":
                        raise RuntimeError(f"Weight receive failed or unexpected status: {status}")

                if self.tp_rank == 0:
                    tensor_metadata = self._get_tensor_metadata_with_offsets(tensors_meta)
                    chunks = self._group_tensors_into_chunks(tensor_metadata, self.weight_transfer_chunk_size)

                    for chunk in chunks:
                        min_offset = min(meta['offset'] for meta in chunk)
                        max_offset_end = max(meta['offset'] + meta['size_in_bytes'] for meta in chunk)
                        chunk_size = max_offset_end - min_offset

                        chunk_buffer = self.weight_receiver_agent_buffer[min_offset:max_offset_end]
                        gpu_chunk = chunk_buffer.to(self.device)
                        torch.distributed.broadcast(gpu_chunk, src=0, group=self.world_group.device_group)

                        chunk_tensors = []
                        for meta in chunk:
                            relative_offset = meta['offset'] - min_offset
                            buffer_slice = gpu_chunk[relative_offset:relative_offset + meta['size_in_bytes']]
                            tensor = buffer_slice.view(meta['dtype']).view(*meta['shape'])
                            chunk_tensors.append((meta['name'], tensor))

                        success, message = self.model_runner.update_weights_from_tensor(
                            named_tensors=chunk_tensors,
                            load_format=recv_req.load_format,
                        )
                        assert success
                else:
                    tensor_metadata = self._get_tensor_metadata_with_offsets(tensors_meta)
                    chunks = self._group_tensors_into_chunks(tensor_metadata, self.weight_transfer_chunk_size)

                    for chunk in chunks:
                        min_offset = min(meta['offset'] for meta in chunk)
                        max_offset_end = max(meta['offset'] + meta['size_in_bytes'] for meta in chunk)
                        chunk_size = max_offset_end - min_offset

                        gpu_chunk = torch.empty(chunk_size, dtype=torch.uint8, device=self.device)
                        torch.distributed.broadcast(gpu_chunk, src=0, group=self.world_group.device_group)

                        chunk_tensors = []
                        for meta in chunk:
                            relative_offset = meta['offset'] - min_offset
                            buffer_slice = gpu_chunk[relative_offset:relative_offset + meta['size_in_bytes']]
                            tensor = buffer_slice.view(meta['dtype']).view(*meta['shape'])
                            chunk_tensors.append((meta['name'], tensor))

                        success, message = self.model_runner.update_weights_from_tensor(
                            named_tensors=chunk_tensors,
                            load_format=recv_req.load_format,
                        )
                        assert success
                return success, message

            def _build_weight_receiver_config(self, server_args):
                host, port = server_args.weight_sender_rpyc_endpoint.split(":")
                sender_rpyc_endpoints = [(host, int(port))]

                engine_config = TransferEngineConfig(
                    local_hostname=server_args.host,
                    handshake_port=server_args.transfer_agent_handshake_port,
                )
                config = TransferAgentConfig(
                    sender_rpyc_endpoints=sender_rpyc_endpoints,
                    engine_config=engine_config,
                    num_engines=server_args.num_transfer_engines_per_group,
                    sglang_http_host=server_args.host,
                    sglang_http_port=server_args.port,
                    zmq_bind_host=server_args.weight_receiver_zmq_bind_host,
                )
                return config

            def _start_weight_receiver_agent(self, meta_tensors, server_args):
                assert self.weight_receiver_agent is None

                mp.set_start_method('spawn', force=True)
                input_queue = mp.Queue()
                output_queue = mp.Queue()
                input_queue.put(meta_tensors)
                self.weight_receiver_agent = start_transfer_agent(
                    self.weight_receiver_config,
                    input_queue,
                    output_queue,
                    server_args
                )
                self.weight_receiver_agent_queues = (input_queue, output_queue)
                buffer = output_queue.get(timeout=60)
                assert torch.is_tensor(buffer)
                assert buffer.is_cpu
                self.weight_receiver_agent_buffer = buffer

            def _construct_received_weights(self, tensors_meta):
                offset = 0
                named_tensors = []
                for name, (shape, dtype) in tensors_meta:
                    size = 1
                    for dim in shape:
                        size *= dim
                    dtype = getattr(torch, dtype)
                    elem_size = torch.finfo(dtype).bits // 8
                    size_in_bytes = size * elem_size
                    buffer_slice = self.weight_receiver_agent_buffer[offset : offset + size_in_bytes]
                    tensor = buffer_slice.view(dtype).view(*shape)
                    named_tensors.append((name, tensor))
                    offset += size_in_bytes
                return named_tensors

            def _get_tensor_metadata_with_offsets(self, tensors_meta):
                offset = 0
                tensor_metadata = []
                for name, (shape, dtype) in tensors_meta:
                    size = 1
                    for dim in shape:
                        size *= dim
                    dtype_obj = getattr(torch, dtype)
                    elem_size = torch.finfo(dtype_obj).bits // 8
                    size_in_bytes = size * elem_size
                    tensor_metadata.append({
                        'name': name,
                        'shape': shape,
                        'dtype': dtype_obj,
                        'offset': offset,
                        'size_in_bytes': size_in_bytes
                    })
                    offset += size_in_bytes
                return tensor_metadata

            def _group_tensors_into_chunks(self, tensor_metadata, chunk_size):
                chunks = []
                current_chunk = []
                current_chunk_size = 0

                for tensor_meta in tensor_metadata:
                    tensor_size = tensor_meta['size_in_bytes']

                    if tensor_size > chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk)
                            current_chunk = []
                            current_chunk_size = 0
                        chunks.append([tensor_meta])
                    elif current_chunk_size + tensor_size <= chunk_size:
                        current_chunk.append(tensor_meta)
                        current_chunk_size += tensor_size
                    else:
                        chunks.append(current_chunk)
                        current_chunk = [tensor_meta]
                        current_chunk_size = tensor_size

                if current_chunk:
                    chunks.append(current_chunk)

                return chunks

            self._mark_as_patched(patched_init, "init")
            TpModelWorker.__init__ = patched_init
            BaseTpWorker.update_weights_from_agent = update_weights_from_agent
            BaseTpWorker._build_weight_receiver_config = _build_weight_receiver_config
            BaseTpWorker._start_weight_receiver_agent = _start_weight_receiver_agent
            BaseTpWorker._construct_received_weights = _construct_received_weights
            BaseTpWorker._get_tensor_metadata_with_offsets = _get_tensor_metadata_with_offsets
            BaseTpWorker._group_tensors_into_chunks = _group_tensors_into_chunks

            return True
        except Exception as e:
            logger.error(f"TpWorkerPatch failed: {e}")
            import traceback
            traceback.print_exc()
            return False


class SchedulerUpdateWeightsMixinPatch(BasePatch):
    def apply(self) -> bool:
        try:
            from sglang.srt.managers import scheduler_update_weights_mixin

            SchedulerUpdateWeightsMixin = scheduler_update_weights_mixin.SchedulerUpdateWeightsMixin

            if hasattr(SchedulerUpdateWeightsMixin, 'update_weights_from_agent'):
                return True

            def update_weights_from_agent(self, recv_req):
                from sglang.srt.managers.io_struct import UpdateWeightsFromAgentReqOutput

                success, message = self.tp_worker.update_weights_from_agent(recv_req)
                if success:
                    if recv_req.flush_cache:
                        flush_cache_success = self.flush_cache()
                        assert flush_cache_success, "Cache flush failed after updating weights"
                else:
                    logger.error(message)
                return UpdateWeightsFromAgentReqOutput(success, message)

            SchedulerUpdateWeightsMixin.update_weights_from_agent = update_weights_from_agent

            return True
        except Exception as e:
            logger.error(f"SchedulerUpdateWeightsMixinPatch failed: {e}")
            return False


class SchedulerPatch(BasePatch):
    def apply(self) -> bool:
        try:
            from sglang.srt.managers import scheduler
            from sglang.srt.managers.io_struct import UpdateWeightsFromAgentReqInput

            Scheduler = scheduler.Scheduler

            original_init = Scheduler.__init__

            if self._is_patched(original_init, "init"):
                return True

            def patched_init(self, *args, **kwargs):
                original_init(self, *args, **kwargs)

                dispatcher = self._request_dispatcher
                # Check if already registered to avoid duplicates
                if not any(ty == UpdateWeightsFromAgentReqInput for ty, _ in dispatcher._mapping):
                    dispatcher._mapping.append((UpdateWeightsFromAgentReqInput, self.update_weights_from_agent))

            original_get_internal_state = Scheduler.get_internal_state

            def patched_get_internal_state(self, recv_req):
                from sglang.srt.managers.io_struct import GetInternalStateReqOutput

                ret = original_get_internal_state(self, recv_req)

                if hasattr(ret, 'internal_state'):
                    internal_state = ret.internal_state
                else:
                    internal_state = ret

                if hasattr(self, 'running_batch') and hasattr(self, 'waiting_queue'):
                    internal_state["#running_req"] = len(self.running_batch.reqs)
                    internal_state["#queue_req"] = len(self.waiting_queue)

                if isinstance(ret, GetInternalStateReqOutput):
                    return ret
                else:
                    return GetInternalStateReqOutput(internal_state=internal_state)

            self._mark_as_patched(patched_init, "init")
            Scheduler.__init__ = patched_init
            Scheduler.get_internal_state = patched_get_internal_state

            return True
        except Exception as e:
            logger.error(f"SchedulerPatch failed: {e}")
            import traceback
            traceback.print_exc()
            return False


class TokenizerCommunicatorMixinPatch(BasePatch):
    def apply(self) -> bool:
        try:
            from sglang.srt.managers import tokenizer_communicator_mixin
            from sglang.srt.managers.io_struct import (
                UpdateWeightsFromAgentReqInput,
                UpdateWeightsFromAgentReqOutput,
            )

            TokenizerCommunicatorMixin = tokenizer_communicator_mixin.TokenizerCommunicatorMixin

            if hasattr(TokenizerCommunicatorMixin, 'update_weights_from_agent'):
                return True

            original_init_communicators = TokenizerCommunicatorMixin.init_communicators

            def patched_init_communicators(self, server_args):
                original_init_communicators(self, server_args)

                _Communicator = tokenizer_communicator_mixin._Communicator
                self.update_weights_from_agent_communicator = _Communicator(
                    self.send_to_scheduler, self.server_args.dp_size
                )

                dispatcher = self._result_dispatcher
                # Check if already registered to avoid duplicates
                if not any(ty == UpdateWeightsFromAgentReqOutput for ty, _ in dispatcher._mapping):
                    dispatcher._mapping.append((UpdateWeightsFromAgentReqOutput,
                                                self.update_weights_from_agent_communicator.handle_recv))

            async def update_weights_from_agent(self, obj, request=None):
                if self.server_args.transfer_agent_handshake_port == 0:
                    logger.warning("Weight transfer agent is not enabled, skipping weight update")
                    result = UpdateWeightsFromAgentReqOutput(
                        success=True, message="Weight transfer agent is not enabled, skipping weight update"
                    )
                    return result.success, result.message
                self.auto_create_handle_loop()
                async with self.model_update_lock.writer_lock:
                    result = (await self.update_weights_from_agent_communicator(obj))[0]
                    return result.success, result.message

            self._mark_as_patched(patched_init_communicators, "init_communicators")
            TokenizerCommunicatorMixin.init_communicators = patched_init_communicators
            TokenizerCommunicatorMixin.update_weights_from_agent = update_weights_from_agent

            return True
        except Exception as e:
            logger.error(f"TokenizerCommunicatorMixinPatch failed: {e}")
            import traceback
            traceback.print_exc()
            return False


class HttpServerPatch(BasePatch):
    def apply(self) -> bool:
        try:
            from sglang.srt.entrypoints import http_server
            from sglang.srt.managers.io_struct import UpdateWeightsFromAgentReqInput
            from fastapi import Request
            from fastapi.responses import ORJSONResponse
            from http import HTTPStatus
            import requests

            original_launch_server = http_server.launch_server

            if self._is_patched(original_launch_server, "launch_server"):
                return True

            def patched_launch_server(server_args, *args, **kwargs):
                if server_args.enable_weight_transfer_agent:
                    rollout_mgr_url = server_args.rollout_manager_address
                    if rollout_mgr_url:
                        try:
                            reg_payload = {
                                "host": server_args.host,
                                "port": server_args.port,
                                "mooncake_handshake_port": server_args.transfer_agent_handshake_port
                            }
                            res = requests.post(f"{rollout_mgr_url.rstrip('/')}/register_rollout_instance", json=reg_payload, timeout=100)
                            if res.status_code == 200:
                                cfg = res.json()
                                for k in [
                                    ("weight_sender_rpyc_endpoint", "weight_sender_rpyc_endpoint"),
                                ]:
                                    key_json, attr = k
                                    if key_json in cfg and hasattr(server_args, attr):
                                        setattr(server_args, attr, cfg[key_json])

                                server_args.transfer_agent_sender_group_idx = cfg["sender_group_idx"]
                                server_args.num_transfer_engines_per_group = cfg["num_mooncake_engines_per_group"]
                                logger.info(f"Registered with rollout manager at {rollout_mgr_url}, got params: {cfg}")
                            else:
                                logger.warning(
                                    f"Failed to register rollout instance: status {res.status_code}, resp {res.text}"
                                )
                        except Exception as e:
                            logger.error(f"Exception when registering rollout instance: {e}")

                return original_launch_server(server_args, *args, **kwargs)

            if hasattr(http_server, 'app'):
                app = http_server.app

                @app.post("/update_weights_from_agent")
                async def update_weights_from_agent(obj: UpdateWeightsFromAgentReqInput, request: Request):
                    success, message = await http_server._global_state.tokenizer_manager.update_weights_from_agent(
                        obj, request
                    )
                    content = {"success": success, "message": message}
                    return ORJSONResponse(
                        content, status_code=200 if success else HTTPStatus.BAD_REQUEST
                    )

            self._mark_as_patched(patched_launch_server, "launch_server")
            http_server.launch_server = patched_launch_server

            return True
        except Exception as e:
            logger.error(f"HttpServerPatch failed: {e}")
            import traceback
            traceback.print_exc()
            return False
