import asyncio
import logging
import os
import queue
import socket
import threading
import time
import mmap
import ctypes
import ctypes.util
from typing import Dict, List, Tuple, Optional

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    uvloop = None

import requests
import rpyc
import torch.multiprocessing as mp
import zmq
from rpyc.utils.classic import obtain

from .transfer_engine import TCPTransferEngine
from .sender_config import (TransferAgentConfig, 
                     TransferStatus, ReceiverInfo)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_tensor_from_shared_memory(shm_path, buffer_length):
    """Create a torch tensor from shared memory file.
    
    Args:
        shm_path: Path to shared memory file
        buffer_length: Size of the buffer in bytes
    
    Returns:
        torch.Tensor: Tensor backed by shared memory
    """
    import mmap
    import ctypes
    import ctypes.util
    import os
    import torch
    
    shm_fd = os.open(shm_path, os.O_RDWR)
    
    flags = mmap.MAP_SHARED
    try:
        flags |= mmap.MAP_POPULATE
    except AttributeError:
        pass
    
    mmap_buffer = mmap.mmap(shm_fd, buffer_length, flags=flags, prot=mmap.PROT_READ | mmap.PROT_WRITE)
    os.close(shm_fd)
    
    try:
        mmap_buffer.madvise(mmap.MADV_DONTDUMP)
        mmap_buffer.madvise(mmap.MADV_DONTFORK)
    except:
        pass
    
    buffer_ptr = ctypes.addressof(ctypes.c_byte.from_buffer(mmap_buffer))
    
    try:
        libc = ctypes.CDLL(ctypes.util.find_library('c'))
        ret = libc.mlock(ctypes.c_void_p(buffer_ptr), ctypes.c_size_t(buffer_length))
        if ret == 0:
            logger.info(f"Successfully locked {buffer_length / (1024*1024):.1f} MB in RAM")
    except Exception as e:
        logger.debug(f"Could not lock pages: {e}")
    
    try:
        buffer_address = ctypes.addressof(ctypes.c_byte.from_buffer(mmap_buffer))
        MADV_HUGEPAGE = 14
        libc = ctypes.CDLL(ctypes.util.find_library('c'))
        ret = libc.madvise(ctypes.c_void_p(buffer_address), 
                          ctypes.c_size_t(buffer_length), 
                          ctypes.c_int(MADV_HUGEPAGE))
        if ret == 0:
            logger.info(f"Enabled transparent huge pages via madvise")
    except Exception as e:
        logger.debug(f"Could not enable transparent huge pages: {e}")
    
    try:
        mmap_buffer.madvise(mmap.MADV_SEQUENTIAL)
        mmap_buffer.madvise(mmap.MADV_WILLNEED)
    except Exception as e:
        logger.debug(f"Could not apply madvise hints: {e}")
    
    torch.cuda.cudart().cudaHostRegister(buffer_ptr, buffer_length, 0)
    
    tensor = torch.frombuffer(mmap_buffer, dtype=torch.uint8)
    tensor._mmap_buffer = mmap_buffer
    
    return tensor


