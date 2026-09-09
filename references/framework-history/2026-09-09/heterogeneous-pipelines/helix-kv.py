# 2024.04.22 Yixuan Mei

from typing import Dict, List, Tuple

from simulator.event_simulator.cluster_simulator import ClusterSimulator
from simulator.event_simulator.utils import AVG_OUTPUT_LEN


class KVParameters:
    def __init__(self, expected_kv_hwm: float, expected_output_length_ratio: float) -> None:
        """
        Parameters for kv cache expectation

        :param expected_kv_hwm: expected kv cache high water mark, if the usage is larger than this value,
                                we can not schedule more requests in this node
        :param expected_output_length_ratio: a length estimation on avg. output length in the kv cache
        """
        self.expected_kv_hwm: float = expected_kv_hwm
        self.expected_output_length_ratio: float = expected_output_length_ratio


class KVExpectedStatus:
    def __init__(self, node_uid: int, start_layer_idx: int, end_layer_idx: int, total_capacity: int,
                 expected_kv_hwm: float, expected_output_length_ratio: float) -> None:
        """
        An entry of kv cache expectation

        :param node_uid: uid of the node
        :param start_layer_idx: start layer index
        :param end_layer_idx: end layer index
        :param total_capacity: total kv cache capacity
        :param expected_kv_hwm: expected kv cache high water mark, if the usage is larger than this value,
                                we can not schedule more requests in this node
        :param expected_output_length_ratio: a length estimation on avg. output length in the kv cache
        :return: None
        """
        # basic info
        # [start_layer_idx, end_layer_idx)
        self.node_uid: int = node_uid
        self.start_layer_idx: int = start_layer_idx
        self.end_layer_idx: int = end_layer_idx

        # parameters
        self.expected_kv_hwm: float = expected_kv_hwm
        self.expected_output_length_ratio: float = expected_output_length_ratio

        # kv cache
        self.total_kv_capacity: int = total_capacity
        self.avail_kv_capacity: int = total_capacity

    def add_request(self, input_seq_length: int, cur_start: int, cur_end: int) -> None:
        """
        Add a request. (seq length = real input + avg_output * EXPECTED_OUTPUT_LENGTH_RATIO)

        :param input_seq_length: input sequence length
        :param cur_start: start layer id
        :param cur_end: end layer id
        :return: None
        """
        assert self.start_layer_idx <= cur_start < cur_end <= self.end_layer_idx, "Bad start end idx!"
        expected_length = int(input_seq_length + AVG_OUTPUT_LEN * self.expected_output_length_ratio)
        self.avail_kv_capacity -= expected_length * (cur_end - cur_start)
        assert self.avail_kv_capacity >= 0, f"Node {self.node_uid} will run out of KV cache in expectation!"

    def remove_request(self, input_seq_length: int, cur_start: int, cur_end: int) -> None:
        """
        Remove a request. (seq length = real input + avg_output * EXPECTED_OUTPUT_LENGTH_RATIO)

        :param input_seq_length: input sequence length
        :param cur_start: start layer id
        :param cur_end: end layer id
        :return: None
        """
        assert self.start_layer_idx <= cur_start < cur_end <= self.end_layer_idx, "Bad start end idx!"
        expected_length = int(input_seq_length + AVG_OUTPUT_LEN * self.expected_output_length_ratio)
        self.avail_kv_capacity += expected_length * (cur_end - cur_start)
        assert self.avail_kv_capacity <= self.total_kv_capacity, f"Double release found!"

    def check_can_add(self, input_seq_length: int) -> bool:
        """
        Check whether we can add a new request without violating EXPECTED_KV_HWM
        Note: during checking, we assume the request will use all layers of the node

        :param input_seq_length: input sequence length
        :return: true if we can add more, false if we can not
        """
        expected_length = int(input_seq_length + AVG_OUTPUT_LEN * self.expected_output_length_ratio)
        expected_availability = self.avail_kv_capacity - expected_length * (self.end_layer_idx - self.start_layer_idx)
        if expected_availability >= (1 - self.expected_kv_hwm) * self.total_kv_capacity:
            return True
        else:
            return False


