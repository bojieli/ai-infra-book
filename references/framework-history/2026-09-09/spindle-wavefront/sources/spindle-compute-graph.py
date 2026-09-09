from typing import List, Dict, Tuple, Any
import math

class LayerInfo():
    def __init__(self, layername, bsz, seqlen, hidden, time_func_type, popt, time_func, time_inv_func):
        # Assume Time-FLOPs satisfy: Time(ms) = A * f(TFLOPs) + D
        # Here f stands for FLOPs <per layer per gpu>
        # self.A, self.D = 0.15, 7.5e-3
        # for modality in popt:
        #     if modality in layername:
        #         self.A, self.D = popt[modality]
        #         break
        
        self.time_func_type = time_func_type
        self.popt = popt
        self.time_func = time_func
        self.time_inv_func = time_inv_func
        
        self.layername = layername
        self.bsz = bsz
        # Assume FLOPs <per layer per data> = 12(6sh^2+s^2h)
        self.FLOPs = 12 * (6 * seqlen * hidden**2 + seqlen**2 * hidden) * 10**(-12) # (TFLOPs) <per layer>
    
    def _local_bsz(self, gpu_num):
        return math.ceil(self.bsz / gpu_num)
    
    def _flops(self, gpu_num): # return FLOPs per layer per gpu
        return self._local_bsz(gpu_num) * self.FLOPs
        
    def cal_time(self, local_bsz: float):
        return self.time_func(local_bsz)
    
    def cal_flops_efficiency(self, gpu_num): # cal_time is (ms), flops_efficiency is (FLOPs/s)
        return self._flops(gpu_num) / self.cal_time(self._local_bsz(gpu_num)) * 1000
    
    def cal_time_inv(self, time: float):
        return self.time_inv_func(time)
    
    @property
    def time_lower_bound(self):
        return self.time_func(0)

