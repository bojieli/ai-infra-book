import argparse
import onnx
import onnx_graphsurgeon as gs
from typing import Optional
from sortedcontainers import SortedSet
from tqdm import tqdm
import pulp
import os
from collections import defaultdict


from utils import Target, GraphConfig, sanitize_prepare_args
from profiler import KernelProfiler, TensorRTKernelProfiler, MemBoundKernelProfiler, ConvKernelProfiler, GemmKernelProfiler, INF
from codegen import CodeGenerator


class GraphAnalyzer:
    def __init__(self, graph: gs.Graph):
        self.graph = graph
        self.execution_states = SortedSet()
        self.output2node = dict()

        # Extract constant nodes
        self.consts = set()
        for node in graph.nodes:
            if node.op == "Constant":
                self.consts.add(node.outputs[0].name)
    
    def get_graph(self):
        return self.graph
    
    def get_output2node(self):
        return self.output2node

    def get_consts(self):
        return self.consts


    def collect_execution_states(self):
        cur = set() # current execution state
        for tensor in self.graph.inputs:
            cur.add(tensor.name)
        self.execution_states.add(str(sorted(cur)))
        self._dfs(1, cur)
        D = [set(eval(x)) for x in self.execution_states]
        return D
    

    def _dfs(self, depth: int, cur: set):
        for node in self.graph.nodes:
            if len(node.inputs) == 0:
                continue
            prepared = True
            for tensor in node.inputs:
                if not isinstance(tensor, gs.Constant) and tensor.name not in self.consts and tensor.name not in cur and tensor.shape:
                    prepared = False
                    break
            if prepared:  # all dependencies have been calculated
                assert len(node.outputs) == 1  # only consider operators with 1 output for now
                tensor = node.outputs[0]
                if tensor.name not in cur:
                    self.output2node[tensor.name] = node
                    cur.add(tensor.name)
                    s = str(sorted(cur))
                    if s not in self.execution_states:
                        self.execution_states.add(s)
                        self._dfs(depth + 1, cur)
                    cur.remove(tensor.name)