class TransferRpycServer(rpyc.Service):
    def __init__(self, transfer_agent: "TransferAgent"):
        self.transfer_agent = transfer_agent

    def exposed_register_sglang_instance(
        self, 
        sglang_http_host: str,
        sglang_http_port: int, 
        session_ids: List[str], 
        buffer_ptr: int, 
        buffer_length: int,
        zmq_endpoint: str,
        zmq_port: int,
        handshake_ports: List[int],
        sender_group_index: int = 0
    ):
        try:
            # Create a unique identifier for this sglang instance
            instance_id = f"{sglang_http_host}:{sglang_http_port}"
            if self.transfer_agent.use_tcp_engine:
                assert len(session_ids) == 1
            elif len(session_ids) != self.transfer_agent.config.num_engines_per_group:
                raise ValueError(
                    f"Expected {self.transfer_agent.config.num_engines_per_group} session IDs, got {len(session_ids)}"
                )
            session_ids = obtain(session_ids)
            handshake_ports = obtain(handshake_ports)

            logger.info(f"[Weight sender] Registering sglang instance: {instance_id}, remote_session_ids: {session_ids}")
            
            # Register with the transfer agent
            self.transfer_agent.register_receiver_session(
                instance_id, 
                session_ids,
                buffer_ptr,
                buffer_length,
                zmq_endpoint,
                zmq_port,
                sglang_http_host,
                sglang_http_port,
                handshake_ports,
                sender_group_index
            )
            
            # Return the registration information
            return {
                "trainer_global_rank": self.transfer_agent.config.trainer_global_rank,
                "trainer_world_size": self.transfer_agent.config.trainer_world_size,
                "trainer_session_ids": self.transfer_agent.get_session_ids(),
                "trainer_buffer_ptr": self.transfer_agent.buffer_ptr,
                "trainer_buffer_length": self.transfer_agent.buffer_length,
                # For P2P handshake
                "trainer_hostname": self.transfer_agent.get_hostname(),
                "trainer_rpc_port": self.transfer_agent.get_rpc_port(),
            }
        
        except Exception as e:
            logger.error(f"Failed to register sglang instance: {e}")
            return {"status": "error", "message": str(e)}
    