class LayerNode():
    def __init__(self, layername: str, layer_config: Dict[str, Any], op_idx: int=0, bsz_multiply: int=1, ga_step: int=1):
        self.layerinfo = LayerInfo(
            layername, layer_config.get("batch_size") * bsz_multiply // ga_step, layer_config.get("seq_len", 0), layer_config.get("hidden_size", 0),
            layer_config["time_func_type"], layer_config["popt"], layer_config["time_func"], layer_config["time_inv_func"]
        )
        
        self.layername = layername
        self.in_edges = list()
        self.out_edges = list()
        self.node_level = layer_config.get("level", 0)
        
        self.in_edges: List[LayerNode]
        self.out_edges: List[LayerNode]
        
        self.op_idx = op_idx
        self.idx_in_name = 0
        self.layernum = layer_config["layer_num"]
        self.remain_work = self.work
        self.remain_time = 0.
        self.remain_layernum = self.layernum
        self.gpunum_opt = 0.
        self.valid_gpunum = None
    
    def __str__(self) -> str:
        return f"LayerNode[{self.op_idx}] \"{self.layername}\" with [in_deg, out_deg, layer_num] = [{self.in_degree}, {self.out_degree}, {self.layernum}]"
    
    def __repr__(self):
        return str(self)
    
    @property
    def in_degree(self) -> int:
        return len(self.in_edges)
    
    @property
    def out_degree(self) -> int:
        return len(self.out_edges)

    # Sign whether the layernode can be scheduled in this micro-stage
    # It is prepared iff all its src nodes have 0 remain_layernums (including the case of 0 src nodes)
    # For in the process of micro-stage partition, nodes in schedule_place may still have working nodes ahead
    @property
    def is_prepared(self) -> bool: 
        sign = True
        for src_node in self.in_edges:
            if src_node.remain_layernum != 0:
                sign = False
                break
        return sign
    
    def short_name(self):
        if "|" in self.layername: # OFASys
            name = self.layername.split("|")
            return name[0][:2] + "-" + { "image_vit": "0", "transformer_encoder": "1", "transformer_decoder": "2" }[name[1]]
        if "_" in self.layername: # multitask-CLIP
            name = self.layername.split("_")
            taskname = "".join(name[0].split("-"))
            opname = { "text": "L", "vision": "V", "audio": "A", "imu": "I", "depth": "D", "thermal": "T" }[name[1]]
            return taskname + "-" + opname
        # QWen
        name = self.layername.split("-")
        return name[0] + "-" + name[1][:1]

    def format_name(self):
        self.idx_in_name += 1
        return f"{self.layername}_{self.idx_in_name-1}"
    
    def refresh_states(self):
        self.layernum = self.remain_layernum
        self.remain_work = self.work
        self.remain_time = 0.
        self.gpunum_opt = 0.
    
    def set_remain_time(self, C):
        self.remain_time = C
    
    def update_remains(self, time: float, gpunum: int, layernum: int) -> None:
        self.remain_work -= time * self.speedup(gpunum)
        assert self.remain_work >= -1e8
        self.remain_time -= time
        self.remain_layernum -= layernum
    
    def set_gpunum_opt(self, C: float) -> None:
        self.gpunum_opt = self.gpunum_linear(C)
    
    def get_time(self, gpu_num: int, layer_num: int=None) -> float:
        if gpu_num == 0:
            return 0
        layer_num = self.remain_layernum if layer_num is None else layer_num
        return self.layerinfo.cal_time(self.layerinfo._local_bsz(gpu_num)) * layer_num
    
    def get_mcu(self, gpu_num, gpu_flops=312):
        return self.layerinfo.cal_flops_efficiency(gpu_num) / gpu_flops
    
    @property
    def min_time(self): # for planner::cal_minimized_time
        return self.L * self.layerinfo.time_lower_bound
    
    @property
    def max_time(self): # for planner::cal_minimized_time
        return self.get_time(gpu_num=1)
    
    @property
    def B(self):
        return self.layerinfo.bsz
    
    @property
    def L(self):
        return self.layernum
    
    @property
    def work(self):
        return self.processing_time(1)
    
    def update_valid_gpunum(self, world_size: int, strategy: str="batch divisible"):
        self.valid_gpunum = list()
        if strategy == "batch divisible":
            for i in range(world_size+1):
                if i == 0 or self.B % i == 0:
                    self.valid_gpunum.append(i)
        elif strategy == "consecutive integers":
            for i in range(world_size+1):
                self.valid_gpunum.append(i)
        else:
            raise NotImplementedError
    
    def get_next_valid_gpunum(self, gpunum: int) -> int:
        assert self.valid_gpunum is not None
        for idx in range(len(self.valid_gpunum)):
            if self.valid_gpunum[idx] > gpunum:
                return self.valid_gpunum[idx]
        return 0
        # idx = self.valid_gpunum.index(gpunum)
        # return self.valid_gpunum[idx+1]
    
    def get_prev_valid_gpunum(self, gpunum: int) -> int:
        assert self.valid_gpunum is not None
        for idx in reversed(range(len(self.valid_gpunum)-1)):
            if self.valid_gpunum[idx] < gpunum:
                return self.valid_gpunum[idx]
        return 0
        
    def find_valid_gpunum_pair(self, gpunum: float) -> Tuple[int, int]:
        if gpunum >= self.valid_gpunum[-1]:
            return math.floor(gpunum), math.ceil(gpunum)
        assert gpunum >= 0 and gpunum <= self.valid_gpunum[-1] # leave corner case to complete        
        
        for i in range(len(self.valid_gpunum)):
            if self.valid_gpunum[i] <= gpunum and gpunum < self.valid_gpunum[i+1]:
                return self.valid_gpunum[i], self.valid_gpunum[i+1]
        assert False
    
    def processing_time(self, gpunum: int) -> float:
        assert gpunum >= 0
        return self.layerinfo.cal_time(self.B/gpunum) * self.L
    
    def _speedup(self, gpunum: int) -> float:
        assert gpunum >= 0
        if gpunum == 0:
            return 0
        return self.processing_time(1) / self.processing_time(gpunum)
    
    def speedup(self, gpunum: float) -> float:
        n1, n2 = self.find_valid_gpunum_pair(gpunum)
        assert n1 <= n2
        # reduce speedup function to a piecewise lienar function
        if n1 == n2:
            return self._speedup(n1)
        else:
            return ((n2-gpunum)*self._speedup(n1) + (gpunum-n1)*self._speedup(n2)) / (n2-n1)
    
    # C: processing time
    # n1, n2: gpunum interval endpoints
    # n_linear: gpunum for the extended piecewise linear speedup function w.r.t. work and C
    def gpunum_interval(self, C: float) -> Tuple[int, int]:
        # gpunum for the extended analytical speedup function
        local_bsz = self.layerinfo.cal_time_inv(C/self.L)
        gpunum = self.B / local_bsz
        n1, n2 = self.find_valid_gpunum_pair(gpunum)
        return n1, n2
    
    def gpunum_linear(self, C: float) -> float:
        n1, n2 = self.gpunum_interval(C)
        if n1 == n2:
            return n2
        s1, s2 = self.speedup(n1), self.speedup(n2)
        n_linear = ((n2-n1) * self.work/C - n2*s1 + n1*s2) / (s2 - s1)
        return n_linear
    
    def time_pair(self, C: float) -> Tuple[float, float]:
        (n1, n2), n = self.gpunum_interval(C), self.gpunum_linear(C)
        if n1 == n2:
            return 0, C
        t1, t2 = (n2 - n)/(n2 - n1) * C * (n1 != 0), (n - n1)/(n2 - n1) * C
        return t1, t2
    
    def cal_layernum(self, time: float, gpunum: int) -> float:
        L = time / self.get_time(gpunum, 1) if gpunum > 0 else 0
        return L