class CandidateKernel:
    def __init__(self, nodes: list, graph_analyzer: GraphAnalyzer):
        self.nodes = nodes
        self.graph_analyzer = graph_analyzer
        self.params = None
        self.onnx_name = None
        self.onnx_path = None
        self.onnx_graph = None
    
    def get_nodes(self):
        return self.nodes
    
    def get_params(self):
        return self.params

    def get_onnx_name(self):
        return self.onnx_name
    
    def set_onnx_name(self, onnx_name: str):
        self.onnx_name = onnx_name

    def get_onnx_path(self):
        return self.onnx_path

    def set_onnx_path(self, onnx_path: str):
        self.onnx_path = onnx_path

    def get_onnx_graph(self):
        return self.onnx_graph
    
    def set_onnx_graph(self, onnx_graph: gs.Graph):
        self.onnx_graph = onnx_graph

    def pruning_check(self) -> bool:
        """
        Return whether the given kernel should be preserved.
        If it is a valid compute-bound kernel, `dict` of parameters will be added to the instance attributes.
        """
        compute_bound = 0
        for tensor in self.nodes:
            output2node = self.graph_analyzer.get_output2node()
            if output2node[tensor].op in ["MatMul", "Conv", "Gemm"]:
                compute_bound += 1
                op = output2node[tensor].op
                if compute_bound > 1:
                    return False
        if compute_bound == 1:
            if op == "Conv":
                if len(self.nodes) > 1: # TODO: conv + relu
                    return False
                conv = output2node[next(iter(self.nodes))] # conv must be the first node
                kernel_size = conv.attrs["kernel_shape"]
                assert kernel_size[0] == kernel_size[1]
                stride = conv.attrs["strides"]
                assert stride[0] == stride[1]
                pad = conv.attrs["pads"]
                assert pad[0] == pad[1] == pad[2] == pad[3]
                dilation = conv.attrs["dilations"]
                assert dilation[0] == dilation[1]
                params = {
                    "type": "conv", "batch_size": conv.inputs[0].shape[0],
                    "in_channels": conv.inputs[0].shape[1], "in_height": conv.inputs[0].shape[2],
                    "in_width": conv.inputs[0].shape[3], "out_channels": conv.inputs[1].shape[0],
                    "kernel_size": kernel_size[0], "stride": stride[0], "padding": pad[0],
                    "dilation": dilation[0], "groups": conv.attrs["group"],
                    "mode": 0 if len(conv.inputs) == 2 else 1}
                self.params = params
                return True
            elif op == "MatMul":
                # TODO: more cases of matmul
                if len(self.nodes) > 1:
                    return False
                matmul = output2node[next(iter(self.nodes))]
                shape_a, shape_b = [x.shape for x in matmul.inputs]
                params = {"type": "matmul", "transa": False, "transb": False, "shapea": shape_a, "shapeb": shape_b}
                self.params = params
                return True
            elif op == "Gemm":
                gemm = output2node[next(iter(self.nodes))]
                if len(self.nodes) > 1:
                    return False
                shape_a, shape_b = [gemm.inputs[i].shape for i in range(2)]
                transa = False if "transA" not in gemm.attrs else gemm.attrs["transA"] == 1
                transb = False if "transB" not in gemm.attrs else gemm.attrs["transB"] == 1
                params = {"type": "matmul", "transa": transa, "transb": transb, "shapea": shape_a, "shapeb": shape_b}
                self.params = params
                return True
            else:
                return False
        return True


    def export_candidate_kernel_graph(self) -> Optional[gs.Graph]:
        """
            If given candidate kernel is valid, set and return its `gs.Graph`. Otherwise return `None`.
        """
        subgraph = self.graph_analyzer.get_graph().copy()
        subgraph.inputs, subgraph.outputs = [], []
        nodes = []
        cur_node = None
        tensor_map = subgraph.tensors()
        for tensor_name in self.nodes:
            # find the corresponding node
            for node in subgraph.nodes:
                if node.outputs[0].name == tensor_name:
                    cur_node = node
                    break
            nodes.append(cur_node)
            # find inputs
            for tensor in cur_node.inputs:
                if not isinstance(tensor, gs.Constant) and tensor.name not in self.graph_analyzer.get_consts() and tensor.name not in self.nodes and tensor not in subgraph.inputs and tensor.shape:
                    subgraph.inputs.append(tensor)
            if cur_node.outputs[0].name not in self.nodes:
                subgraph.outputs.append(tensor)
        # find outputs
        for tensor_name in self.nodes:
            is_output = True
            for node in nodes:
                for tensor in node.inputs:
                    if tensor.name == tensor_name:
                        is_output = False
            if is_output:
                if len(subgraph.outputs) != 0: # multiple outputs
                    return None
                subgraph.outputs.append(tensor_map[tensor_name])
        subgraph.cleanup(True, True, True)
        
        self.set_onnx_graph(subgraph)
        return subgraph

    def export_to_file(self, path: str=None):
        if path == None or path == "":
            path = self.get_onnx_path()
        # if path not exist, create it
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        onnx.save(gs.export_onnx(self.get_onnx_graph()), path)
    
    def profile_best_latency(self, profilers: list[KernelProfiler]) -> float:
        min_time = INF
        for profiler in profilers:
            latency = profiler.profile(self)
            min_time = min(min_time, latency)
        return min_time            


