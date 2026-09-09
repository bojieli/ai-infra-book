from typing import List, Dict, Tuple, Literal, Any
import math
import numpy as np
import matplotlib.pyplot as plt

from galvatron.core import ComputeGraph, LayerNode, TaskNode, TaskPlace, draw_rects_task

def build_graph_decouple(layerconfig_dict: Dict, layer_conns: List[Tuple[str, str]], task_layername_map: Dict[str, List[str]], bsz_multiply=1, ga_step=1) -> ComputeGraph:
    graph = ComputeGraph()
    graph.build_graph(layerconfig_dict, layer_conns, bsz_multiply, ga_step)
    graph.compile_task(task_layername_map)
    return graph


class PlannerDecouple():
    def __init__(
        self,
        world_size: int,
        graph: ComputeGraph,
        allotment_rule: Literal["optimus", "uniform", "all"]="all",
        optimus_mode: Literal["completion", "makespan", None]=None,
        valid_gpunum_strategy: Literal["batch divisible", "consecutive integers"]="batch divisible",
        sort_rule: Literal["bigT"]="bigT",
        leverage_gpunum_opt: bool=False,
        ga_step: int=1,
        draw_rects: bool=False,
        fig_path: str=None,
    ):
        self.world_size = world_size
        self.graph = graph
        self.task: Dict[str, TaskNode] = graph.task
        assert graph.task is not None
        self.allotment_rule = allotment_rule
        self.optimus_mode = optimus_mode
        self.valid_gpunum_strategy = valid_gpunum_strategy
        assert allotment_rule != "optimus" or optimus_mode is not None
        self.sort_rule = sort_rule
        self.leverage_gpunum_opt = leverage_gpunum_opt
        self.ga_step = ga_step
        self.draw_rects = draw_rects
        self.fig_path = fig_path
        assert not draw_rects or (draw_rects and fig_path is not None)
    
    def gen_schedule_task_parallel(self, task_placement: List[TaskPlace]) -> Tuple[List[TaskPlace], float]:
        tasknum = len(task_placement)
        if self.sort_rule == "bigT":
            task_placement.sort(key=lambda x: x.scheduled_time, reverse=True)
        else:
            raise NotImplementedError(f"not supported sorting rule {self.sort_rule} in schedule generation.")
        
        used_gpunum = 0
        for i in range(min(self.world_size, tasknum)):
            task_placement[i].set_xy(0., used_gpunum)
            used_gpunum += task_placement[i].scheduled_gpunum
        
        device_time = [[i, task_placement[i].scheduled_time] for i in range(min(self.world_size, tasknum))]
        if tasknum > self.world_size:
            idx = self.world_size
            while idx < tasknum: # assign one gpu to task indexed `idx` in task_placement
                device_time.sort(key=lambda x: x[1])
                task_placement[idx].set_xy(device_time[0][1], device_time[0][0])
                device_time[0][1] += task_placement[idx].scheduled_time
                idx += 1
        
        return task_placement, np.max(device_time)
    
    def resource_alloc_uniform(self) -> List[TaskPlace]:
        tasknum = len(self.task)
        resource_map: List[TaskPlace] = list()
        gpunum = math.ceil(self.world_size / tasknum)
        for tasknode in self.task.values():
            resource_map.append(TaskPlace(gpunum, tasknode))
        if tasknum > self.world_size:
            pass
        else:
            over_allocated_gpunum = gpunum * tasknum - self.world_size
            while over_allocated_gpunum > 0:
                valid_tp_list: List[Tuple[TaskPlace, int, int, float]] = list()
                for tp in resource_map:
                    prev_gpunum = tp.tasknode.get_prev_valid_gpunum(tp.scheduled_gpunum)
                    
                    # scheduled_gpunum can only be changed one time in uniform task parallel
                    if prev_gpunum != 0 and tp.scheduled_gpunum == gpunum:
                        valid_tp_list.append((tp, tp.scheduled_gpunum, prev_gpunum, tp.tasknode.get_time(prev_gpunum)))
            
                valid_tp_list.sort(key=lambda x: x[3])
                tp_tuple = valid_tp_list[0]
                tp_tuple[0].set_scheduled_gpunum(tp_tuple[2])
                over_allocated_gpunum -= (tp_tuple[1] - tp_tuple[2])
            
            while over_allocated_gpunum < 0: # at least fill the whole cluster
                valid_tp_list: List[Tuple[TaskPlace, int, int, float]] = list()
                for tp in resource_map:
                    next_gpunum = tp.tasknode.get_next_valid_gpunum(tp.scheduled_gpunum)
                    
                    # scheduled_gpunum can only be changed one time in uniform task parallel
                    if next_gpunum != 0 and tp.scheduled_gpunum == gpunum:
                        next_gpunum = gpunum + min(next_gpunum-gpunum, -over_allocated_gpunum) # not exceed world_size
                        valid_tp_list.append((tp, tp.scheduled_gpunum, next_gpunum, tp.scheduled_time))

                valid_tp_list.sort(key=lambda x:x[3], reverse=True)
                tp_tuple = valid_tp_list[0]
                tp_tuple[0].set_scheduled_gpunum(tp_tuple[2])
                over_allocated_gpunum += (tp_tuple[2] - tp_tuple[1])
        
        return resource_map
    
    # mode for optimization object
    # "completion" means to minmize average completion time
    # "makespan" means to minimize maximum of makespan
    def resource_alloc_optimus(self, mode: Literal["completion", "makespan"]="completion") -> List[TaskPlace]:
        tasknum = len(self.task)
        if tasknum > self.world_size: # degenerate to uniform allocations
            return self.resource_alloc_uniform()
        
        resource_map: List[TaskPlace] = list()
        if not self.leverage_gpunum_opt:
            start_gpunum = [1 for _ in range(tasknum)]
        else:
            start_gpunum = list()
            for tasknode in self.task.values():
                gpunum_opt = tasknode.layernode_list[0].gpunum_opt
                if gpunum_opt < 1:
                    start_gpunum.append(1)
                else:
                    start_gpunum.append(tasknode.get_prev_valid_gpunum(math.ceil(gpunum_opt)))
            if np.sum(start_gpunum) > self.world_size:
                start_gpunum = [1 for _ in range(tasknum)]
        
        for tasknode in self.task.values():
            resource_map.append(TaskPlace(1, tasknode))
        unused_gpunum = self.world_size - tasknum
        while unused_gpunum:
            valid_tp_list: List[Tuple[TaskPlace, int, int, float, float]] = list()
            for tp in resource_map:
                next_gpunum = tp.tasknode.get_next_valid_gpunum(tp.scheduled_gpunum)
                if next_gpunum != 0 and next_gpunum - tp.scheduled_gpunum <= unused_gpunum:
                    valid_tp_list.append((tp, tp.scheduled_gpunum, next_gpunum, tp.scheduled_time, tp.tasknode.get_time(next_gpunum)))
            
            # immediate marginal gain after gpunum+1
            if mode == "completion":
                valid_tp_list.sort(key=lambda x: (x[3]-x[4])/(x[2]-x[1]), reverse=True) # Actually use (x[3]-x[4]) may get better results
            elif mode == "makespan":
                valid_tp_list.sort(key=lambda x: x[3], reverse=True)
            
            tp_tuple = valid_tp_list[0]
            tp_tuple[0].set_scheduled_gpunum(tp_tuple[2])
            unused_gpunum -= (tp_tuple[2] - tp_tuple[1])
        
        return resource_map

    def gen_schedule_all(self) -> Tuple[List[TaskPlace], float]:
        task_placement: List[TaskPlace] = list()
        total_time = 0.
        for tasknode in self.task.values():
            tp = TaskPlace(self.world_size, tasknode, scheduled=True, x=total_time, y=0)
            task_placement.append(tp)
            total_time += tp.scheduled_time
        return task_placement, total_time
        
    def plan_algorithm(self) -> Tuple[Any, float]:
        if self.allotment_rule != "all":
            for tasknode in self.task.values():
                tasknode.update_valid_gpunum(self.world_size, strategy=self.valid_gpunum_strategy)
        
        if self.allotment_rule == "uniform":
            resource_map = self.resource_alloc_uniform()
            task_placement, total_time = self.gen_schedule_task_parallel(resource_map)
        elif self.allotment_rule == "all":
            task_placement, total_time = self.gen_schedule_all()
        elif self.allotment_rule == "optimus":
            resource_map = self.resource_alloc_optimus(mode=self.optimus_mode)
            task_placement, total_time = self.gen_schedule_task_parallel(resource_map)
        else:
            raise NotImplementedError(f"not support allotment rule {self.allotment_rule}.")

        if self.draw_rects:
            draw_rects_task(task_placement, tasknum=len(task_placement))
            plt.savefig(self.fig_path)
            plt.clf()
            plt.close("all")
        
        plan: List[Dict[str, Any]] = list()
        for tp in task_placement:
            task_plan = {
                "task": tp.tasknode.taskname,
                "devices": list(range(tp.y, tp.v)),
                "exe_time": tp.scheduled_time
            }
            plan.append(task_plan)
        
        return plan, total_time * self.ga_step