class TransferAgent:
    def __init__(
        self, 
        input_queue: mp.Queue, 
        output_queue: mp.Queue, 
        config: TransferAgentConfig,
        rollout_manager_endpoint,
    ):
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.config = config
        self.registered_receivers: Dict[str, ReceiverInfo] = {}
        self.buffer_length: Optional[int] = None
        self.buffer_ptr: Optional[int] = None
        self.transfer_engines: List[List] = []
        self.buffer_slices: List[List[Tuple[int, int, int]]] = []
        self.transfer_counter = 0
        self.use_tcp_engine = os.environ.get('TRANSFER_ENGINE_TYPE', 'tcp').lower() == 'tcp'
        
        # mmap related - shared across all groups
        self.memfd: Optional[int] = None
        self.mmap_buffer: Optional[mmap.mmap] = None

        self.weight_version = 0
        assert rollout_manager_endpoint is not None, "Rollout manager endpoint is not set"
        self.rollout_manager_endpoint = rollout_manager_endpoint
        self.tensors_meta = None

        weight_sender_ip = config.engine_configs[0].local_hostname
        self.endpoint = f"{weight_sender_ip}:{self.config.rpyc_bind_port}"
        
        self.use_async_notify = os.environ.get('ASYNC_WEIGHT_NOTIFY', 'true').lower() == 'true'
        self.async_executor = None
        self.async_loop = None
        self.async_thread = None
        self.pending_async_tasks = []
        
        if self.use_async_notify:
            self._setup_async_executor()
        
        self.initialize_transfer_engines()
    
    def _setup_async_executor(self):
        def run_async_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.async_loop = loop
            loop.run_forever()
        
        self.async_thread = threading.Thread(target=run_async_loop, daemon=True)
        self.async_thread.start()
        
        while self.async_loop is None:
            time.sleep(0.001)
        
        logger.info("Setup async executor for weight notifications")
    
    def check_port_available(self, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return True
        except:
            return False

    def initialize_transfer_engines(self):
        num_engines_per_group = self.config.num_engines_per_group
        for group_idx, engine_config in enumerate(self.config.engine_configs):
            engine = TCPTransferEngine(config=engine_config, num_threads=num_engines_per_group)
            self.transfer_engines.append([engine])
            logger.info(f"Initialized TCP engine group {group_idx} with {engine.num_parallel_streams} parallel streams")

    def allocate_transfer_buffer(self, params_size: List[Tuple[str, int]]):
        assert len(self.transfer_engines) > 0, "Transfer Engines not initialized"
        
        total_bytes = sum(size for _, size in params_size)
        self.buffer_length = total_bytes
        
        import tempfile
        import os
        
        self.shm_file = tempfile.NamedTemporaryFile(dir='/dev/shm', delete=False, prefix='verl_buffer_')
        os.ftruncate(self.shm_file.fileno(), self.buffer_length)
        
        flags = mmap.MAP_SHARED
        try:
            flags |= mmap.MAP_POPULATE
        except AttributeError:
            pass
        
        self.mmap_buffer = mmap.mmap(self.shm_file.fileno(), self.buffer_length, flags=flags, prot=mmap.PROT_READ | mmap.PROT_WRITE)
        
        try:
            self.mmap_buffer.madvise(mmap.MADV_DONTDUMP)
            self.mmap_buffer.madvise(mmap.MADV_DONTFORK)
        except:
            pass
        
        buffer_address = ctypes.addressof(ctypes.c_byte.from_buffer(self.mmap_buffer))
        try:
            libc = ctypes.CDLL(ctypes.util.find_library('c'))
            ret = libc.mlock(ctypes.c_void_p(buffer_address), ctypes.c_size_t(self.buffer_length))
            if ret == 0:
                logger.info(f"[Sender] Successfully locked {self.buffer_length / (1024*1024):.1f} MB in RAM")
        except Exception as e:
            logger.debug(f"[Sender] Could not lock pages: {e}")
        
        try:
            MADV_HUGEPAGE = 14
            libc = ctypes.CDLL(ctypes.util.find_library('c'))
            ret = libc.madvise(ctypes.c_void_p(buffer_address), 
                                ctypes.c_size_t(self.buffer_length), 
                                ctypes.c_int(MADV_HUGEPAGE))
            if ret == 0:
                logger.info(f"[Sender] Enabled transparent huge pages via madvise")
        except Exception as e:
            logger.debug(f"[Sender] Could not enable transparent huge pages: {e}")
        
        try:
            self.mmap_buffer.madvise(mmap.MADV_SEQUENTIAL)
            self.mmap_buffer.madvise(mmap.MADV_WILLNEED)
            logger.info(f"[Sender] Applied madvise hints for optimal memory access")
        except Exception as e:
            logger.debug(f"[Sender] Could not apply madvise hints: {e}")
        
        self.buffer_ptr = buffer_address
        self.memfd = self.shm_file.fileno()
        
        logger.info(f"[Sender] Created shared memory buffer at {self.shm_file.name} for {self.buffer_length} bytes")
        
        self.output_queue.put((self.shm_file.name, self.buffer_length))
        
        num_engines_per_group = self.config.num_engines_per_group
        total_length = self.buffer_length
        slice_size = total_length // num_engines_per_group
        
        for group_idx, group_engines in enumerate(self.transfer_engines):
            group_slices = []
            
            # For TCP engine, register the shared memfd with each group's engine
            assert len(group_engines) == 1, "TCP engine should have single instance per group"
            engine = group_engines[0]
            engine.register_memfd(self.memfd, self.buffer_length)
            group_slices.append((self.buffer_ptr, 0, self.buffer_length))
            logger.info(f"Registered shared memfd with TCP engine group {group_idx}")
            
            self.buffer_slices.append(group_slices)
    
    def get_hostname(self):
        return self.transfer_engines[0][0].get_hostname() if self.transfer_engines else None
    
    def get_rpc_port(self):
        return self.transfer_engines[0][0].get_rpc_port() if self.transfer_engines else None
    
    def get_session_ids(self) -> List[List[str]]:
        session_ids = []
        for group_engines in self.transfer_engines:
            group_session_ids = [engine.get_session_id() for engine in group_engines]
            session_ids.append(group_session_ids)
        return session_ids

    def event_loop(self):
        try:
            while True:
                try:
                    request = self.input_queue.get(timeout=1.0)
                    if request == "update_weights":
                        self.weight_version += 1
                        logger.info(f"[Weight sender] Weight version updated to {self.weight_version}")
                        self.output_queue.put("completed")
                        self.check_and_update_receivers()
                except queue.Empty:
                    # continue # uncomment to disable pull-based weight transfer
                    if self.rollout_manager_endpoint:
                        self.check_and_update_receivers()
        except Exception as e:
            logger.error(f"Transfer agent event loop terminated: {e}")
            raise e

    def wait_for_receiver_registration(self, instance_ids: List[str]):
        while True:
            success = True
            for instance_id in instance_ids:
                if instance_id not in self.registered_receivers:
                    success = False
                    break
            if success:
                return
            time.sleep(1)

    def register_receiver_session(
        self, 
        instance_id, 
        session_ids: List[str], 
        buffer_ptr, 
        buffer_length,
        zmq_endpoint, 
        zmq_port,
        sglang_http_host=None,
        sglang_http_port=None,
        handshake_ports: List[int] = None,
        sender_group_index: int = 0
    ):
        if instance_id in self.registered_receivers:
            logger.warning(f"[Weight sender] Instance {instance_id} (session_ids: {session_ids}) already registered")
            
        assert self.buffer_length is not None, "Transfer buffer not allocated"
        assert self.buffer_length == buffer_length, \
            "Transfer buffer length mismatch between sender and receiver"
        assert sender_group_index < len(self.transfer_engines), \
            f"Invalid sender group index {sender_group_index}, only have {len(self.transfer_engines)} groups"

        self.registered_receivers[instance_id] = ReceiverInfo(
            session_ids=session_ids,
            buffer_ptr=buffer_ptr,
            buffer_length=buffer_length,
            zmq_endpoint=zmq_endpoint,
            zmq_port=zmq_port,
            sglang_http_host=sglang_http_host,
            sglang_http_port=sglang_http_port,
            handshake_ports=handshake_ports,
            sender_group_index=sender_group_index
        )
            
        logger.info(f"[Weight sender] Registered rollout instance {instance_id} with weight receiver session IDs {session_ids} using group {sender_group_index}")
        return True

    def submit_transfer_to_instance(self, instance_id) -> List[int]:
        assert instance_id in self.registered_receivers, f"Instance {instance_id} not registered"
        receiver_info = self.registered_receivers[instance_id]

        group_idx = receiver_info.sender_group_index
        group_engines = self.transfer_engines[group_idx]
        group_slices = self.buffer_slices[group_idx]
        
        batch_ids = []
        
        if self.use_tcp_engine:
            # For TCP engine, use single engine with internal parallelism
            assert len(group_engines) == 1, "TCP engine should have single instance per group"
            target_session_id = receiver_info.session_ids[0]
            # Pass offset 0 since we're using memfd
            batch_id = group_engines[0].transfer_submit_write(
                target_session_id,
                0,  # Local offset in memfd
                0,  # Remote offset
                self.buffer_length
            )
            batch_ids.append(batch_id)
            logger.debug(f"Submitted TCP transfer to {instance_id}: batch_id={batch_id}")
        else:
            for engine_idx, (engine, (slice_ptr, slice_offset, slice_length)) in enumerate(zip(group_engines, group_slices)):
                target_session_id = receiver_info.session_ids[engine_idx]
                remote_ptr = receiver_info.buffer_ptr + slice_offset
                
                batch_id = engine.transfer_submit_write(
                    target_session_id,
                    slice_ptr,
                    remote_ptr,
                    slice_length
                )
                batch_ids.append(batch_id)
                logger.debug(f"Submitted transfer to {instance_id} engine {engine_idx}: batch_id={batch_id}")
        
        return batch_ids

    def sync_status_to_receiver_endpoint(self, instance_id, status):
        receiver_info = self.registered_receivers[instance_id]
        sock = zmq.Context().socket(zmq.PUSH)
        sock.connect(f"tcp://{receiver_info.zmq_endpoint}:{receiver_info.zmq_port}")
        sock.send_multipart(
            [
                str(self.config.trainer_global_rank).encode('ascii'),
                str(int(status)).encode('ascii'),
            ]
        )

    def get_receive_instances(self):
        if not self.rollout_manager_endpoint:
            logger.warning("[Weight sender] Rollout manager endpoint not set")
            return []
        
        try:
            payload = {
                "weight_sender_endpoint": self.endpoint,
                "sender_weight_version": self.weight_version
            }
            response = requests.post(
                f"{self.rollout_manager_endpoint.rstrip('/')}/get_receive_instances",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get("instances", [])
        except Exception as e:
            logger.error(f"[Weight sender] Failed to get receive instances: {e}")
            return []

    def notify_weights_update(self, instance_endpoints, weight_version, tensors_meta, bootstrap=False):
        if not self.rollout_manager_endpoint:
            logger.warning("[Weight sender] Rollout manager endpoint not set")
            return False
        
        try:
            payload = {
                "instance_endpoints": instance_endpoints,
                "weight_version": weight_version,
                "tensors_meta": tensors_meta,
                "load_format": None,
                "flush_cache": True,
                "bootstrap": bootstrap
            }
            response = requests.post(
                f"{self.rollout_manager_endpoint.rstrip('/')}/update_weights",
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            data = response.json()
            return data.get("success", False)
        except Exception as e:
            logger.error(f"[Weight sender] Failed to notify weights update: {e}")
            return False

    async def _async_notify_weights_update(self, instance_endpoints, weight_version, tensors_meta, bootstrap=False):
        if not self.rollout_manager_endpoint:
            logger.warning("[Weight sender] Rollout manager endpoint not set")
            return False
        
        import aiohttp
        try:
            payload = {
                "instance_endpoints": instance_endpoints,
                "weight_version": weight_version,
                "tensors_meta": tensors_meta,
                "load_format": None,
                "flush_cache": True,
                "bootstrap": bootstrap
            }
            
            timeout = aiohttp.ClientTimeout(total=300)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.rollout_manager_endpoint.rstrip('/')}/update_weights",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data.get("success", False)
        except Exception as e:
            logger.error(f"[Weight sender] Failed to async notify weights update: {e}")
            return False

    def _schedule_async_notify(self, instance_endpoints, weight_version, tensors_meta, bootstrap=False):
        if self.async_loop and self.use_async_notify:
            future = asyncio.run_coroutine_threadsafe(
                self._async_notify_weights_update(instance_endpoints, weight_version, tensors_meta, bootstrap),
                self.async_loop
            )
            return future
        else:
            raise ValueError("Missing async loop")
            # self.notify_weights_update(instance_endpoints, weight_version, tensors_meta, bootstrap)

    def check_and_update_receivers(self):
        if self.weight_version == 0:
            logger.debug("Waiting for initial weights, skipping receiver check")
            return
        
        instances_to_update = self.get_receive_instances()
        if not instances_to_update:
            logger.debug("[Weight sender] No instances need weight updates")
            return
        
        logger.info(f"[Weight sender] Found {len(instances_to_update)} instances needing updates")
        
        bootstrap_instances = []
        regular_instances = []
        
        for instance_data in instances_to_update:
            instance = instance_data["instance"]
            current_version = instance_data["current_weight_version"]
            assert current_version < self.weight_version, \
                f"Instance {instance['endpoint']} has weight version {current_version} which is ahead of sender {self.weight_version}"
            
            if current_version == 0:
                bootstrap_instances.append(instance)
            else:
                regular_instances.append(instance)
        
        if bootstrap_instances:
            logger.info(f"[Weight sender] Bootstrapping {len(bootstrap_instances)} instances")
            bootstrap_endpoints = [inst["endpoint"].replace("http://", "") for inst in bootstrap_instances]
            
            self.notify_weights_update(
                bootstrap_endpoints,
                self.weight_version,
                self.tensors_meta,
                bootstrap=True
            )
            
            self.wait_for_receiver_registration([inst["endpoint"].replace("http://", "") for inst in bootstrap_instances])
        
        all_instances = bootstrap_instances + regular_instances
        if all_instances:
            logger.info(f"[Weight sender] Transferring weights to {len(all_instances)} instances")
            start_time = time.perf_counter()
            
            instance_batch_ids = {}
            endpoint_engine_completed = {}
            for instance in all_instances:
                endpoint = instance["endpoint"].replace("http://", "")
                if endpoint in self.registered_receivers:
                    batch_ids = self.submit_transfer_to_instance(endpoint)
                    instance_batch_ids[endpoint] = batch_ids
                    group_idx = self.registered_receivers[endpoint].sender_group_index
                    endpoint_engine_completed[endpoint] = [False] * len(self.transfer_engines[group_idx])
            
            completed_instances = set()
            all_completed = False
            while not all_completed:
                time.sleep(0.001)
                
                for endpoint, batch_ids in instance_batch_ids.items():
                    if endpoint in completed_instances:
                        continue
                    
                    receiver_info = self.registered_receivers[endpoint]
                    group_idx = receiver_info.sender_group_index
                    group_engines = self.transfer_engines[group_idx]
                    completed_flags = endpoint_engine_completed[endpoint]
                    failure = False
                    for engine_idx, (engine, batch_id) in enumerate(zip(group_engines, batch_ids)):
                        if completed_flags[engine_idx]:
                            continue
                        status = engine.transfer_check_status(batch_id)
                        if status == 1:
                            completed_flags[engine_idx] = True
                        elif status < 0:
                            logger.error(f"Transfer to {endpoint} engine {engine_idx} failed with status {status}")
                            self.sync_status_to_receiver_endpoint(endpoint, TransferStatus.FAILURE)
                            completed_instances.add(endpoint)
                            failure = True
                            break
                    
                    if failure:
                        continue
                    
                    if all(completed_flags):
                        self.sync_status_to_receiver_endpoint(endpoint, TransferStatus.SUCCESS)
                        completed_instances.add(endpoint)
                        logger.info(f"[Weight sender] Completed transfer to {endpoint} at {time.perf_counter()-start_time:.2f}s")
                        
                        if self.use_async_notify:
                            future = self._schedule_async_notify(
                                [endpoint],
                                self.weight_version,
                                self.tensors_meta,
                                bootstrap=False
                            )
                            self.pending_async_tasks.append(future)
                
                all_completed = len(completed_instances) == len(instance_batch_ids)

            end_time = time.perf_counter()
            total_bytes = self.buffer_length * len(all_instances)
            logger.info(f"[Weight sender] All transfers completed in {end_time-start_time:.2f}s, bandwidth {total_bytes/(end_time-start_time)/1024/1024:.2f}MB/s")
            
            if self.use_async_notify and self.pending_async_tasks:
                logger.info(f"[Weight sender] Waiting for {len(self.pending_async_tasks)} async notifications to complete")
                for future in self.pending_async_tasks:
                    try:
                        future.result(timeout=60)
                    except Exception as e:
                        logger.error(f"[Weight sender] Async notification failed: {e}")
                self.pending_async_tasks.clear()
                logger.info("[Weight sender] All async notifications completed")
            elif not self.use_async_notify:
                self.notify_weights_update(
                    list(completed_instances),
                    self.weight_version,
                    self.tensors_meta,
                    bootstrap=False
                )


def _init(
    config: TransferAgentConfig,
    input_queue: mp.Queue,
    output_queue: mp.Queue,
    event,
    rollout_manager_endpoint: str,
):
    transfer_agent = TransferAgent(input_queue, output_queue, config, rollout_manager_endpoint)

    from rpyc.utils.server import ThreadedServer

    # Create RPyC service with reference to this agent
    service = TransferRpycServer(transfer_agent)
    # Start server in a separate thread
    server = ThreadedServer(service, port=config.rpyc_bind_port, protocol_config={"allow_pickle": True})
    logger.info(f"Starting RPyC server on 0.0.0.0:{config.rpyc_bind_port}")
    threading.Thread(target=server.start, daemon=True).start()

    # polyrl-dev
    # NOTE(liuxs): new torch likely has a problem with pickle empty tensor, pass size directly
    weights_meta_size = input_queue.get()
    tensors_meta = input_queue.get()
    transfer_agent.tensors_meta = tensors_meta
    # allocate_transfer_buffer will complete output_queue.put(weights_meta_tensors)
    transfer_agent.allocate_transfer_buffer(weights_meta_size)

    # FIXME(yongji):
    # Consider whether to register a graceful shutdown like LightLLM
    event.set()
    transfer_agent.event_loop()


def start_transfer_agent(
    config: TransferAgentConfig,
    input_queue: mp.Queue,
    output_queue: mp.Queue,
    rollout_manager_endpoint: str = None,
):
    event = mp.Event()
    proc = mp.Process(target=_init, args=(config, input_queue, output_queue, event, rollout_manager_endpoint))
    proc.start()
    event.wait()
    assert proc.is_alive(), "Transfer agent process should be alive"
    logger.info("Successfully started sender transfer agent process.")
    return proc