class KernelOrchestrationSolver:
    def __init__(self, K: list[CandidateKernel], latencies: list[float], graph_analyzer: GraphAnalyzer):
        self.graph_analyzer = graph_analyzer
        self.name2id = dict()
        self.K = K
        self.latencies = latencies

    def _visit(self, name: str) -> int:
        if name not in self.name2id:
            self.name2id[name] = len(self.name2id)
        return self.name2id[name]

    def _get_inputs(self, graph: gs.Graph) -> list[int]:
        ret = []
        for tensor in graph.inputs:
            if tensor.name not in self.graph_analyzer.get_consts():
                ret.append(self._visit(tensor.name))
        return ret
    
    class Solution:
        def __init__(self, graph, selected_kernels, latency):
            self.graph = graph
            self.latency = latency
            self.selected_kernels = selected_kernels
            self.execution_graph = defaultdict(list)
            for i in range(len(selected_kernels)):
                current_kernel_graph = selected_kernels[i].get_onnx_graph()
                # if subgraph A's input is in another subgraph B's output, add edge: B -> A
                for input_tensor in current_kernel_graph.inputs:
                    for j in range(len(selected_kernels)):
                        if i != j and input_tensor.name == selected_kernels[j].get_onnx_graph().outputs[0].name:
                            self.execution_graph[j].append(i)
            self.execution_order = self.topologicalSort(len(selected_kernels))
            # Find out the lifetime of each kernel's output tensor
            self.kernel_output_lifetimes = [[] for _ in range(len(self.execution_order))] # the list of kernel ids at index i refers to kernels whose outputs can be removed from CUDA memory after the i-th kernel is executed
            self.deduce_lifetimes()
    
        # A recursive function used by topologicalSort
        def topologicalSortUtil(self, v, visited, stack):
            visited[v] = True
            for i in self.execution_graph[v]:
                if visited[i] == False:
                    self.topologicalSortUtil(i,visited,stack)
            stack.insert(0,v)
    
        def topologicalSort(self, V):
            visited = [False]*V
            stack =[]
            for i in range(V):
                if visited[i] == False:
                    self.topologicalSortUtil(i,visited,stack)
            return stack

        def deduce_lifetimes(self):
            execution_order_dict = dict() # kernel id -> its position in the execution order
            for i in range(len(self.execution_order)):
                execution_order_dict[self.execution_order[i]] = i
            for kernel_id in self.execution_order:
                children_kernel_ids = self.execution_graph[kernel_id]
                if len(children_kernel_ids) == 0:
                    # We do not calculate lifetime for the last kernel's output tensor. 
                    continue
                farthest_child = max(children_kernel_ids, key=lambda x: execution_order_dict[x])
                farthest_child_order = execution_order_dict[farthest_child]
                self.kernel_output_lifetimes[farthest_child_order].append(kernel_id)
        
        def get_graph(self):
            return self.graph

        def get_latency(self):
            return self.latency
        
        def get_selected_kernels(self):
            return self.selected_kernels
        
        def get_execution_order(self):
            return self.execution_order
        
        def get_kernel_output_lifetimes(self):
            return self.kernel_output_lifetimes
        

    def solve(self) -> Solution:
        graph = self.graph_analyzer.get_graph()
        graph_inputs = self._get_inputs(graph)
        inputs = []
        outputs = []
        for candidate_kernel in self.K:
            candidate_kernel_graph = candidate_kernel.get_onnx_graph()
            inputs.append(self._get_inputs(candidate_kernel_graph))
            outputs.append(self._visit(candidate_kernel_graph.outputs[0].name))
        
        bp = pulp.LpProblem("BinaryProgramming")
        a = [pulp.LpVariable(f"a{i}", cat="Binary") for i in range(len(self.K))]
        bp += (sum([self.latencies[i] * a[i] for i in range(len(self.K))]))
        b = []
        for _, id in self.name2id.items():
            if id in graph_inputs:
                b.append(1)
            else:
                b.append(0)
                for i in range(len(self.K)):
                    if outputs[i] == id:
                        b[id] += a[i]
        for tensor in graph.outputs:
            bp += (b[self.name2id[tensor.name]] >= 1)
        for name, id in self.name2id.items():
            for i in range(len(self.K)):
                if id in inputs[i]:
                    bp += (b[id] >= a[i])
        bp.solve(pulp.PULP_CBC_CMD(maxSeconds=1000, msg=1, fracGap=0))

        selected_kernels = []
        for v in bp.variables():
            if v.varValue == 1:
                id = int(v.name[1:])
                selected_kernel = self.K[id]
                # selected_kernel = (selected_kernel.get_onnx_graph(), selected_kernel.get_params(), selected_kernel.get_onnx_name())
                selected_kernels.append(selected_kernel)
        
        overall_latency = bp.objective.value()
        print("Current latency: ", overall_latency)
        return KernelOrchestrationSolver.Solution(graph, selected_kernels, overall_latency)
    

