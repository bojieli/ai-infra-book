from scheduler import Slice, TPU
from scheduler.graph_utils import coordinate_type, get_graph
from typing import List, Tuple, Dict
import networkx as nx
from gurobipy import Model, GRB, quicksum, Env
import os

env = Env(
    params={
        "LICENSEID": int(os.getenv("LICENSEID")),
        "WLSACCESSID": os.getenv("WLSACCESSID"),
        "WLSSECRET": os.getenv("WLSSECRET"),
    }
)

class BW_allocator_ILP:
    def __init__(self, slice: Slice, logical_topology: List[List[int]], tpu_injection_bw: int = 6, link_bw: int = 1, physical_topology: nx.Graph = None):
        # slice contains the TPUs assigned to the slice, with the TPU list ordered by the physical connection
        # the logical topology is a list of rings, each ring is a list of logical nodes with integer as index
        # the physical topology is a networkx graph with each node being a TPU (not server), for ILP allocator
        
        self.slice = slice
        self.injection_bw = tpu_injection_bw

        self.logical_topology = logical_topology
        self.physical_topology = physical_topology
        self.link_bw = link_bw
        self.check_logical_topology()

        if self.physical_topology:
            self.check_tpu_physical_map()
        self.logical_physical_map: Dict[coordinate_type, TPU] = {}

    def check_logical_topology(self):
        logical_nodes = set()
        for ring in self.logical_topology:
            for node in ring:
                logical_nodes.add(node)
        assert len(logical_nodes) <= len(self.slice.tpus), "Number of logical nodes does not match number of TPUs in slice"

    def check_tpu_physical_map(self):
        assert len(self.physical_topology.nodes) == len(
            slice.tpus
        ), "Number of TPUs in slice does not match physical topology"
        tpu_coord_set = set([tpu.coord for tpu in self.slice.tpus])
        for node in self.physical_topology.nodes:
            assert node in tpu_coord_set, f"TPU {node} not in slice"

    def _is_tpu_connected(self, tpu_i_coord: coordinate_type, tpu_j_coord: coordinate_type):
        return self.physical_topology.has_edge(tpu_i_coord, tpu_j_coord)

    def allocate_bw(self):
        # determine TPU to logical node coord mapping, constraint one to one mapping
        model = Model("BW_Allocation", env=env)
        logical_physical_map = {}
        for ring in self.logical_topology:
            for i in ring:
                if i not in logical_physical_map:
                    logical_physical_map[i] = {}
                    for tpu in self.slice.tpus:
                        logical_physical_map[i][tpu.coord] = model.addVar(
                            vtype=GRB.BINARY, name=f"logical_{i}_physical_{tpu.coord}"
                        )

        # Constraint: every logical node i is mapped to exactly one TPU
        for i in logical_physical_map:
            model.addConstr(
            quicksum(logical_physical_map[i][tpu.coord] for tpu in self.slice.tpus) == 1,
            name=f"logical_{i}_one_tpu"
            )

        # Constraint: every TPU is mapped to exactly one logical node i
        for tpu in self.slice.tpus:
            model.addConstr(
            quicksum(logical_physical_map[i][tpu.coord] for i in logical_physical_map) == 1,
            name=f"tpu_{tpu.coord}_one_logical"
            )

        # create routing variables
        routing_variables = {}
        for i, tpu_i in enumerate(self.slice.tpus):
            for tpu_j in self.slice.tpus[i+1:]:
                tpu_i_coord, tpu_j_coord = tpu_i.coord, tpu_j.coord
                if tpu_i_coord not in routing_variables:
                    routing_variables[tpu_i_coord] = {}
                routing_variables[tpu_i_coord][tpu_j_coord] = []

                for r in range(len(self.logical_topology)):
                    rvar = model.addVar(
                        vtype=GRB.INTEGER, name=f"tpu_{tpu_i_coord}_tpu_{tpu_j_coord}_ring_{r}"
                    )
                    routing_variables[tpu_i_coord][tpu_j_coord].append(rvar)

        # determine bandwidth allocated for each physical link, constraint every logical link has a physical link, constraint link and injection bandwidth is not exceeded
        for r, ring in enumerate(self.logical_topology):
            for i, node_i in enumerate(ring):
                node_j = ring[(i+1) % len(ring)]
                for tpu_i in self.slice.tpus:
                    for tpu_j in self.slice.tpus:
                        rvar = None
                        rvar_all_ring = None
                        tpu_i_coord, tpu_j_coord = tpu_i.coord, tpu_j.coord

                        if tpu_i_coord in routing_variables and tpu_j_coord in routing_variables[tpu_i_coord]:
                            rvar = routing_variables[tpu_i_coord][tpu_j_coord][r]
                            rvar_all_ring = routing_variables[tpu_i_coord][tpu_j_coord]
                        elif tpu_j_coord in routing_variables and tpu_i_coord in routing_variables[tpu_j_coord]:
                            rvar = routing_variables[tpu_j_coord][tpu_i_coord][r]
                            rvar_all_ring = routing_variables[tpu_j_coord][tpu_i_coord]

                        if rvar:
                            and_var = model.addVar(vtype=GRB.BINARY, name=f"and_var_{node_i}_{node_j}_{tpu_i_coord}_{tpu_j_coord}")

                            # Add constraints to enforce AND logic:
                            model.addConstr(and_var <= logical_physical_map[node_i][tpu_i_coord])
                            model.addConstr(and_var <= logical_physical_map[node_j][tpu_j_coord])
                            model.addConstr(and_var >= logical_physical_map[node_i][tpu_i_coord] + logical_physical_map[node_j][tpu_j_coord] - 1)

                            threshold = 0.9
                            model.addGenConstrIndicator(
                                and_var,
                                True,
                                rvar >= threshold,
                                name=f"logical_ring_{r}_{node_i}_to_{node_j}_tpu_{tpu_i_coord}_to_{tpu_j_coord}_routing"
                            )

                            link_bw = 0
                            if self._is_tpu_connected(tpu_i_coord, tpu_j_coord):
                                link_bw = self.physical_topology[tpu_i_coord][tpu_j_coord]['weight']

                            model.addConstr(
                                (quicksum(rvar_all_ring) <= link_bw),
                                name=f"logical_ring_{r}_{node_i}_to_{node_j}_tpu_{tpu_i_coord}_to_{tpu_j_coord}_bw",
                            )

        # mirror routing variables
        mirrored_routing_variables = {}
        for tpu_i_coord in routing_variables:
            for tpu_j_coord in routing_variables[tpu_i_coord]:
                rval_all_ring = routing_variables[tpu_i_coord][tpu_j_coord]
                if tpu_j_coord not in mirrored_routing_variables:
                    mirrored_routing_variables[tpu_j_coord] = {}
                mirrored_routing_variables[tpu_j_coord][tpu_i_coord] = rval_all_ring
                if tpu_i_coord not in mirrored_routing_variables:
                    mirrored_routing_variables[tpu_i_coord] = {}
                mirrored_routing_variables[tpu_i_coord][tpu_j_coord] = rval_all_ring

        # constraint rvar sum per tpu is smaller than injection bandwidth
        for tpu_i_coord in routing_variables:
            model.addConstr(
                quicksum(
                    quicksum(mirrored_routing_variables[tpu_i_coord][tpu_j_coord]) for tpu_j_coord in mirrored_routing_variables[tpu_i_coord]
                )
                  <= self.injection_bw,
                name=f"tpu_{tpu_i_coord}_injection_bw"
            )

        # Objective max min link bw
        epsilon = 1e-6  # Small positive constant
        M = 1e6         # Large constant for upper bound
        optimization_var = model.addVar(vtype=GRB.INTEGER, name="optimization_var")
        for tpu_i_coord in routing_variables:
            for tpu_j_coord in routing_variables[tpu_i_coord]:
                for r, rvar in enumerate(routing_variables[tpu_i_coord][tpu_j_coord]):

                    binary_var = model.addVar(vtype=GRB.BINARY, name=f"binary_var_{tpu_i_coord}_{tpu_j_coord}_ring_{r}")

                    # Enforce binary_var = 1 if and only if rvar > 0
                    model.addConstr(rvar >= epsilon * binary_var, name=f"{tpu_i_coord}_{tpu_j_coord}_ring_{r}_rvar_lb")
                    model.addConstr(rvar <= M * binary_var, name=f"{tpu_i_coord}_{tpu_j_coord}_ring_{r}_rvar_ub")
                    model.addGenConstrIndicator(
                        binary_var,
                        True,
                        optimization_var <= rvar,
                        name=f"optimization_var_{tpu_i_coord}_to_{tpu_j_coord}_ring_{r}",
                    )

        model.setObjective(optimization_var, GRB.MAXIMIZE)

        model.setParam('DualReductions', 0)  # Disable dual reductions to detect unboundedness
        model.optimize()

        # model.computeIIS()
        # model.write("iis.ilp")  # Save IIS to a file for inspection

        ring_tpu_pair_bw = {}
        for v in model.getVars():
            # print(f"{v.varName}: {v.x}")
            if v.varName.startswith("tpu_") and "_ring_" in v.varName:
                parts = v.varName.split("_")
                tpu_i_coord = tuple(map(int, parts[1].strip("()").split(",")))
                tpu_j_coord = tuple(map(int, parts[3].strip("()").split(",")))
                ring_number = int(parts[5])
                print(
                    f"TPU {tpu_i_coord} to TPU {tpu_j_coord} on ring {ring_number}: {v.x}"
                )
                if v.x > 0:
                    if ring_number not in ring_tpu_pair_bw:
                        ring_tpu_pair_bw[ring_number] = {}
                    ring_tpu_pair_bw[ring_number][(tpu_i_coord, tpu_j_coord)] = v.x

        # print(ring_tpu_pair_bw)
        return ring_tpu_pair_bw

