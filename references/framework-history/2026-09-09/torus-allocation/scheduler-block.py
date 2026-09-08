from morphlux.scheduler.val import BLOCK_DIM, BLOCK_NUM, OCS_NUM

from morphlux.scheduler.val import Polarity, Direction
from morphlux.scheduler.helper import get_link_id
from typing import List, Dict, Tuple
from morphlux.scheduler.slice import TPU, Slice
from morphlux.scheduler.graph_utils import (
    get_graph, 
    get_paths_for_all_pairs,
    get_paths_for_all_pairs_without_overlap,
    path_dict_type, 
    coordinate_type
)
import networkx as nx
import gurobipy as gp
import os

class Block:
    def __init__(self, block_id: int):
        self.block_id = block_id
        self.tpus: List[TPU] = [TPU(block_id, i) for i in range(BLOCK_DIM**3)]
        self.sub_block_slices: Dict[Tuple[int, int, int], List[Slice]] = {
            (2, 2, 1): [],
            (2, 2, 2): [],
            (2, 2, 4): [],
            (2, 4, 4): [],
            (4, 4, 4): [],
        }
        # Precompute all possible slices of size (2,2,1), (2,2,2), (2,2,4), (2,4,4), and (4,4,4), and store them in self.slices
        for slice_size, l in self.sub_block_slices.items():
            for x in range(0, BLOCK_DIM, slice_size[0]):
                for y in range(0, BLOCK_DIM, slice_size[1]):
                    for z in range(0, BLOCK_DIM, slice_size[2]):
                        tpus = [
                            self.tpus[i + (j * BLOCK_DIM) + (k * BLOCK_DIM**2)]
                            for i in range(x, x + slice_size[0])
                            for j in range(y, y + slice_size[1])
                            for k in range(z, z + slice_size[2])
                        ]
                        l.append(Slice(slice_size, tpus))

        # edge count, including wrap around edges
        # note that edge is neighboring server-pair, link is neighboring tpu-pair, path is server-pair
        self.edge_count: Dict[
            Tuple[Tuple[int, int, int], Tuple[int, int, int]], int
        ] = {}

        # maintain a list of fragmented slice ids. Fragmented slices are not precomputed as regular slices
        self.fragmented_slices = set()
        self.fragmented_slice_route_map = {}

        self.block_graph = get_graph(2, 2, 4) # every server is a node
        # self.paths: path_dict_type = get_paths_for_all_pairs(self.block_graph, 5) # every pair of servers has a path

    def count_free_tpus(self) -> int:
        return sum([1 for tpu in self.tpus if not tpu.allocated])

    def get_free_server_nodes(self) -> list:
        # return a list of server nodes that are free (all 4 tpus are free)
        free_server = []
        for pos, server in self.block_graph.nodes.items():
            x, y, z = pos
            tpu_x, tpu_y, tpu_z = 2 * x, 2 * y, z
            free = True
            for i in range(2):
                for j in range(2):
                    tpu = self.tpus[tpu_x + i + (tpu_y + j) * BLOCK_DIM + tpu_z * BLOCK_DIM**2]
                    if tpu.allocated:
                        free = False
                        break
                if not free:
                    break
            if free:
                free_server.append(pos)
        return free_server

    # def _get_free_path_between_servers(self, free_servers: list) -> path_dict_type:
    #     paths_between_free_servers: path_dict_type = {}
    #     for u in free_servers:
    #         for v in free_servers:
    #             if u != v:
    #                 if u not in paths_between_free_servers:
    #                     paths_between_free_servers[u] = {}
    #                 if v not in paths_between_free_servers[u]:
    #                     paths_between_free_servers[u][v] = []

    #                 paths_between_free_servers[u][v].extend(self.paths[u][v])

    def allocate_slice(self, x_size, y_size, z_size, current_slice_id, reserve=None) -> Slice:
        for slice in self.sub_block_slices[(x_size, y_size, z_size)]:
            if not slice.allocated:
                slice_tpu_set = set([tpu.tpu_id for tpu in slice.tpus])
                
                if reserve and reserve in slice_tpu_set:
                    continue

                slice.allocate(current_slice_id)
                self._count_slice_edge(slice) # including wrap around links
                for dim in self.sub_block_slices:
                    for other_slice in self.sub_block_slices[dim]:
                        other_slice_tpu_set = set(
                            [tpu.tpu_id for tpu in other_slice.tpus]
                        )
                        if slice_tpu_set.intersection(other_slice_tpu_set):
                            other_slice.allocated = True  # if a slice is allocated that shares a TPU with the requested slice, then mark it as allocated but keep its slice_id as None
                return slice
            
        return None
    
    def allocate_slice_fragmented(self, x_size, y_size, z_size, current_slice_id) -> Slice:
        free_tpus = self.count_free_tpus()
        size = x_size * y_size * z_size
        if size > free_tpus:
            return None

        slice_graph = get_graph(x_size // 2, y_size // 2, z_size)
        free_servers = self.get_free_server_nodes()
        
        # path between servers, contains all free server pairs
        paths_between_free_servers = get_paths_for_all_pairs_without_overlap(
            self.block_graph, free_servers, self.edge_count, 5
        )

        try:
            servers, route_list = self._allocate_fragmented_slice(slice_graph, free_servers, paths_between_free_servers)
            #TODO keep track of route list, decrement edge count when deallocate
            ordered_tpus = [None for _ in range(x_size * y_size * z_size)]
            for x in range(x_size):
                for y in range(y_size):
                    for z in range(z_size):
                        server_logical_id = x // 2 + y // 2 * x_size // 2 + z * x_size // 2 * y_size // 2
                        server = servers[server_logical_id]
                        real_x, real_y, real_z = server
                        tpu = self.tpus[real_x * 2 + x % 2 + (real_y * 2 + y % 2) * BLOCK_DIM + real_z * BLOCK_DIM**2]
                        ordered_tpus[x+y*x_size+z*x_size*y_size] = tpu
            slice = Slice((x_size, y_size, z_size), ordered_tpus)
            slice.allocate(current_slice_id)

            self.fragmented_slices.add(current_slice_id)
            self.fragmented_slice_route_map[current_slice_id] = route_list

            slice_tpu_set = set([tpu.tpu_id for tpu in slice.tpus])
            for dim in self.sub_block_slices:
                for other_slice in self.sub_block_slices[dim]:
                    other_slice_tpu_set = set(
                        [tpu.tpu_id for tpu in other_slice.tpus]
                    )
                    if slice_tpu_set.intersection(other_slice_tpu_set):
                        other_slice.allocated = True  # if a slice is allocated that shares a TPU with the requested slice, then mark it as allocated but keep it as having None slice_id

            return slice
        except gp.GurobiError as e:
            print('Gurobi error: {}'.format(e))
            return None
    
    def deallocate_slice(self, slice: Slice):
        # Mark intersecting slices as free
        if not slice.allocated:
            return
        if slice.id in self.fragmented_slices:
            # Fragmented slice allocation
            self.fragmented_slices.remove(slice.id)
            route_list = self.fragmented_slice_route_map[slice.id]

            for route in route_list:
                for i in range(len(route) - 1):
                    # the route here is directional
                    self._count_edge((route[i], route[i + 1]), up=False)
            del self.fragmented_slice_route_map[slice.id]

        else:
            self._count_slice_edge(slice, up=False) # including wrap around links
        
        slice.deallocate()
        slice_tpu_set = set([tpu.tpu_id for tpu in slice.tpus])
        for dim in self.sub_block_slices:
            for other_slice in self.sub_block_slices[dim]:
                other_slice_tpu_set = set([tpu.tpu_id for tpu in other_slice.tpus])
                if other_slice != slice and slice_tpu_set.intersection(other_slice_tpu_set):
                    assert other_slice.allocated == True
                    assert other_slice.id == None
                    if not any([tpu.allocated for tpu in other_slice.tpus]):
                        other_slice.allocated = False

    def _allocate_fragmented_slice(self, slice_graph, free_servers, paths_between_free_servers):
        # return a list of servers ordered by the logical slice topology
        allocator = slice_allocator(slice_graph, self.block_graph, free_servers, paths_between_free_servers)

        allocator.add_mapping_variables()
        allocator.add_route_variables()
        allocator.add_one_mapping_constraint()
        allocator.add_route_selection_constraint()
        server_list, route_list = allocator.optimize(self.edge_count)

        for route in route_list:
            for i in range(len(route) - 1):
                # the route here is directional
                self._count_edge((route[i], route[i + 1]), up=True)

        return server_list, route_list

    def get_neighbor_tpu(self, tpu: TPU, dir: Direction, pol: Polarity) -> TPU:
        # Return TPU of the neighbor in the given direction, if it exists
        # Don't return the neighbor if it is using the wrap around link
        x, y, z = tpu.coord
        if dir == Direction.X:
            if pol == Polarity.NEGATIVE:
                if x == 0:
                    return None
                ntpu_id = x - 1 + y * BLOCK_DIM + z * BLOCK_DIM**2
                return self.tpus[ntpu_id]
            else:
                if x == BLOCK_DIM - 1:
                    return None
                ntpu_id = x + 1 + y * BLOCK_DIM + z * BLOCK_DIM**2
                return self.tpus[ntpu_id]
        elif dir == Direction.Y:
            if pol == Polarity.NEGATIVE:
                if y == 0:
                    return None
                ntpu_id = x + (y - 1) * BLOCK_DIM + z * BLOCK_DIM**2
                return self.tpus[ntpu_id]
            else:
                if y == BLOCK_DIM - 1:
                    return None
                ntpu_id = x + (y + 1) * BLOCK_DIM + z * BLOCK_DIM**2
                return self.tpus[ntpu_id]

        elif dir == Direction.Z:
            if pol == Polarity.NEGATIVE:
                if z == 0:
                    return None
                ntpu_id = x + y * BLOCK_DIM + (z - 1) * BLOCK_DIM**2
                return self.tpus[ntpu_id]
            else:
                if z == BLOCK_DIM - 1:
                    return None
                ntpu_id = x + y * BLOCK_DIM + (z + 1) * BLOCK_DIM**2
                return self.tpus[ntpu_id]

    def is_fully_allocated(self):
        return all([tpu.allocated for tpu in self.tpus])
    
    def is_partially_allocated(self):
        return any([tpu.allocated for tpu in self.tpus])

    def get_tpus(self) -> List[TPU]:
        return self.tpus

    def get_face(self, dim: int, pol: Polarity) -> list:
        pass

    def is_tpu_in_slice(self, coords: Tuple[int, int, int], s: Slice):
        tpus_in_slice: List[TPU] = s.tpus
        for slice_tpu in tpus_in_slice:
            if slice_tpu.coord == coords:
                return True
        return False

    def _get_link_id(self, s: Tuple[int, int, int], d: Tuple[int, int, int]):
        # return ordered pair of server/tpu ids
        if s[0] < d[0]:
            assert s[1] == d[1] and s[2] == d[2]
            return (s, d)
        if s[0] > d[0]:
            assert s[1] == d[1] and s[2] == d[2]
            return (d, s)

        if s[1] < d[1]:
            assert s[0] == d[0] and s[2] == d[2]
            return (s, d)
        if s[1] > d[1]:
            assert s[0] == d[0] and s[2] == d[2]
            return (d, s)

        if s[2] < d[2]:
            assert s[1] == d[1] and s[0] == d[0]
            return (s, d)
        if s[2] > d[2]:
            assert s[1] == d[1] and s[0] == d[0]
            return (d, s)
        return None

    def _count_edge(self, edge: Tuple[Tuple[int, int, int], Tuple[int, int, int]], up: bool = True):
        if up:
            if edge not in self.edge_count:
                self.edge_count[edge] = 0
            self.edge_count[edge] += 1
        else:
            if edge in self.edge_count and self.edge_count[edge] > 0:
                self.edge_count[edge] -= 1
                if self.edge_count[edge] == 0:
                    del self.edge_count[edge]


    def get_server_id(self, coord: Tuple[int, int, int]) -> Tuple[int, int, int]:
        x, y, z = coord
        s_x, s_y, s_z = int(x / 2), int(y / 2), int(z)
        return s_x, s_y, s_z

    def _count_slice_edge(self, s: Slice, up: bool = True):
        for tpu in s.tpus:
            x, y, z = tpu.coord

            right_coords = ((x + 1) % BLOCK_DIM, y, z)
            if self.is_tpu_in_slice(right_coords, s):
                right_edge = self._get_link_id(
                    self.get_server_id(tpu.coord), 
                    self.get_server_id(right_coords))
                if right_edge:
                    self._count_edge(right_edge, up)

            left_coords = ((x - 1) % BLOCK_DIM, y, z)
            if self.is_tpu_in_slice(left_coords, s):
                left_edge = self._get_link_id(
                    self.get_server_id(tpu.coord), 
                    self.get_server_id(left_coords))
                if left_edge:
                    self._count_edge(left_edge, up)

            front_coords = (x, (y + 1) % BLOCK_DIM, z)
            if self.is_tpu_in_slice(front_coords, s):
                front_edge = self._get_link_id(
                    self.get_server_id(tpu.coord), 
                    self.get_server_id(front_coords))
                if front_edge:
                    self._count_edge(front_edge, up)
            back_coords = (x, (y - 1) % BLOCK_DIM, z)
            if self.is_tpu_in_slice(back_coords, s):
                back_edge = self._get_link_id(
                    self.get_server_id(tpu.coord), 
                    self.get_server_id(back_coords))
                if back_edge:
                    self._count_edge(back_edge, up)

            up_coords = (x, y, (z + 1) % BLOCK_DIM)
            if self.is_tpu_in_slice(up_coords, s):
                up_edge = self._get_link_id(
                    self.get_server_id(tpu.coord), 
                    self.get_server_id(up_coords))
                if up_edge:
                    self._count_edge(up_edge, up)
            down_coords = (x, y, (z - 1) % BLOCK_DIM)
            if self.is_tpu_in_slice(down_coords, s):
                down_edge = self._get_link_id(
                    self.get_server_id(tpu.coord), 
                    self.get_server_id(down_coords))
                if down_edge:
                    self._count_edge(down_edge, up)

    def get_face(self, dim: int, pol: Polarity) -> list:
        pass


class slice_allocator:

    def __init__(
        self,
        slice_graph: nx.Graph,
        block_graph: nx.Graph,
        free_servers: List[coordinate_type],
        block_paths: path_dict_type,
    ):
        # TODO is the TPU order correct
        self.slice_graph = slice_graph
        self.block_graph = block_graph
        self.block_paths = block_paths
        self.free_servers = free_servers

        self.slice_slots = [s for s in range(len(slice_graph.nodes))]
        self.servers = [s for s in range(len(self.free_servers))]
        env = gp.Env(
            params={
                "LICENSEID": int(os.getenv("LICENSEID")),
                "WLSACCESSID": os.getenv("WLSACCESSID"),
                "WLSSECRET": os.getenv("WLSSECRET"),
            }
        )
        self.model = gp.Model("slice_allocator", env=env)
        self.model.setParam('OutputFlag', 0)
        self.mapping_variables: List[List[gp.Var]] = []
        self.routing_variables: Dict[int, Dict[int, List[gp.Var]]] = {}
        self.edge_to_routes: Dict[Tuple[coordinate_type], List[gp.Var]] = {}

    def add_mapping_variables(self):
        for server in self.servers:
            slot_variables = []
            for slot in self.slice_slots:
                mapping_variable = self.model.addVar(
                    vtype=gp.GRB.BINARY, name="server_{}_slot_{}".format(server, slot)
                )
                slot_variables.append(mapping_variable)
            assert len(slot_variables) == len(self.slice_slots)
            self.mapping_variables.append(slot_variables)
        assert len(self.mapping_variables) == len(self.servers)

    def _get_edge_label(self, p1: coordinate_type, p2: coordinate_type):
        return p1, p2

    def _add_edge_to_routes_mapping(
        self,
        u: coordinate_type,
        v: coordinate_type,
        route_id: int,
        route_variable: gp.Var,
    ):
        route = self.block_paths[u][v][route_id]
        for p1, p2 in zip(route, route[1:]):
            edge = self._get_edge_label(p1, p2)
            if edge not in self.edge_to_routes:
                self.edge_to_routes[edge] = []
            self.edge_to_routes[edge].append(route_variable)

    def add_route_variables(self):
        for u in self.servers:
            for v in self.servers:
                if u != v:
                    u_key = self.free_servers[u]
                    v_key = self.free_servers[v]
                    # print(
                    #     "Paths between {} and {} is {}".format(
                    #         u_key, v_key, len(self.block_paths[u_key][v_key])
                    #     )
                    # )
                    if u not in self.routing_variables:
                        self.routing_variables[u] = {}
                    if v not in self.routing_variables[u]:
                        self.routing_variables[u][v] = []
                    for route in range(len(self.block_paths[u_key][v_key])):
                        route_variable = self.model.addVar(
                            vtype=gp.GRB.BINARY,
                            name="route_{}_from_{}_to_{}".format(route, u, v),
                        )
                        self.routing_variables[u][v].append(route_variable)
                        self._add_edge_to_routes_mapping(
                            u_key, v_key, route, route_variable
                        )

    def add_one_mapping_constraint(self):
        for server in self.servers:
            server_mapping_variables = self.mapping_variables[server]
            # self.model.addConstr(gp.quicksum(server_mapping_variables) >= 1)
            self.model.addConstr(gp.quicksum(server_mapping_variables) <= 1)

        for slot in self.slice_slots:
            slot_vars = [mapping[slot] for mapping in self.mapping_variables]
            self.model.addConstr(gp.quicksum(slot_vars) >= 1)
            self.model.addConstr(gp.quicksum(slot_vars) <= 1)

    def _are_slice_servers_connected(self, u: int, v: int):
        slice_u = list(self.slice_graph.nodes)[u]
        slice_v = list(self.slice_graph.nodes)[v]
        return self.slice_graph.has_edge(slice_u, slice_v)

    def _add_route_selection_if_slices_connected(self, server_u: int, server_v: int):
        for slice_u in self.slice_slots:
            for slice_v in self.slice_slots:
                if slice_u != slice_v and self._are_slice_servers_connected(
                    slice_u, slice_v
                ):
                    # There should be a route from server_u and server_v
                    routing_variables = self.routing_variables[server_u][server_v]
                    placement_u, placement_v = (
                        self.mapping_variables[server_u][slice_u],
                        self.mapping_variables[server_v][slice_v],
                    )
                    temp_uv_variable = self.model.addVar(vtype=gp.GRB.BINARY)
                    self.model.addConstr(temp_uv_variable >= placement_u * placement_v)
                    self.model.addGenConstrIndicator(
                        temp_uv_variable, True, gp.quicksum(routing_variables) == 1
                    )

    def add_route_selection_constraint(self):
        for server_u in self.servers:
            for server_v in self.servers:
                if server_u != server_v:
                    self._add_route_selection_if_slices_connected(server_u, server_v)

    def print_output(self):
        server_list = self.free_servers
        slot_list = list(self.slice_graph.nodes)
        assert len(self.slice_slots) == len(self.slice_graph.nodes)

        server_slot_map = {}
        server_list_in_logical_topo = [None for _ in range(len(slot_list))]
        for server in self.servers:
            for slot in self.slice_slots:
                if self.mapping_variables[server][slot].X > 0.9:
                    print(
                        "Server {} is on {}".format(
                            server_list[server], slot_list[slot]
                        )
                    )
                    server_slot_map[server] = slot
                    server_list_in_logical_topo[slot] = server_list[server]

        route_list = []
        # Also print routes
        for u in self.routing_variables:
            for v in self.routing_variables:
                if u != v:
                    u_coord = server_list[u]
                    v_coord = server_list[v]
                    if u in server_slot_map and v in server_slot_map:
                        slot_u = server_slot_map[u]
                        slot_v = server_slot_map[v]
                        slot_u_coord = list(self.slice_graph.nodes)[slot_u]
                        slot_v_coord = list(self.slice_graph.nodes)[slot_v]
                        if self.slice_graph.has_edge(slot_u_coord, slot_v_coord):
                            for idx, route_var in enumerate(self.routing_variables[u][v]):
                                if route_var.X > 0.9:
                                    print('Route between server {} and {} is {}'.format(u_coord, v_coord, self.block_paths[u_coord][v_coord][idx]))
                                    route_list.append(self.block_paths[u_coord][v_coord][idx])
                            
                    

        return server_list_in_logical_topo, route_list

    def optimize(self, block_edge_counts):
        # return a list of servers ordered in logical topo and a list of routes
        optimization_var = self.model.addVar(vtype=gp.GRB.INTEGER)

        for edge in self.edge_to_routes:
            # Add values to the quick sum array to reflect the state of the block here
            edge_count = 0
            if edge in block_edge_counts:
                edge_count += block_edge_counts[edge]
                print(
                    "Found existing edge count for: {} which is {}".format(
                        edge, edge_count
                    )
                )
            self.model.addConstr(
                optimization_var >= gp.quicksum(self.edge_to_routes[edge]) * 4 + edge_count
            )

        self.model.setObjective(optimization_var, gp.GRB.MINIMIZE)
        self.model.params.BestObjStop = 2
        self.model.optimize()

        # self.model.computeIIS()
        # self.model.write("iis.ilp")  # Save IIS to a file for inspection
        return self.print_output()
