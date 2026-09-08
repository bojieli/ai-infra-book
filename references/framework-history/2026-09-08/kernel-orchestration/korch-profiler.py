from compute_bound_profiler import profile_conv, profile_gemm
from kernel_profiler import profile_main
from math import prod
import subprocess
import os
import re
import onnx
from utils import Target
from abc import ABC, abstractmethod

null = open(os.devnull, "w")
pattern = re.compile(r"mean = (.*?) ms")
INF = 100000

def trt_profile(onnx_path, trt_path="trt.log"):
    subprocess.run([
        "trtexec",
        "--separateProfileRun",
        f"--onnx={onnx_path}",
        "--dumpProfile",
        "--iterations=100",
        "--duration=0",
        "--device=1"],
        stdout=open(trt_path, "w"), stderr=null)
    for line in open(trt_path):
        if "GPU Compute Time: m" in line:
            return float(pattern.findall(line)[0])
    raise TypeError

def profile(onnx_path, params, DEVICE, TARGET, RPC_CONFIG, TARGET_DEVICE, WORK_DIR="./tune_kernels/", enable_trt=False, MODEL_FILENAME="kernel") -> float:
    if not os.path.exists(WORK_DIR):
        os.makedirs(WORK_DIR)
    candidate_kernel = onnx.load(onnx_path)
    result = trt_profile(onnx_path, WORK_DIR + "trt.log") if enable_trt else INF
    if params is None:
        tvm_result = list(profile_main(DEVICE, TARGET, RPC_CONFIG, WORK_DIR=WORK_DIR, onnx_model=candidate_kernel, DB_WIPE=False, MODEL_FILENAME=MODEL_FILENAME).values())
        if len(tvm_result) != 0:
            result = min(result, float(tvm_result[0][0]) * 1000)

    if params is not None and TARGET_DEVICE in ["v100", "a100", "a5000"]:  # compute bound case
        type = params.pop("type")
        if type == "conv":
            for i in range(8):
                params["algo"] = i
                cur_t = profile_conv(**params)
                if cur_t > 0:
                    result = min(result, cur_t)
            params["type"] = "conv"
        elif type == "matmul":
            shape_a, shape_b = tuple(params["shapea"]), tuple(params["shapeb"])
            if len(shape_a) != len(shape_b):
                shape_a = (1, prod(shape_a[:-1]), shape_a[-1])
                shape_b = (1, shape_b[0], prod(shape_b[1:]))
            else:
                shape_a = (prod(shape_a[:-2]), shape_a[-2], shape_a[-1])
                shape_b = (prod(shape_b[:-2]), shape_b[-2], shape_b[-1])
                assert shape_a[0] == shape_b[0]
            
            time = profile_gemm(shape_a[0], shape_a[1], shape_b[2], shape_a[2], params["transa"], params["transb"], TARGET_DEVICE == "a100")
            result = min(time, result)
            params["type"] = "matmul"

    return result


class KernelProfiler(ABC):
    def __init__(self, target_info: Target, database_path: str):
        self.target_info = target_info
        self.database_path = database_path

    @abstractmethod
    def profile(self, candidate_kernel) -> float:
        pass


class TensorRTKernelProfiler(KernelProfiler):
    def __init__(self, target_info: Target, database_path: str):
        super().__init__(target_info, database_path)

    def profile(self, candidate_kernel) -> float:
        return trt_profile(candidate_kernel.get_onnx_path(), os.path.join(self.database_path, "trt.log"))
    

class MemBoundKernelProfiler(KernelProfiler):
    def __init__(self, target_info: Target, database_path: str):
        super().__init__(target_info, database_path)
    
    def profile(self, candidate_kernel) -> float:
        # If the kernel is not mem-bound, return INF
        if candidate_kernel.get_params() is not None:
            return INF
        candidate_kernel_graph = onnx.load(candidate_kernel.get_onnx_path())
        tvm_result = list(profile_main(self.target_info.get_device(), self.target_info.get_target(), self.target_info.get_rpc_config(), WORK_DIR=self.database_path, onnx_model=candidate_kernel_graph, DB_WIPE=False, MODEL_FILENAME=candidate_kernel.get_onnx_name()).values())
        if len(tvm_result) != 0:
            return float(tvm_result[0][0]) * 1000
        else:
            return INF


class ConvKernelProfiler(KernelProfiler):
    def __init__(self, target_info: Target, database_path: str):
        super().__init__(target_info, database_path)
    
    def profile(self, candidate_kernel) -> float:
        if candidate_kernel.get_params() is None \
            or self.target_info.get_target_device_name() not in ["v100", "a100", "a5000"] \
            or candidate_kernel.get_params()["type"] != "conv":
            return INF
        
        params = candidate_kernel.get_params()
        op_type = params.pop("type")
        min_time = INF
        for i in range(8):
            params["algo"] = i
            cur_t = profile_conv(**params)
            if cur_t > 0:
                min_time = min(min_time, cur_t)
        params["type"] = op_type
        return min_time
    

class GemmKernelProfiler(KernelProfiler):
    def __init__(self, target_info: Target, database_path: str):
        super().__init__(target_info, database_path)
    
    def profile(self, candidate_kernel) -> float:
        if candidate_kernel.get_params() is None \
            or self.target_info.get_target_device_name() not in ["v100", "a100", "a5000"] \
            or candidate_kernel.get_params()["type"] != "matmul":
            return INF
        
        params = candidate_kernel.get_params()
        shape_a, shape_b = tuple(params["shapea"]), tuple(params["shapeb"])
        if len(shape_a) != len(shape_b):
            shape_a = (1, prod(shape_a[:-1]), shape_a[-1])
            shape_b = (1, shape_b[0], prod(shape_b[1:]))
        else:
            shape_a = (prod(shape_a[:-2]), shape_a[-2], shape_a[-1])
            shape_b = (prod(shape_b[:-2]), shape_b[-2], shape_b[-1])
            assert shape_a[0] == shape_b[0]
        
        result = profile_gemm(shape_a[0], shape_a[1], shape_b[2], shape_a[2], params["transa"], params["transb"], self.target_info.get_target_device_name() == "a100") # only enable tensor core on A100
        return result