class KVExpectation:
    def __init__(self, kv_param: KVParameters) -> None:
        """
        Stores the expected kv cache status
        """
        # parameters
        self.kv_param: KVParameters = kv_param

        # status
        self.initialized: bool = False
        self.total_num_layers: int = -1
        self.node_uid_to_status: Dict[int, KVExpectedStatus] = {}

    def initialize(self, simulator: ClusterSimulator) -> None:
        """
        Initialize the KV expectations from the cluster simulator.

        :param simulator: cluster simulator
        :return: None
        """
        assert not self.initialized, "KV Expectation already initialized!"
        self.initialized = True

        # set total num layers
        self.total_num_layers = simulator.model_manager.get_num_layers()

        # enumerate through all compute nodes
        for compute_node_id, compute_node in simulator.compute_nodes.items():
            assert compute_node_id not in self.node_uid_to_status, "Duplicate compute node found!"
            start_layer_idx = min(compute_node.in_vram_model_layers.keys())
            end_layer_idx = max(compute_node.in_vram_model_layers.keys()) + 1
            assert sorted(list(compute_node.in_vram_model_layers.keys())) == \
                   list(range(start_layer_idx, end_layer_idx)), "Model is not continuous!"
            self.node_uid_to_status[compute_node_id] = KVExpectedStatus(
                node_uid=compute_node_id, start_layer_idx=start_layer_idx, end_layer_idx=end_layer_idx,
                total_capacity=compute_node.kv_cache_capacity,
                expected_kv_hwm=self.kv_param.expected_kv_hwm,
                expected_output_length_ratio=self.kv_param.expected_output_length_ratio
            )

    def add_request(self, input_seq_length: int, route: List[int],
                    start_idx_list: List[int], end_idx_list: List[int]) -> None:
        """
        Add a request that consume some kv cache. (Call after route is determined)

        :param input_seq_length: input sequence length
        :param route: a list of node uids
        :param start_idx_list: start layer idx list (inclusive)
        :param end_idx_list: end layer idx list (exclusive)
        :return: None
        """
        for node_uid, start_idx, end_idx in zip(route, start_idx_list, end_idx_list):
            self.node_uid_to_status[node_uid].add_request(input_seq_length=input_seq_length,
                                                          cur_start=start_idx, cur_end=end_idx)

    def remove_request(self, input_seq_length: int, route: List[int],
                       start_idx_list: List[int], end_idx_list: List[int]) -> None:
        """
        Remove a request. (Call after last decode finished)

        :param input_seq_length: input sequence length
        :param route: a list of node uids
        :param start_idx_list: start layer idx list (inclusive)
        :param end_idx_list: end layer idx list (exclusive)
        :return: None
        """
        for node_uid, start_idx, end_idx in zip(route, start_idx_list, end_idx_list):
            self.node_uid_to_status[node_uid].remove_request(input_seq_length=input_seq_length,
                                                             cur_start=start_idx, cur_end=end_idx)

    def check_can_add(self, node_uid: int, input_seq_length: int) -> bool:
        """
        Check whether we can add a new request without violating EXPECTED_KV_HWM
        Note: during checking, we assume the request will use all layers of the node

        :param node_uid: uid of the node
        :param input_seq_length: input sequence length
        :return: true if we can add more, false if we can not
        """
        return self.node_uid_to_status[node_uid].check_can_add(input_seq_length=input_seq_length)

    def bottleneck_usage(self) -> float:
        """
        Get bottleneck kv cache usage.

        :return: a value in [0, 1)
        """
        free_kv_entries = [0 for _ in range(self.total_num_layers)]
        total_kv_entries = [0 for _ in range(self.total_num_layers)]
        for _, kv_status in self.node_uid_to_status.items():
            cur_free_entries = kv_status.avail_kv_capacity / (kv_status.end_layer_idx - kv_status.start_layer_idx)
            cur_total_entries = kv_status.total_kv_capacity / (kv_status.end_layer_idx - kv_status.start_layer_idx)
            for layer_id in range(kv_status.start_layer_idx, kv_status.end_layer_idx):
                free_kv_entries[layer_id] += cur_free_entries
                total_kv_entries[layer_id] += cur_total_entries
        kv_entry_usage = [1 - free / total for free, total in zip(free_kv_entries, total_kv_entries)]
        return max(kv_entry_usage)

    def get_node_usage(self, node_uid: int) -> Tuple[int, int]:
        """
        Get node usage for given node.

        :param node_uid: uid of the node
        :return: used, total
        """
        target_node = self.node_uid_to_status[node_uid]
        total = target_node.total_kv_capacity
        used = total - target_node.avail_kv_capacity
        return used, total