class TaskNode():
    def __init__(self, taskname: str, layernode_list: List[LayerNode], task_id: int=0):
        self.taskname = taskname
        self.layernode_list = layernode_list
        self.task_id = task_id
        
        self.valid_gpunum = None
        self.bsz_gcd = None
    
    def get_time(self, gpu_num: int) -> float:
        if gpu_num == 0:
            return 0
        total_time = 0.
        for layernode in self.layernode_list:
            total_time += layernode.get_time(gpu_num)
        return total_time

    def __str__(self) -> str:
        return f"TaskNode[{self.task_id}] \"{self.taskname}\""

    @property
    def B(self) -> int:
        return self.bsz_gcd
    
    def update_valid_gpunum(self, world_size: int, strategy: str="batch divisible"):
        B_gcd = self.layernode_list[0].B
        for layernode in self.layernode_list:
            B_gcd = math.gcd(B_gcd, layernode.B)
        self.bsz_gcd = B_gcd
        
        self.valid_gpunum = list()
        if strategy == "batch divisible":
            for i in range(world_size+1):
                if i == 0 or self.B % i == 0:
                    self.valid_gpunum.append(i)
        elif strategy == "consecutive integers":
            for i in range(world_size+1):
                self.valid_gpunum.append(i)
        else:
            raise NotImplementedError
        
        self.valid_gpunum.append(0)
        # two 0s are guards of array valid_gpunum
    
    def get_next_valid_gpunum(self, gpunum: int) -> int:
        assert self.valid_gpunum is not None
        for idx in range(len(self.valid_gpunum)):
            if self.valid_gpunum[idx] > gpunum:
                return self.valid_gpunum[idx]
        return 0
        # idx = self.valid_gpunum.index(gpunum)
        # return self.valid_gpunum[idx+1]
    
    def get_prev_valid_gpunum(self, gpunum: int) -> int:
        assert self.valid_gpunum is not None
        for idx in reversed(range(len(self.valid_gpunum)-1)):
            if self.valid_gpunum[idx] < gpunum:
                return self.valid_gpunum[idx]
        return 0


class ComputeGraph():
    def __init__(self):
        self.nodes = dict()
        self.all_node_num = 0
        
        self.nodes: Dict[str, LayerNode]
        
    def _add_node(self, layername, layer_config, bsz_multiply: int=1, ga_step: int=1):
        assert layername not in self.nodes
        self.nodes[layername] = LayerNode(layername, layer_config, op_idx=len(self.nodes)+1, bsz_multiply=bsz_multiply, ga_step=ga_step)
    
    def _add_edge(self, src_layername, dst_layername):
        assert src_layername in self.nodes
        assert dst_layername in self.nodes
        
        src_node, dst_node = self.nodes[src_layername], self.nodes[dst_layername]
        src_node.out_edges.append(dst_node)
        dst_node.in_edges.append(src_node)
    
    def shrink_graph(self) -> None:
        # currently do nothing
        pass
    
    def build_graph(self, layerconfig_dict: Dict, layer_conns: List[Tuple[str, str]], bsz_multiply: int=1, ga_step: int=1) -> None:
        for layername in layerconfig_dict:
            self._add_node(layername, layerconfig_dict[layername], bsz_multiply=bsz_multiply, ga_step=ga_step)
        
        for conn in layer_conns:
            self._add_edge(*conn)
        
        self.shrink_graph()
        self.all_node_num = len(self.nodes)
    
    def top_nodes(self) -> List[LayerNode]:
        candidate_set = list()
        for layernode in self.nodes.values():
            if layernode.in_degree == 0:
                candidate_set.append(layernode)
        
        return candidate_set
    
    def first_level_nodes(self) -> List[LayerNode]:
        candidate_set = list()
        if self.is_empty():
            return candidate_set
        
        lvl = min([layernode.node_level for layernode in self.nodes.values()])
        for layernode in self.nodes.values():
            if layernode.node_level == lvl:
                candidate_set.append(layernode)
        
        return candidate_set
    
    def pop_nodes(self) -> List[LayerNode]:
        popped_nodes = list()
        for layernode in self.nodes.values():
            if layernode.remain_layernum == 0 and layernode.in_degree == 0: # finished execution
                popped_nodes.append(layernode)
                for dst_node in layernode.out_edges:
                    dst_node.in_edges.remove(layernode)
                layernode.out_edges.clear()
        
        for popped_node in popped_nodes:
            self.nodes.pop(popped_node.layername)
        
        return popped_nodes

    def is_empty(self) -> bool:
        return not bool(self.nodes)
    
    def refresh_nodes(self):
        for layernode in self.nodes.values():
            layernode.refresh_states()
    
    def compile_task(self, task_layername_map: Dict[str, List[str]]):
        self.task: Dict[str, TaskNode] = dict()
        for taskname, layernames in task_layername_map.items():
            assert taskname not in self.task
            layernode_list = list()
            for layername in layernames:
                assert layername in self.nodes
                layernode_list.append(self.nodes[layername])
            self.task[taskname] = TaskNode(taskname, layernode_list, len(self.task)+1)