def print_tpu_pair_bw(tpu_pair_bw):
    for ring, tpu_pair_bw in tpu_pair_bw.items():
        print(f"Ring {ring}")
        for tpu_pair, bw in tpu_pair_bw.items():
            print(f"TPU pair {tpu_pair}: {bw}")

if __name__ == "__main__":
    from scheduler.val import BLOCK_DIM
    tpu_ids = [0, 1, 4, 5]
    slice = Slice((2, 2, 1), [TPU(0, i) for i in tpu_ids])
    physical_topology = get_graph(dim_x=2, dim_y=2, dim_z=1, wrap_around=False)
    logical_topology = [[0, 1, 3, 2]] # index within in the slice
    bw_allocator = BW_allocator_ILP(slice=slice, logical_topology=logical_topology, tpu_injection_bw=6, link_bw=1, physical_topology=physical_topology)
    ring_tpu_pair_bw = bw_allocator.allocate_bw()
    print("ILP allocation")
    print_tpu_pair_bw(ring_tpu_pair_bw)

    tpu_ids = [0, 1, 4, 5, 16, 17, 20, 21]
    slice = Slice((2, 2, 2), [TPU(0, i) for i in tpu_ids])
    physical_topology = get_graph(dim_x=2, dim_y=2, dim_z=2, wrap_around=False)
    logical_topology = [[0, 1, 3, 2], [4, 5, 7, 6]]
    bw_allocator = BW_allocator_ILP(slice=slice, logical_topology=logical_topology, tpu_injection_bw=6, link_bw=1, physical_topology=physical_topology)
    ring_tpu_pair_bw = bw_allocator.allocate_bw()
    print("ILP allocation")
    print_tpu_pair_bw(ring_tpu_pair_bw)
