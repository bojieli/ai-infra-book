from typing import Tuple, List, Dict, Any, Literal
import copy
import math
import numpy as np
from functools import cmp_to_key
from pprint import pprint
import random
import matplotlib.pyplot as plt

from galvatron.core import ComputeGraph, LayerNode, RectPlace, SchedulePlace, draw_rects_schedule, draw_rects


def float_eq(a: float, b: float) -> bool:
    return abs(a-b) <= 1e-2

def float_lt(a: float, b: float) -> bool:
    return a < b and not float_eq(a, b)

def float_leq(a: float, b: float) -> bool:
    return a < b or float(a, b)


# StageOp type == LayerType (Maybe extend to StageOp type >= LayerType afterwards)
def build_graph(layerconfig_dict, layer_conns, bsz_multiply=1, ga_step=1):
    graph = ComputeGraph()
    graph.build_graph(layerconfig_dict, layer_conns, bsz_multiply, ga_step)
    return graph

class Planner():
    def __init__(
        self,
        world_size: int,
        graph: ComputeGraph,
        candidate_sel_rule: Literal["indegree", "level", "all"]="indegree",
        global_optimization: bool=False,
        valid_gpunum_strategy: Literal["batch divisible", "consecutive integers"]="batch divisible",
        sort_rule: Literal["smallN", "smallT", "bigN_smallT", "bigN_bigT"]="bigN_bigT", # sorting rule for StageOp selection in global opt.
        extend_rule: Literal[None, "bigRW_", "_bigST", "bigRW_bigST", "bigRT_", "bigRT_bigST"]=None, # specify layernum and gpuunum extension rule respectively
        device_map_level: Literal[0, 1, 2]=0,
        decoder_opt: bool=False,
        ga_step: int=1,
        group_opnum_limit: int=0,
        solver_path: str=None,
        bsz_divisible_by_gpunum: bool=False,
        naive: bool=False,
        threshold_policy: bool=False,
        threshold: float=1.0,
        low_MCU_layer_first: bool=False,
        logging: bool=False,
        draw_rects: bool=False,
        fig_path: str=None,
    ):
        self.world_size = world_size
        self.graph = graph
        self.candidate_sel_rule = candidate_sel_rule
        self.global_optimization = global_optimization
        self.valid_gpunum_strategy = valid_gpunum_strategy
        self.sort_rule = sort_rule
        self.extend_rule = extend_rule
        self.device_map_level = device_map_level
        self.decoder_opt = decoder_opt
        # self.enable_time_slice = enable_time_slice
        self.ga_step = ga_step
        self.group_opnum_limit = group_opnum_limit
        self.solver_path = solver_path
        self.bsz_divisible_by_gpunum = bsz_divisible_by_gpunum
        self.naive = naive
        self.logging = logging
        self.draw_rects = draw_rects
        self.fig_path = fig_path
        assert not draw_rects or (draw_rects and fig_path is not None)
        self.threshold_policy = threshold_policy
        self.threshold = threshold
        self.expected_MCU = 1.0
        self.low_MCU_layer_first = low_MCU_layer_first
        
        self.global_opt_makespan = 0. # Optimal C_max for global optimization[int gpunum, float layernum, float local bsz]
        
        # For greedy stage partition, only 0-indegree nodes can be selected into the candidate set
        if not global_optimization and candidate_sel_rule != "indegree":
            assert False, "For greedy stage partition, only 0-indegree nodes can be selected into the candidate set."
        
    def plan_stage(self, working_graph: ComputeGraph, stage_idx: int, start_time: float=0) -> Tuple[List[Dict[str, Dict]], float, List[SchedulePlace]]:
        if self.logging:
            print(f"======================== Stage {stage_idx} ========================")
        
        stage_time = 0.
        # Step 1: Fill the candidate set, getting StageOps from graph
        if self.candidate_sel_rule == "indegree": # in_degree == 0
            candidate_set = working_graph.top_nodes()
        elif self.candidate_sel_rule == "level": # smallest level
            candidate_set = working_graph.first_level_nodes()
        elif self.candidate_sel_rule == "all": # the whole graph
            candidate_set = list(working_graph.nodes.values())
        else:
            raise NotImplementedError(f"candidate selection rule in choices [indegree, level, all], but found {self.candidate_sel_rule}.")
        
        if self.logging:
            print("Step 1: candidate set is")
            pprint(candidate_set)

        if self.global_optimization:
            # a special flag for all decoders, we use optimus-style greedy algorithm on makespan to do resource allocation
            decoder_flag = self.decoder_opt and self.candidate_sel_rule == "level" and candidate_set[0].layername.endswith("transformer_decoder")
            
            for layernode in candidate_set:
                layernode.update_valid_gpunum(self.world_size, strategy=self.valid_gpunum_strategy)
            
            # Step 2: Do group partition, not allowing too many StageOps crowding in one macro stage
            # group_opnum_limit set to 0 for arbitrarily large group size
            opnum = len(candidate_set)
            group_size = self.group_opnum_limit if self.group_opnum_limit > 0 else opnum
            group_num = opnum // group_size
            remainder = opnum % group_size
            group_num += remainder>0
            group_size = opnum // group_num
            remainder = opnum % group_num
            group_sizes = [group_size] * (group_num - remainder) + [group_size + 1] * remainder
            
            # import random
            # random.shuffle(candidate_set)
            idx, groups = 0, list()
            for i in range(group_num):
                groups.append(candidate_set[idx:idx+group_sizes[i]])
                idx += group_sizes[i]
            
            # Step 3: Do micro-stage partition for each group
            if self.logging:
                print(f"Step 3: micro-stage partition for {len(groups)} group(s)")
            
            groups: List[List[LayerNode]]
            opnum, places = 0, list()
            wrapped_plan = list()
            for i, candidate_group in enumerate(groups):
                group_time = self.cal_minimized_time(candidate_group)
                
                if self.logging:
                    print(f"Group {i+1} minimized makespan is {group_time}")
                    
                data = list()
                schedule_data = list()
                
                if not decoder_flag:
                    time_slice = self.global_opt_makespan/len(candidate_group) * 0.5
                    for layernode in candidate_group:
                        n1, n2 = layernode.gpunum_interval(group_time)
                        t1, t2 = layernode.time_pair(group_time)
                        data.append([(n1,t1), (n2,t2)])
                        
                        l1f, l2f = layernode.cal_layernum(t1, n1), layernode.cal_layernum(t2, n2)
                        l1, l2 = round(l1f), round(l2f)
                        
                        # May face float precision problem, e.g. 0.50000000000000, 11.500000000000002
                        assert l1 >= 0 and l2 >= 0
                        if l1+l2 != layernode.L:
                            diff = layernode.L - (l1+l2)
                            if l1+l2 < layernode.L:
                                if n1 and l1:
                                    l1 += diff
                                else:
                                    l2 += diff
                            elif l1+l2 > layernode.L:
                                if n1 and l1:
                                    l1 += diff
                                else:
                                    l2 += diff
                        
                        assert l1+l2 == layernode.L, f"l1, l2 = {l1}, {l2}, but total layernum is {layernode.L}"
                        assert l1 >= 0 and l2 >= 0
                        
                        # if self.enable_time_slice:
                        #     if t1 < t2 and t1 < time_slice:
                        #         l1, l2 = 0, layernode.L
                        #     elif t2 < t1 and t2 < time_slice:
                        #         l1, l2 = layernode.L, 0
                        
                        t1, t2 = layernode.get_time(n1, l1), layernode.get_time(n2, l2)
                        # if layernode.layername.endswith("decoder"):
                        #     print(f"{layernode.short_name()}, {n1}:{l1}|{t1:.1f}, {n2}:{l2}|{t2:.2f}")
                        if n1 and l1:
                            schedule_data.append(SchedulePlace(layernode.op_idx, t1, n1, 0, 0, l1, layernode=layernode))
                        if n2 and l2:
                            schedule_data.append(SchedulePlace(layernode.op_idx, t2, n2, 0, 0, l2, layernode=layernode))

                    group_places, group_time, group_plan = self.schedule_gen(schedule_data, start_stage_idx=stage_idx)
                    
                    # Below are for rectangle packing algorithm
                    # First fill the BIG region with rectangles, then do stage partition on borders of rectangles
                    # group_places = self.rect_pack(data, group_time, candidate_set=candidate_group)
                    # group_places, group_time = self.stage_partition(group_places, group_time)
                    # Above are for rectangle packing algorithm
                else:
                    from .spindle_planner_decouple import TaskNode, TaskPlace, PlannerDecouple
                    
                    decoder_task_layername_map = {
                        layernode.layername: [layernode.layername] for layernode in candidate_group
                    }
                    # n = layernode.gpunum_opt
                    
                    working_graph.compile_task(decoder_task_layername_map)
                    task_planner = PlannerDecouple(
                        world_size=self.world_size,
                        graph=working_graph,
                        allotment_rule="optimus",
                        optimus_mode="makespan",
                        leverage_gpunum_opt=True,
                        ga_step=1
                    )
                    
                    task_plan, task_time = task_planner.plan_algorithm()
                    group_places, group_time, group_plan = list(), task_time, dict()
                    for tp in task_plan:
                        layername = tp["task"]
                        devices = tp["devices"]
                        exe_time = tp["exe_time"]
                        layernode = working_graph.nodes[layername]
                        execute_gpunum = len(devices)
                        group_plan[layernode.format_name()] = {
                            "short_name": layernode.short_name(),
                            "local_bsz": layernode.layerinfo._local_bsz(execute_gpunum),
                            "layer_num": layernode.L,
                            "exe_time": exe_time,
                            "mcu": f"{layernode.get_mcu(execute_gpunum, 156):.2%}",
                            "devices": devices
                        }

                        sp = SchedulePlace(layernode.op_idx, exe_time, execute_gpunum, 0, devices[0], layernode.L, stage_idx, layernode)
                        sp.affect_layernode()
                        group_places.append(sp)
                        
                    
                    group_plan = [{
                        "stage": stage_idx,
                        "plan": group_plan,
                        "time": task_time
                    }]
                    
                
                for p in group_places:
                    p.x, p.u = p.x + stage_time + start_time, p.u + stage_time + start_time
                opnum += group_sizes[i]
                places.extend(group_places)
                
                stage_time += group_time
                wrapped_plan.extend(group_plan)
            
            # Step 4: Parallelism Optimization for each StageOp in the working set
            # === pass now ===
            
            # Step 5: Pop out finished StageOp from the working graph
            # and refresh every alive StageOp's state for next loop of global optimization
            finished_nodes = working_graph.pop_nodes()
            working_graph.refresh_nodes()
            if self.logging:
                print("Step 5, removed nodes are")
                pprint(finished_nodes)
            return wrapped_plan, stage_time, places
        else:
            # Step 2: Resource allocation for each StageOp in the candidate set, can be zero for some StageOps
            resource_map, MCU = self.resource_alloc(candidate_set)
        
            if self.logging:
                print("Step 2: resource map is")
                pprint(resource_map)
                print(f"With estimated MCU {MCU}")
        
            # Add a threshold for the 1st stage
            if self.threshold_policy and idx == 1:
                self.expected_MCU = MCU * self.threshold
                resource_map, MCU = self.resource_alloc(candidate_set)
            
                if self.logging:
                    print("Step 2 [with threshold]: resource map is")
                    pprint(resource_map)
                    print(f"With estimated MCU {MCU}")
        
            # Step 3: Parallelism Optimization for each StageOp in the working set
            # === pass now ===

            # Step 4: Work: simulate to execute the working set until one StageOp is finished
            # We use mfu to calculate training time temporarily.
            # But it is worth noting that Step 4 will change the FLOPs-MFU curve, therefore, computing
            # training time through MFU is not accurate anymore, should be fixed afterwards.
            stage_plan, stage_time = self.gen_stage_plan(resource_map)
            if self.logging:
                print("Step 4: plan for this stage is")
                print(stage_plan)
                print(f"With stage time {stage_time}")
            
            # Step 5: Pop out finished StageOp from the working set, prepare to refill it in next loop
            finished_nodes = working_graph.pop_nodes()
            if self.logging:
                print("Step 5, removed nodes are")
                pprint(finished_nodes)

            wrapped_plan = [{
                "stage": stage_idx,
                "plan": stage_plan,
                "time": stage_time,
            }]
            return wrapped_plan, stage_time, None
    
    def plan_algorithm(self) -> Tuple[List[Dict[str, Any]], float]:        
        stage_idx = 1
        total_time = 0.
        plan = list()
        schedule = list()
        
        working_graph = copy.deepcopy(self.graph)
        while not working_graph.is_empty():
            wrapped_stage_plan, stage_time, stage_schedule = self.plan_stage(working_graph, stage_idx, total_time)
            micro_stage_num = len(wrapped_stage_plan)
            stage_idx += micro_stage_num
            total_time += stage_time
            
            plan.extend(wrapped_stage_plan)
            if self.global_optimization:
                schedule.extend(stage_schedule)
        
        # Generate rectangle schedule figure for greedy stage partition
        if not self.global_optimization:
            total_time = 0.
            
            for stage_plan in plan:
                used_gpunum = 0
                stage_idx, stage_time, real_plan = stage_plan["stage"], stage_plan["time"], stage_plan["plan"]
                for layer_name, layer_plan in real_plan.items():
                    execute_layer_num, execute_time, gpu_num = layer_plan["layer_num"], layer_plan["exe_time"], len(layer_plan["devices"])
                    
                    layernode = self.graph.nodes[layer_name.strip("_0123456789")]
                    correct_sp = SchedulePlace(layernode.op_idx, execute_time, gpu_num, total_time, used_gpunum, execute_layer_num, stage_idx, layernode)
                    schedule.append(correct_sp)
                    used_gpunum += gpu_num
                total_time += stage_time
        
        if self.draw_rects:
            draw_rects_schedule(schedule, self.graph.all_node_num)
            plt.savefig(self.fig_path)
            plt.clf()
            plt.close("all")
            
        return plan, total_time * self.ga_step
    
    def cal_minimized_time(self, candidate_set: List[LayerNode]) -> float:
        def _equation(C: float) -> float:
            nonlocal candidate_set
            sum = 0.
            for layernode in candidate_set:
                sum += layernode.gpunum_linear(C)
            return sum
        
        min_time = np.array([layernode.min_time for layernode in candidate_set])
        max_time = np.array([layernode.max_time for layernode in candidate_set])
        
        C_low, C_high = np.max(min_time), np.sum(max_time)
        
        while True:
            C_mid = (C_low + C_high) / 2
            res = _equation(C_mid)
            if res > self.world_size:
                C_low = C_mid
            elif res < self.world_size:
                C_high = C_mid
            else:
                break
            
            if C_high - C_low <= 1e-8:
                break
        
        self.global_opt_makespan = C_mid
        for layernode in candidate_set:
            layernode.set_remain_time(C_mid)
            layernode.set_gpunum_opt(C_mid)
        
        return C_mid
                    
    def rect_pack(self, data: List[List[Tuple[int, float]]], time: float, candidate_set: List[LayerNode]=None) -> List[RectPlace]:        
        places = list()
        places: List[RectPlace]
        w, h = 0., 0
        W, H = time, self.world_size
        for i in range(len(data)):
            (n1,t1), (n2,t2) = data[i]
            layernode = candidate_set[i] if candidate_set is not None else None
            
            if w == 0.:
                places.append(RectPlace(i, t2, n2, w, h, layernode))
                if n1 > 0:
                    places.append(RectPlace(i, t1, n1, w+t2, h, layernode))
                    h = h+n1
                w = t2
            else:
                if float_lt(w+t2, W):
                    places.append(RectPlace(i, t2, n2, w, h, layernode))
                    if n1 > 0:
                        places.append(RectPlace(i, W-(w+t2), n1, w+t2, h, layernode))
                        places.append(RectPlace(i, w, n1, 0, h+1, layernode))
                    w = w+t2
                    h = h+n1
                elif float_lt(W, w+t2):
                    places.append(RectPlace(i, W-w, n2, w, h, layernode))
                    places.append(RectPlace(i, t2-(W-w), n2, 0, h+1, layernode))
                    if n1 > 0:
                        places.append(RectPlace(i, t1, n1, t2-(W-w), h+1, layernode))
                    w = t2-(W-w)
                    h = h+n2
                else:
                    places.append(RectPlace(i, t2, n2, w, h, layernode))
                    if n1 > 0:
                        places.append(RectPlace(i, t1, n1, 0, h+1, layernode))
                    w = 0
                    h = h+n2
        
        def sort_places():
            def sort_func(a: RectPlace, b: RectPlace) -> int:
                if float_lt(a.x, b.x) or (float_eq(a.x, b.x) and float_lt(a.y, b.y)):
                    return -1
                elif float_eq(a.x, b.x) and float_eq(a.y, b.y):
                    return 0
                else:
                    return 1
            
            nonlocal places
            print("Before Sorted")
            for p in places:
                print(f"op {p.op_idx:<2}: start from ({p.x:<6.2f}, {p.y:<2}) with shape [{p.width:<6.2f}, {p.height:<2}]")
            places.sort(key=cmp_to_key(sort_func))
            print("After Sorted")
            for p in places:
                print(f"op {p.op_idx:<2}: start from ({p.x:<6.2f}, {p.y:<2}) with shape [{p.width:<6.2f}, {p.height:<2}]")
        
        # sort_places()
        return places
    
    def stage_partition(self, places: List[RectPlace], time: float) -> Tuple[List[RectPlace], float]:
        time_points = set()
        for p in places:
            time_points.add(p.x)
            time_points.add(p.u)
        time_points = sorted(list(time_points))
        merged_time_ints, merged_time_points = list(), list() # in case some time points are float-equal but not equal
        
        idx = 0
        while idx < len(time_points):
            t1 = time_points[idx]
            while idx+1 < len(time_points) and float_eq(time_points[idx], time_points[idx+1]):
                idx = idx+1
            t2 = time_points[idx]
            merged_time_ints.append((t1, t2))
            merged_time_points.append((t1+t2)/2)
            idx = idx+1
        
        def find_idx(t: float) -> int:
            nonlocal merged_time_ints
            for i in range(len(merged_time_ints)):
                if merged_time_ints[i][0] <= t and t <= merged_time_ints[i][1]:
                    return i
            assert False
            
        for i in range(len(places)):
            places[i].x = merged_time_points[find_idx(places[i].x)]
            places[i].u = merged_time_points[find_idx(places[i].u)]
        
        partitioned_places = list()
        for p in places:
            i1 = merged_time_points.index(p.x)
            i2 = merged_time_points.index(p.u)
            assert i1 < i2
            for i in range(i1, i2):
                partitioned_places.append(RectPlace(p.op_idx, merged_time_points[i+1]-merged_time_points[i], p.height, merged_time_points[i], p.y, p.layernode))
        
        return partitioned_places, merged_time_points[-1]

    # Extend the schedule placements to fullfill the GPU cluster
    def stage_extension(self, stage_schedule: List[SchedulePlace], stage_time: float, N_valid: int) -> None:
        while N_valid > 0:
            # Do layernum extension (along with gpunum expansion)
            stage_schedule: List[SchedulePlace]
            if self.extend_rule.startswith("bigRW"):
                stage_schedule.sort(key=lambda sp: sp.new_remain_work_nstar, reverse=True)
            elif self.extend_rule.startswith("bigRT"):
                stage_schedule.sort(key=lambda sp: sp.new_remain_time_nstar, reverse=True)
                
            extend_flag = False
            for sp in stage_schedule:
                gpunum = sp.scheduled_gpunum
                n1, n2 = sp.layernode.find_valid_gpunum_pair(gpunum)
                assert n1 == gpunum
                if n2-n1 > N_valid or sp.scheduled_layernum == sp.l or n1 == n2:
                    continue
                
                # Do the extension on this schedule placement in this stage
                extend_flag = True
                new_scheduled_layernum = min(sp.l, math.floor(stage_time / sp.layernode.get_time(n2, 1)))
                sp.set_scheduled(n2, new_scheduled_layernum)
                N_valid -= (n2 - n1)
                break
            
            # An layernum extension has been performed, continue to find other extensions
            if extend_flag:
                continue
            
            # No available layernum extension is performed, do gpunum extension only
            if self.extend_rule.endswith("bigST"):
                stage_schedule.sort(key=lambda sp: sp.scheduled_time, reverse=True)
            
            extend_flag = False
            for sp in stage_schedule:
                gpunum = sp.scheduled_gpunum
                n1, n2 = sp.layernode.find_valid_gpunum_pair(gpunum)
                assert n1 == gpunum
                if n2-n1 > N_valid or n1 == n2:
                    continue
                
                # Do the extension on this schedule placement in this stage
                extend_flag = True
                sp.set_scheduled(n2, sp.l)
                N_valid -= (n2 - n1)
                break
            
            # Even gpunum extension is not allowed, the stage extension process is over
            if not extend_flag:
                break
    
    def find_identical_allotment(self, stage_schedule: List[SchedulePlace], sp_to_match: SchedulePlace) -> int:
        for idx, sp in enumerate(stage_schedule):
            if sp.op_idx == sp_to_match.op_idx and sp.height == sp_to_match.height:
                return idx
        return -1
    
    def device_mapping(self, stage_schedule: List[SchedulePlace], last_stage_schedule: List[SchedulePlace]) -> List[SchedulePlace]:
        working_schedule = last_stage_schedule.copy()
        
        tmp_stage_schedule_forward, tmp_stage_schedule_backward = list(), list()
        for lsp in working_schedule:
            idx = self.find_identical_allotment(stage_schedule, lsp)
            if idx == -1:
                break
            sp = stage_schedule.pop(idx)
            tmp_stage_schedule_forward.append(sp)
        done_opnum_forward = len(tmp_stage_schedule_forward)
        working_schedule = working_schedule[done_opnum_forward:]
        
        for lsp in reversed(working_schedule):
            idx = self.find_identical_allotment(stage_schedule, lsp)
            if idx == -1:
                break
            sp = stage_schedule.pop(idx)
            tmp_stage_schedule_backward.append(sp)
        done_opnum_backward = len(tmp_stage_schedule_backward)
        tmp_stage_schedule_backward.reverse()
        
        if done_opnum_backward > 0:
            working_schedule = working_schedule[:-done_opnum_backward]
        
        last_map, i = list(), 0
        for sp in working_schedule:
            last_map.extend([(sp.op_idx, i, i+sp.scheduled_gpunum)]*sp.scheduled_gpunum)
            i += sp.scheduled_gpunum
        opnum = len(stage_schedule)
        gpunum = len(last_map)
        
        curr_map, i = list(), 0
        for sp in stage_schedule:
            curr_map.extend([(sp.op_idx, i, i+sp.scheduled_gpunum)]*sp.scheduled_gpunum)
            i += sp.scheduled_gpunum
        curr_gpunum = len(curr_map)
            
        def _p2p_cost() -> float:
            nonlocal opnum, last_map, stage_schedule
            curr_map, i = list(), 0
            for sp in stage_schedule:
                curr_map.extend([(sp.op_idx, i, i+sp.scheduled_gpunum)]*sp.scheduled_gpunum)
                i += sp.scheduled_gpunum
            cost = 0
            for i in range(gpunum):
                if last_map[i][0] != curr_map[i][0]:
                    cost += 1 / (last_map[i][2] - last_map[i][1])
                if last_map[i] == curr_map[i]:
                    cost -= 1
            return cost

        def _recursive_explore(reverse: bool=False) -> None:
            nonlocal stage_schedule
            cost_ori = _p2p_cost()
            if not reverse:
                for i in range(opnum):
                    spi = stage_schedule[i]
                    for j in range(i+1, opnum):
                        spj = stage_schedule[j]
                        # Find suitable rect(s) to swap
                        if self.device_map_level == 1:
                            if spi.scheduled_gpunum == spj.scheduled_gpunum:
                                stage_schedule[i], stage_schedule[j] = spj, spi
                                if _p2p_cost() < cost_ori:
                                    _recursive_explore(reverse)
                                    break
                                stage_schedule[i], stage_schedule[j] = spi, spj
                        elif self.device_map_level == 2:
                            jp = j
                            total_height = 0
                            while True:
                                total_height += stage_schedule[jp].scheduled_gpunum
                                jp += 1
                                if total_height >= spi.scheduled_gpunum or jp >= opnum:
                                    break
                            if total_height == spi.scheduled_gpunum: # Found, swap i with [j, jp)
                                stage_schedule[i:jp] = stage_schedule[j:jp] + stage_schedule[i+1:j] + stage_schedule[i:i+1]
                                if _p2p_cost() < cost_ori:
                                    _recursive_explore(reverse)
                                    break
                                stage_schedule[i:jp] = stage_schedule[jp-1:jp] + stage_schedule[i+jp-j:jp-1] + stage_schedule[i:i+jp-j]
                        
                        # Find a place to insert
                        stage_schedule.pop(i)
                        stage_schedule.insert(j, spi)
                        if _p2p_cost() < cost_ori:
                            _recursive_explore(reverse)
                            break
                        stage_schedule.pop(j)
                        stage_schedule.insert(i, spi)
            else:
                for i in reversed(range(opnum)):
                    spi = stage_schedule[i]
                    for j in reversed(range(i)):
                        spj = stage_schedule[j]
                        # Find suitable rect(s) to swap
                        if self.device_map_level == 1:
                            if spi.scheduled_gpunum == spj.scheduled_gpunum:
                                stage_schedule[i], stage_schedule[j] = spj, spi
                                if _p2p_cost() < cost_ori:
                                    _recursive_explore(reverse)
                                    break
                                stage_schedule[i], stage_schedule[j] = spi, spj
                        elif self.device_map_level == 2:
                            jp = j
                            total_height = 0
                            while True:
                                total_height += stage_schedule[jp].scheduled_gpunum
                                jp -= 1
                                if total_height >= spi.scheduled_gpunum or jp < 0:
                                    break
                            if total_height == spi.scheduled_gpunum: # Found, swap i with (jp, j]
                                stage_schedule[jp+1:i+1] = stage_schedule[i:i+1] + stage_schedule[j+1:i] + stage_schedule[jp+1:j+1]
                                if _p2p_cost() < cost_ori:
                                    _recursive_explore(reverse)
                                    break
                                stage_schedule[jp+1:i+1] = stage_schedule[i+1+jp-j:i+1] + stage_schedule[jp+2:i+1+jp-j] + stage_schedule[jp+1:jp+2]
                        
                        # Find a place to insert
                        stage_schedule.pop(i)
                        stage_schedule.insert(j, spi)
                        if _p2p_cost() < cost_ori:
                            _recursive_explore(reverse)
                            break
                        stage_schedule.pop(j)
                        stage_schedule.insert(i, spi)
            return
        
        if gpunum == curr_gpunum:
            _recursive_explore()
            _recursive_explore(reverse=True)
        
        stage_schedule = tmp_stage_schedule_forward + stage_schedule + tmp_stage_schedule_backward
        return stage_schedule
        
    def schedule_gen(self, schedule_place: List[SchedulePlace], start_stage_idx: int=1) -> Tuple[List[SchedulePlace], float, List]:
        schedule = list()
        stage_idx = start_stage_idx
        schedule: List[List[SchedulePlace]]
        
        def check_valid(schedule_place: List[SchedulePlace], idx_to_plug_in: List[int], sp: SchedulePlace, N_valid: int) -> bool:
            if sp.height > N_valid or not sp.layernode.is_prepared:
                return False
            for i in idx_to_plug_in:
                if schedule_place[i].op_idx == sp.op_idx:
                    return False
            return True 
        
        schedule_place.sort(key=lambda sp: sp.height) # let Ops occupying the whole culster do first
        
        while len(schedule_place):
            if self.logging:
                print("=================================", "Micro-Stage", stage_idx, "=================================")
            
            if schedule_place[0].height < self.world_size:
                if self.sort_rule == "smallN":
                    schedule_place.sort(key=lambda sp: (sp.height, sp.width))
                elif self.sort_rule == "bigN_smallT":
                    schedule_place.sort(key=lambda sp: (-sp.height, sp.width))
                elif self.sort_rule == "bigN_bigT":
                    schedule_place.sort(key=lambda sp: (-sp.height, -sp.width))
                elif self.sort_rule == "smallT":
                    schedule_place.sort(key=lambda sp: (sp.width, -sp.height))
            idx = 0
            N_valid = self.world_size
            min_time = 0.
            idx_to_plug_in = list()
            op_idx_to_plug_in = list()
            
            if self.logging:
                print("[1] Candidate schedule placements are:")
                for p in schedule_place:
                    print(p)
            
            # Determine schedule places that will be plugged into this stage, record indices and get min_time
            while idx < len(schedule_place) and N_valid:
                sp = schedule_place[idx]
                if check_valid(schedule_place, idx_to_plug_in, sp, N_valid):
                    idx_to_plug_in.append(idx)
                    op_idx_to_plug_in.append(sp.op_idx)
                    N_valid -= sp.height
                    if min_time == 0.:
                        min_time = sp.width
                    else:
                        min_time = min(min_time, sp.width)
                idx += 1
            
            # Determine the actual stage time for integer layernums
            stage_time = 0.
            for idx in idx_to_plug_in:
                sp = schedule_place[idx]
                gpunum = sp.height
                execute_layernum = max(round(min_time / sp.layernode.get_time(gpunum, 1)), 1)
                execute_time = sp.layernode.get_time(gpunum, execute_layernum)
                stage_time = max(stage_time, execute_time)
            
            stage_schedule = list()
            # Set originally scheduled time and gpunum
            for idx in idx_to_plug_in:
                sp = schedule_place[idx]
                gpunum = sp.scheduled_gpunum
                scheduled_layernum = min(sp.l, math.floor(stage_time / sp.layernode.get_time(gpunum, 1)))
                sp.set_scheduled(gpunum, scheduled_layernum)
                stage_schedule.append(sp)
            
            if self.logging:
                print("[2] Working schedule placements for this micro-stage are:")
                for sp in stage_schedule:
                    print(sp)
                
            if self.extend_rule is not None:
                self.stage_extension(stage_schedule, stage_time, N_valid)
                
                if self.logging:
                    print("[3] Extended schedule placements with stage time", stage_time, "are:")
                    for sp in stage_schedule:
                        print(sp)
            else:
                if self.logging:
                    print("[3] Stage extension is omitted.")
            
            # Generate real stage schedule
            correct_stage_schedule = list()
            for sp in stage_schedule:
                schedule_place.remove(sp)
                execute_gpunum, execute_layernum = sp.scheduled_gpunum, sp.scheduled_layernum
                execute_time = sp.layernode.get_time(execute_gpunum, execute_layernum)
                
                correct_sp = SchedulePlace(sp.op_idx, execute_time, execute_gpunum, 0., 0, execute_layernum, stage_idx, sp.layernode)
                correct_sp.affect_layernode()
                correct_stage_schedule.append(correct_sp)
                
                if sp.l > execute_layernum:
                    remain_layernum = sp.l - execute_layernum
                    schedule_place.append(SchedulePlace(sp.op_idx, sp.layernode.get_time(sp.height, remain_layernum), sp.height, 0., 0, remain_layernum, layernode=sp.layernode))
                else:
                    assert sp.l == execute_layernum
            stage_schedule = correct_stage_schedule
            
            # For 1st stage, nothing should be done
            if stage_idx == start_stage_idx:
                if self.device_map_level == -1:
                    random.shuffle(stage_schedule)
                schedule.append(stage_schedule)
                stage_idx += 1
                
                if self.logging:
                    print("[4] The 1st micro-stage in macro-stage, reach here to finish.")
                
                continue
            
            # For other stages, check duplication and map device
            # Re-check stage schedule for duplicate stages (exactly same Ops with same gpunum allotments)
            duplicate_stage_flag = True
            idx_map = list()
            for sp in stage_schedule:
                lidx = self.find_identical_allotment(schedule[-1], sp)
                if lidx == -1:
                    duplicate_stage_flag = False
                    break
                else:
                    idx_map.append(lidx)
            
            # If duplicate with the last stage, merge current stage into former one and finish
            if duplicate_stage_flag:
                for idx, sp in enumerate(stage_schedule):
                    lidx = idx_map[idx]
                    lsp = schedule[-1][lidx]
                    assert lsp.op_idx == sp.op_idx and lsp.height == sp.height
                    lsp.update_luv(lsp.height, lsp.scheduled_layernum+sp.scheduled_layernum)
                
                if self.logging:
                    print("[4] This micro-stage is merged into the former one.")
                
                continue
            
            # If not duplicate, do device mapping to match the last stage as much as possible
            if self.device_map_level > 0:
                stage_schedule = self.device_mapping(stage_schedule, schedule[-1])
                
                if self.logging:
                    print("[4] After device mapping, the schedule placements are ordered as:")
                    for sp in stage_schedule:
                        print(sp)
            elif self.device_map_level == -1: # randomly place the MetaOPs
                random.shuffle(stage_schedule)
                
            schedule.append(stage_schedule)
            stage_idx += 1
        
        
        # Generate plan
        plan = list()
        total_time = 0.
        for idx, stage_schedule in enumerate(schedule):
            stage_plan = dict()
            stage_time = 0.
            device_num = 0
            for sp in stage_schedule:
                execute_gpunum, execute_layernum = sp.scheduled_gpunum, sp.scheduled_layernum
                execute_time = sp.layernode.get_time(execute_gpunum, execute_layernum)
                stage_time = max(stage_time, execute_time)
                
                sp.update_xyuv(total_time, device_num)
                stage_plan[sp.layernode.format_name()] = {
                    "short_name": sp.layernode.short_name(),
                    "local_bsz": sp.layernode.layerinfo._local_bsz(execute_gpunum),
                    "layer_num": execute_layernum,
                    "exe_time": execute_time,
                    "mcu": f"{sp.layernode.get_mcu(execute_gpunum, 156):.2%}",
                    "devices": list(range(device_num, device_num+execute_gpunum)),
                }
                device_num += execute_gpunum
            
            plan.append({
                "stage": start_stage_idx+idx,
                "plan": stage_plan,
                "time": stage_time
            })
            total_time += stage_time
            
        new_schedule = list()
        for stage_schedule in schedule:
            new_schedule.extend(stage_schedule)
        
        return new_schedule, total_time, plan

    def resource_alloc(self, candidate_set: List[LayerNode]) -> Tuple[Dict[LayerNode, int], float]:
        resource_map = dict()
        cur_map = dict()
        MCU_best = 0.
        
        # selecting low_MCU layers needs to sort candidate set according to MCU first
        if self.low_MCU_layer_first:
            candidate_set.sort(key=lambda x:x.get_mcu(self.world_size))
        
        if self.naive:
            resource_map = { candidate_set[0]: self.world_size }
            MCU = self.get_MCU_given_resource_map(resource_map)
            return resource_map, MCU
        
        def _resource_alloc_recurse(idx: int, remain_gpunum: int):
            assert self.threshold_policy is False
            nonlocal resource_map, cur_map, MCU_best
            if idx == len(candidate_set):
                if remain_gpunum > 0:
                    return
                MCU = self.get_MCU_given_resource_map(cur_map)
                if MCU > MCU_best:
                    MCU_best = MCU
                    resource_map = cur_map.copy()
            elif idx+1 == len(candidate_set):
                cur_map[candidate_set[idx]] = remain_gpunum
                _resource_alloc_recurse(idx+1, 0)
            else:
                layernode = candidate_set[idx]
                for used_gpunum in range(remain_gpunum+1):
                    cur_map[layernode] = used_gpunum
                    _resource_alloc_recurse(idx+1, remain_gpunum-used_gpunum)
        
        def _resource_alloc_solver():
            assert self.threshold_policy is False
            nonlocal resource_map, MCU_best
            import pyomo.environ as pyo
            nodes = list(candidate_set)
            infos = [layernode.layerinfo for layernode in nodes]
            k = len(nodes)
            # NOTE zsh mark: update uncheck
            a = [info.a / (info.FLOPs*info.bsz) for info in infos]
            b = [info.c / (info.FLOPs) for info in infos]
            # XXX
            model = pyo.ConcreteModel()
            model.n = pyo.Var(range(k), domain=pyo.NonNegativeIntegers)
            
            stage_MCU_obj = pyo.Objective(
                rule=lambda model: sum(model.n[i] / (a[i]*model.n[i] + b[i]) for i in range(k)),
                sense=pyo.maximize
            )
            stage_extra_gpu_time_ratio_obj = pyo.Objective(
                rule=lambda model: sum(a[i]*(model.n[i]**2) / (a[i]*model.n[i] + b[i]) for i in range(k)),
                sense=pyo.minimize
            )
            model.objective = stage_MCU_obj
            
            model.sum_constraint = pyo.Constraint(
                rule=lambda model: sum(model.n[i] for i in range(k)) == self.world_size
            )
            
            solver = pyo.SolverFactory("bonmin", executable=self.solver_path)
            solver.solve(model)
            
            resource_map = {
                nodes[i]: int(model.n[i].value) for i in range(k) if model.n[i].value != 0.0
            }
            
            MCU_best = self.get_MCU_given_resource_map(resource_map)
            
            
        def _resource_alloc_divisible_gpunum(idx: int, remain_gpunum: int):
            nonlocal resource_map, cur_map, MCU_best
            if idx == len(candidate_set):
                if remain_gpunum > 0:
                    return
                MCU = self.get_MCU_given_resource_map(cur_map)
                if self.threshold_policy is False and MCU > MCU_best:
                    MCU_best = MCU
                    resource_map = cur_map.copy()
                elif self.threshold_policy is True and \
                    ((MCU_best == 0.) or \
                     (MCU < self.expected_MCU and MCU > MCU_best) or \
                     (MCU >= self.expected_MCU and MCU_best < self.expected_MCU) or \
                     (MCU >= self.expected_MCU and MCU < MCU_best)):
                    MCU_best = MCU
                    resource_map = cur_map.copy()
            else:
                layernode = candidate_set[idx]
                for used_gpunum in range(remain_gpunum+1):
                    if used_gpunum > 0 and layernode.B % used_gpunum != 0:
                        continue
                    if self.low_MCU_layer_first and idx == 0 and used_gpunum == 0:
                        continue
                    cur_map[layernode] = used_gpunum
                    _resource_alloc_divisible_gpunum(idx+1, remain_gpunum-used_gpunum)
        
        
        if self.bsz_divisible_by_gpunum:
            _resource_alloc_divisible_gpunum(0, self.world_size)
        elif self.solver_path is None:
            _resource_alloc_recurse(0, self.world_size)
        else:
            _resource_alloc_solver()
        
        for key in list(resource_map):
            if resource_map[key] == 0:
                del resource_map[key]
        
        return resource_map, MCU_best
    
    def get_MCU_given_resource_map(self, resource_map: Dict[LayerNode, int]):
        # MCU = 1/N sum_i [n_i/(D_i / (ceil(bsz_i/n_i) f_i) + A_i)]
        MCU = 0.
        for layernode in resource_map:
            gpu_num = resource_map[layernode]
            if gpu_num == 0:
                continue
            MCU = gpu_num * layernode.get_mcu(gpu_num)
        MCU /= self.world_size
        return MCU
    
    def gen_stage_plan(self, resource_map: Dict[LayerNode, int]) -> Tuple[Dict[str, Dict[str, Any]], float]:
        time_dict = { layernode: layernode.get_time(gpu_num) for layernode, gpu_num in resource_map.items() }
        min_time = min(time_dict.values())
        stage_time = 0.
        stage_plan = dict()
        device_num = 0
        for layernode in resource_map:
            # Here use round to deal with indivisible cases, can adapt to other methods
            gpu_num = resource_map[layernode]
            execute_layer_num = max(round(min_time / layernode.get_time(gpu_num=resource_map[layernode], layer_num=1)), 1)
            execute_time = layernode.get_time(gpu_num=gpu_num, layer_num=execute_layer_num)
            stage_time = max(stage_time, execute_time)
            layernode.remain_layernum -= execute_layer_num
            stage_plan[layernode.format_name()] = {
                "op_idx": layernode.op_idx,
                "local_bsz": layernode.layerinfo._local_bsz(gpu_num),
                "layer_num": execute_layer_num,
                "exe_time": execute_time,
                "mcu": f"{layernode.get_mcu(gpu_num, 156):.2%}",
                "devices": list(range(device_num, device_num+gpu_num))
            }
            device_num += gpu_num
        
        return stage_plan, stage_time