def main(input_args: argparse.Namespace, target_info: Target, config: GraphConfig) -> None:
    onnx_graph = gs.import_onnx(onnx.load(input_args.model))
    if config.graph_partition is None:
        config.cut_points = [([tensor.name for tensor in onnx_graph.inputs], [tensor.name for tensor in onnx_graph.outputs])]
    e2e_latencies = []
    for subgraph_id, (inputs, outputs) in enumerate(config.cut_points):
        if config.specified_subgraph is not None and subgraph_id != config.specified_subgraph:
            continue
        # Cleanup the onnx computation graph
        graph = onnx_graph.copy()
        tensors = graph.tensors()
        for tensor_name in tensors:
            tensors[tensor_name].name = tensor_name.replace('.', '_')
        graph.inputs = [tensors[input] for input in inputs]
        graph.outputs = [tensors[output] for output in outputs]
        graph.cleanup(True, True, True)
        
        # Calculate candidate kernels
        K = []
        graph_analyzer = GraphAnalyzer(graph)
        if subgraph_id in config.full_graph:
            # Entire subgraph is a candidate kernel
            k = CandidateKernel(graph.nodes, None)
            k.set_onnx_graph(graph)
            K.append(k)
            k.set_onnx_name(str(len(K)))
            onnx_path = os.path.join(input_args.database_dir, f"subgraph{subgraph_id}", "candidate_kernel_graphs", f"{k.get_onnx_name()}.onnx")
            k.set_onnx_path(onnx_path)
            k.export_to_file()   
        else:
            # Calculate execution states
            D = graph_analyzer.collect_execution_states()
            print(f"Number of execution states: {len(D)}")

            # Deduce candidate kernels, extra information is added to the valid kernel's instance attributes
            for i in tqdm(range(len(D))):
                for j in range(len(D)):
                    if i != j and D[i].issubset(D[j]):
                        k = CandidateKernel(D[j] - D[i], graph_analyzer)
                        preserve = k.pruning_check()
                        if preserve:
                            candidate_kernel_graph = k.export_candidate_kernel_graph()
                            if candidate_kernel_graph is not None:
                                K.append(k)
                                k.set_onnx_name(str(len(K)))
                                onnx_path = os.path.join(input_args.database_dir, f"subgraph{subgraph_id}", "candidate_kernel_graphs", f"{k.get_onnx_name()}.onnx")
                                k.set_onnx_path(onnx_path)
                                k.export_to_file()
        print(f"Number of candidate kernels: {len(K)}")

        # Profile latencies of candidate kernels using different profilers
        kernel_profiler_database_path = os.path.join(input_args.database_dir, f"subgraph{subgraph_id}")
        trt_profiler = TensorRTKernelProfiler(target_info, kernel_profiler_database_path)
        membound_profiler = MemBoundKernelProfiler(target_info, kernel_profiler_database_path)
        conv_profiler = ConvKernelProfiler(target_info, kernel_profiler_database_path)
        gemm_profiler = GemmKernelProfiler(target_info, kernel_profiler_database_path)

        candidate_kernels_latencies = []
        for k in tqdm(K):
            latency = k.profile_best_latency([membound_profiler, conv_profiler, gemm_profiler])
            candidate_kernels_latencies.append(latency) 

        # Build and solve binary programming
        korch_solver = KernelOrchestrationSolver(K, candidate_kernels_latencies, graph_analyzer)
        korch_solution = korch_solver.solve()
        e2e_latencies.append(korch_solution.get_latency())
        selected_kernel_info = [(x.get_onnx_graph(), x.get_params(), x.get_onnx_name()) for x in korch_solution.get_selected_kernels()]
        print(f"Selected Kernels: {[selected_kernel_info[x][2] for x in korch_solution.get_execution_order()]}")
        print(f"Latencies: {[candidate_kernels_latencies[int(selected_kernel_info[x][2]) - 1] for x in korch_solution.get_execution_order()]}")

        if input_args.code_output_dir is not None:
            # print out a clear line indicating the rest of the print out are codegen related
            print("-------------------------------------------------CodeGen-------------------------------------------------")
            # print(f"execution_order: {korch_solution.get_execution_order()}")
            # print(f"kernel_output_lifetimes: {korch_solution.get_kernel_output_lifetimes()}")
            codegen = CodeGenerator(
                korch_solution.get_execution_order(),
                selected_kernel_info,
                korch_solution.get_kernel_output_lifetimes(),
                graph,
                input_path=os.path.join(input_args.database_dir, f"subgraph{subgraph_id}", "lib_export"),
                output_path=os.path.join(input_args.code_output_dir, f"subgraph{subgraph_id}", "forward_pass.cu")
            )
            codegen.generate_code()

    print("Overall latency:", sum(e2e_latencies))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Korch: Optimal Kernel Orchestration")
    parser.add_argument("model", type=str, help="path to the input model in ONNX format")
    parser.add_argument("device", type=str, help="target device (e.g., v100, a100, a5000)")
    parser.add_argument("--config", type=str, help="path to the configuration file")
    parser.add_argument("--database_dir", type=str, help="directory to store the intermeidate results")
    parser.add_argument("--code_output_dir", type=str, help="directory to store the generated code. If not specified, no codegen")
    args = parser.parse_args()

    args, config, target_info = sanitize_prepare_args(args)

    main(args, target_info, config)
