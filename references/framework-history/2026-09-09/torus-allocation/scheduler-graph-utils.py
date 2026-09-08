import networkx as nx
from typing import Dict, Tuple, List
from itertools import islice
from morphlux.scheduler.val import BLOCK_DIM
import random

dim_x, dim_y, dim_z = 2, 2, 4
coordinate_type = Tuple[int, int, int]
path_dict_type = Dict[
    coordinate_type, Dict[coordinate_type, List[List[coordinate_type]]]
]


def get_graph(dim_x=dim_x, dim_y=dim_y, dim_z=dim_z, wrap_around=True) -> nx.Graph:
    # TODO Currently the wrap around links are not created properly. Need DiGraph
    G = nx.Graph()
    edge_weight = 1

    for x in range(dim_x):
        for y in range(dim_y):
            for z in range(dim_z):
                G.add_node((x, y, z), pos=(x, y, z))

    for x in range(dim_x):
        for y in range(dim_y):
            for z in range(dim_z):
                if x < dim_x - 1:
                    G.add_edge((x, y, z), (x + 1, y, z), weight=edge_weight)
                if y < dim_y - 1:
                    G.add_edge((x, y, z), (x, y + 1, z), weight=edge_weight)
                if z < dim_z - 1:
                    G.add_edge((x, y, z), (x, y, z + 1), weight=edge_weight)

    # add wrap around edges
    if wrap_around:
        if dim_x == BLOCK_DIM // 2:
            for y in range(dim_y):
                for z in range(dim_z):
                    G.add_edge((0, y, z), (dim_x - 1, y, z), weight=edge_weight)
        
        if dim_y == BLOCK_DIM // 2:
            for x in range(dim_x):
                for z in range(dim_z):
                    G.add_edge((x, 0, z), (x, dim_y - 1, z), weight=edge_weight)
        
        if dim_z == BLOCK_DIM:
            for x in range(dim_x):
                for y in range(dim_y):
                    G.add_edge((x, y, 0), (x, y, dim_z - 1), weight=edge_weight)

    return G


def get_paths_for_all_pairs(block_graph: nx.Graph, K: int) -> path_dict_type:
    paths: path_dict_type = {}

    for u in block_graph.nodes:
        for v in block_graph.nodes:
            if u != v:
                if u not in paths:
                    paths[u] = {}
                if v not in paths[u]:
                    paths[u][v] = []
                all_paths = nx.shortest_simple_paths(block_graph, u, v)
                k_paths = list(islice(all_paths, K))
                paths[u][v].extend(k_paths)
    return paths

def get_paths_for_all_pairs_without_overlap(block_graph: nx.Graph, free_servers, edge_counts, K: int) -> path_dict_type:
    paths: path_dict_type = {}

    for u in free_servers:
        for v in free_servers:
            if u != v:
                if u not in paths:
                    paths[u] = {}
                if v not in paths[u]:
                    paths[u][v] = []
                all_paths = nx.shortest_simple_paths(block_graph, u, v)
                all_paths = list(islice(all_paths, K * 10))

                k_paths = []
                weighted_paths = []
                for path in all_paths:
                    weight = 0
                    for e_u, e_v in zip(path, path[1:]):
                        edge = (e_u, e_v)
                        if edge in edge_counts:
                            weight += edge_counts[edge]
                    weighted_paths.append((path, weight))
                weighted_paths.sort(key=lambda x: x[1])
                
                k_paths = [w[0] for w in weighted_paths]
                paths[u][v].extend(k_paths[: min(K, len(k_paths))])   
    return paths

