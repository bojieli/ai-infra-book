from typing import List
import math
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib import patches as mpatches
from matplotlib import cm as cm

from galvatron.core import LayerNode, TaskNode


class RectPlace():
    def __init__(self, idx: int, width: float, height: int, x: float, y: int, layernode: LayerNode=None):
        self.layernode = layernode
        self.op_idx = idx
        # self.width = width
        # self.height = height
        self.x = x
        self.y = y
        self.u = x + width
        self.v = y + height
    
    @property
    def width(self):
        return self.u - self.x
    
    @property
    def height(self):
        return self.v - self.y


class SchedulePlace():
    def __init__(self, op_idx: int, width: float, height: int, x: float, y: int, layernum: int, stage_idx: int=-1, layernode: LayerNode=None):
        self.layernode = layernode
        self.op_idx = op_idx
        # self.width = width
        # self.height = height
        self.x = x
        self.y = y
        self.u = x + width
        self.v = y + height
        self.l = layernum
        self.stage_idx = stage_idx
        
        self.scheduled_gpunum, self.scheduled_layernum = height, layernum
    
    @property
    def width(self):
        return self.u - self.x
    
    @property
    def height(self):
        return self.v - self.y
    
    def set_scheduled(self, gpunum: int, layernum: int):
        assert layernum <= self.l
        self.scheduled_gpunum, self.scheduled_layernum = gpunum, layernum
    
    def update_luv(self, gpunum: int, layernum: int):
        self.l = layernum
        self.set_scheduled(gpunum, layernum)
        self.u = self.x + self.scheduled_time
        self.v = self.y + gpunum
    
    def update_xyuv(self, x: float, y: int):
        self.x, self.y = x, y
        self.u, self.v = x + self.scheduled_time, y + self.scheduled_gpunum
    
    @property
    def scheduled_time(self) -> float:
        return self.layernode.get_time(self.scheduled_gpunum, self.scheduled_layernum)
    
    @property
    def new_remain_time_nstar(self) -> float:
        node = self.layernode
        scheduled_time = node.get_time(self.scheduled_gpunum, self.scheduled_layernum)
        return (node.remain_work - scheduled_time*node.speedup(self.scheduled_gpunum)) / node.speedup(node.gpunum_opt)
    
    @property
    def new_remain_work_nstar(self) -> float:
        node = self.layernode
        scheduled_time = node.get_time(self.scheduled_gpunum, self.scheduled_layernum)
        return (node.remain_work - scheduled_time*node.speedup(self.scheduled_gpunum)) / node.gpunum_opt
    
    def affect_layernode(self):
        self.layernode.update_remains(self.scheduled_time, self.scheduled_gpunum, self.scheduled_layernum)
    
    def __str__(self):
        return f"schedule placement: OP {self.op_idx}, gpunum {self.height}[{self.scheduled_gpunum}], layernum {self.l}[{self.scheduled_layernum}], time {self.width:.2f}[{self.scheduled_time:.2f}], start from {self.x}, at stage {self.stage_idx}"


class TaskPlace():
    def __init__(self, gpunum: int, tasknode: TaskNode, scheduled: bool=False, x: float=0., y: int=0):
        self.tasknode = tasknode
        self.scheduled = scheduled
        self.x = x
        self.y = y
        self.scheduled_gpunum = gpunum

    def set_xy(self, x: float, y: int):
        self.scheduled = True
        self.x = x
        self.y = y

    def set_scheduled_gpunum(self, gpunum: int):
        self.scheduled_gpunum = gpunum
    
    @property
    def task_id(self) -> int:
        return self.tasknode.task_id
    
    @property
    def scheduled_time(self) -> float:
        return self.tasknode.get_time(self.scheduled_gpunum)
    
    @property
    def width(self) -> float:
        return self.scheduled_time
    
    @property
    def u(self) -> float:
        return self.x + self.width
    
    @property
    def height(self) -> int:
        return self.scheduled_gpunum
    
    @property
    def v(self) -> int:
        return self.y + self.height


def draw_rects(places: List[RectPlace], opnum: int, W: float, H: int) -> None:    
    cnames = list(mpl.colors.cnames)
    
    fig, ax = plt.subplots()
    maxX, maxY = 0., 0
    for p in places:
        maxX = max(maxX, p.x+p.width)
        maxY = max(maxY, p.y+p.height)
    ax.set_xlim(0, maxX)
    ax.set_ylim(0, maxY)
    for p in places:
        artist = mpatches.Rectangle((p.x, p.y), p.width, p.height, facecolor=cnames[math.floor((p.op_idx-1)/opnum*len(cnames))], edgecolor='black', alpha=0.3, linewidth=0.2)
        ax.add_artist(artist)
        if p.layernode is not None:
            ax.annotate(f"{p.op_idx}|{p.layernode.cal_layernum(p.width, p.height):.2f}", (p.x, p.y), (p.x+p.width/2, p.y+p.height/2), fontsize=3)

def draw_rects_schedule(places: List[SchedulePlace], opnum: int) -> None:    
    cnames = list(mpl.colors.cnames)
    
    fig, ax = plt.subplots()
    maxX, maxY = 0., 0
    for p in places:
        maxX = max(maxX, p.x+p.width)
        maxY = max(maxY, p.y+p.height)
    ax.set_xlim(0, maxX)
    ax.set_ylim(0, maxY)
    for p in places:
        x, y = p.x, p.y
        artist = mpatches.Rectangle((x, y), p.width, p.height, facecolor=cnames[math.floor((p.op_idx-1)/opnum*len(cnames))], edgecolor='black', alpha=0.5, linewidth=0.2)
        ax.add_artist(artist)
        ax.annotate(f"{p.layernode.short_name()}|{p.l}", (x, y), (x+p.width/2, y+p.height/2), fontsize=5)

def draw_rects_task(places: List[TaskPlace], tasknum: int) -> None:
    cnames = list(mpl.colors.cnames)
    
    fig, ax = plt.subplots()
    maxX, maxY = 0., 0
    for p in places:
        maxX = max(maxX, p.x+p.width)
        maxY = max(maxY, p.y+p.height)
    ax.set_xlim(0, maxX)
    ax.set_ylim(0, maxY)
    for p in places:
        x, y = p.x, p.y
        artist = mpatches.Rectangle((x, y), p.width, p.height, facecolor=cnames[math.floor((p.task_id-1)/tasknum*len(cnames))], edgecolor='black', alpha=0.5, linewidth=0.2)
        ax.add_artist(artist)
        ax.annotate(p.tasknode.taskname, (x, y), (x+p.width/2, y+p.height/2), fontsize=5)