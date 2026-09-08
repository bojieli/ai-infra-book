from morphlux.scheduler import Slice, TPU
from morphlux.scheduler.graph_utils import coordinate_type, get_graph
from morphlux.controller.type import Topology
from typing import List, Tuple, Dict

class BW_allocator:
    def __init__(self, slice: Slice, topo: Topology, tpu_injection_bw: int = 6, link_bw: int = 1, logical_topology: List[List[int]] = None, desired_bw: List[int] = None):
        # slice contains the TPUs assigned to the slice, with the TPU list ordered by the physical connection
        # the logical topology is a list of rings, each ring is a list of logical nodes. 
        # The logical node ID is the index to the physical TPU in the slice TPU list
        # the logical node is ordered as below for a 2x2x4 slice
        #   6--7
        # 4--5
        #   2---3
        # 0---1
        # the desired_bw is a list of integer specifying the bandwidth for each ring
        
        self.slice = slice
        self.logical_topology = logical_topology
        self.injection_bw = tpu_injection_bw
        self.link_bw = link_bw
        self.topo = topo
        self.desired_bw = desired_bw
        self.check_logical_topology()
        # self.logical_physical_map: Dict[coordinate_type, TPU] = {}

    def check_logical_topology(self):
        if self.topo == Topology.RING:
            logical_nodes = set()
            for ring in self.logical_topology:
                for node in ring:
                    logical_nodes.add(node)
            assert len(logical_nodes) <= len(self.slice.tpus), "Number of logical nodes does not match number of TPUs in slice"

        if self.logical_topology and self.desired_bw:
            assert len(self.logical_topology) == len(self.desired_bw)

    def _allocate_bw_ring(self):
        # assume physical topology has uniform bandwidth
        # assume physical topology has wrap around links
        nodes = [tpu.coord for tpu in self.slice.tpus]
        link_bw = self.link_bw
        tpu_ring_map = {}
        tpu_ring_bw_ratio_map = {}
        ring_min_bw_map = {}

        # calculate the mapping between TPU to ring
        for r, ring in enumerate(self.logical_topology):
            for node in ring:
                if node not in tpu_ring_map:
                    tpu_ring_map[node] = [r]
                else:
                    tpu_ring_map[node].append(r)

        # calculate bw ratio to each ring for every TPU
        for node in range(len(self.slice.tpus)):
            tpu_ring_bw_ratio_map[node] = {}
            if not self.desired_bw:
                denom = len(tpu_ring_map[node])
                for r in tpu_ring_map[node]:
                    tpu_ring_bw_ratio_map[node][r] = 1 / denom
            else:
                denom = sum([self.desired_bw[r] for r in tpu_ring_map[node]])
                for r in tpu_ring_map[node]:
                    tpu_ring_bw_ratio_map[node][r] = self.desired_bw[r] / denom

        print(tpu_ring_bw_ratio_map)

        for r, ring in enumerate(self.logical_topology):
            ring_min_bw_map[r] = link_bw
            for node in ring:
                # divide by two because injection bw is shared between two direction of one ring
                ring_min_bw_map[r] = min(ring_min_bw_map[r], (self.injection_bw * tpu_ring_bw_ratio_map[node][r]) // 2)
                if self.desired_bw and ring_min_bw_map[r] < self.desired_bw[r]:
                    raise Exception(f"Cannot allocate desired amount of bw, required {self.desired_bw[r]}, available: {ring_min_bw_map[r]}")
                
        print(ring_min_bw_map)

        ring_tpu_pair_bw = {}
        for r, ring in enumerate(self.logical_topology):
            ring_tpu_pair_bw[r] = {}
            for i, node_i in enumerate(ring):
                node_j = ring[(i+1) % len(ring)]
                tpu_i_coord, tpu_j_coord = nodes[node_i], nodes[node_j]
                ring_tpu_pair_bw[r][(tpu_i_coord, tpu_j_coord)] = ring_min_bw_map[r]

        # print(ring_tpu_pair_bw)
        return ring_tpu_pair_bw
    
    def _allocate_bw_mesh(self):
        #TODO default allocation for mesh
        pass
    
    def allocate_bw(self):
        if self.topo == Topology.RING:
            return self._allocate_bw_ring()

def print_tpu_pair_bw(tpu_pair_bw):
    for ring, tpu_pair_bw in tpu_pair_bw.items():
        print(f"Ring {ring}")
        for tpu_pair, bw in tpu_pair_bw.items():
            print(f"TPU pair {tpu_pair}: {bw}")

if __name__ == "__main__":
    from morphlux.scheduler.val import BLOCK_DIM

    print("Test 2x2x1")
    tpu_ids = [0, 1, 4, 5]
    slice = Slice((2, 2, 1), [TPU(0, i) for i in tpu_ids])
    logical_topology = [[0, 1, 3, 2]] # index within in the slice
    bw_allocator = BW_allocator(slice=slice, topo=Topology.RING,logical_topology=logical_topology, tpu_injection_bw=6, link_bw=1)
    ring_tpu_pair_bw = bw_allocator.allocate_bw()
    print_tpu_pair_bw(ring_tpu_pair_bw)

    print("Test 2x2x2")
    tpu_ids = [0, 1, 4, 5, 16, 17, 20, 21]
    slice = Slice((2, 2, 2), [TPU(0, i) for i in tpu_ids])
    logical_topology = [[0, 1, 3, 2], [4, 5, 7, 6]]
    bw_allocator = BW_allocator(slice=slice, topo=Topology.RING,logical_topology=logical_topology, tpu_injection_bw=6, link_bw=1)
    ring_tpu_pair_bw = bw_allocator.allocate_bw()
    print_tpu_pair_bw(ring_tpu_pair_bw)
    
    print("Test 2x2x4")
    # More simple allocator testing
    tpu_ids = [0, 1, 4, 5, 16, 17, 20, 21, 32, 33, 36, 37, 48, 49, 52, 53]
    logical_topology = [[0, 1, 3, 2], [4, 5, 7, 6], [8, 9, 11, 10], [12, 13, 15, 14], [0, 4, 8, 12], [1, 5, 9, 13], [2, 6, 10, 14], [3, 7, 11, 15]]
    slice = Slice((2, 2, 4), [TPU(0, i) for i in tpu_ids])
    bw_allocator = BW_allocator(slice=slice, topo=Topology.RING, logical_topology=logical_topology, tpu_injection_bw=6, link_bw=1)
    ring_tpu_pair_bw = bw_allocator.allocate_bw()
    print_tpu_pair_bw(ring_tpu_pair_bw)

    print("Test 2x2x2 one big ring")
    # one big ring
    tpu_ids = [0, 1, 4, 5, 16, 17, 20, 21]
    slice = Slice((2, 2, 2), [TPU(0, i) for i in tpu_ids])
    logical_topology = [[0, 1, 3, 7, 5, 4, 6, 2]]
    bw_allocator = BW_allocator(slice=slice, topo=Topology.RING, logical_topology=logical_topology, tpu_injection_bw=6, link_bw=1)
    ring_tpu_pair_bw = bw_allocator.allocate_bw()
    print_tpu_pair_bw(ring_tpu_pair_bw)
