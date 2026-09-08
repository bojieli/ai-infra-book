# Copyright 2025 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Hashable, KeysView, List, Optional, Sequence

import numpy as np

from arctic_inference.suffix_decoding._C import SuffixTree, Draft


@dataclass
class SuffixDecodingDraft:
    """
    A dataclass representing the result of a speculation using SuffixDecoding.

    Attributes:
        token_ids (List[int]): List of token IDs in the speculation result.
        parents (List[int]): List of parent indices for each token used to
            encode the tree structure. The parent token of token_ids[i] is
            token_ids[parents[i]].
        probs (List[float]): List of estimated probabilities for each token.
        score (float): The overall score of the suffix match computed as the
            sum of the estimated probabilities of each speculated token.
        match_len (int): The length of the context match that yielded this
            speculation result.
    """
    token_ids: List[int] = field(default_factory=list)
    parents: List[int] = field(default_factory=list)
    probs: List[float] = field(default_factory=list)
    score: float = 0.0
    match_len: int = 0

    @staticmethod
    def from_native(draft: Draft) -> SuffixDecodingDraft:
        return SuffixDecodingDraft(
            token_ids=draft.token_ids,
            parents=draft.parents,
            probs=draft.probs,
            score=draft.score,
            match_len=draft.match_len,
        )


class SuffixDecodingCache:
    
    def __init__(self,
                 max_tree_depth: int = 64,
                 max_cached_requests: int = -1):
        """
        Initialize the SuffixDecodingCache.

        Args:
            max_tree_depth (int): The maximum depth of the suffix trees.
            max_cached_requests (int, optional): The maximum number of cached
                requests. Eviction is triggered when the limit is reached. `-1`
                means no limit on the number of cached requests.
        """
        if max_cached_requests > 0x7FFFFFFF:
            raise ValueError("max_cached_requests must be at most 2^31")

        self._max_tree_depth = max_tree_depth
        self._max_cached_requests = max_cached_requests

        # Global suffix tree caches previous responses in a single tree.
        self._global_tree = SuffixTree(max_tree_depth)

        # Local suffix trees cache prompts for each active request separately.
        self._local_trees = {}

        # Maps between Python request ID and int32_t sequence ID. Tracks all
        # request IDs that are in the global tree.
        self._req_to_seq_id = {}
        self._seq_to_req_id = {}

        # Unused sequence ID to assign to a new request ID.
        self._next_seq_id = 0

    @property
    def max_tree_depth(self) -> int:
        return self._max_tree_depth

    @property
    def max_cached_requests(self) -> int:
        return self._max_cached_requests

    @property
    def active_requests(self) -> KeysView:
        """
        Returns a view of the currently active request IDs. Active requests are
        those that have been started via `start_request` and not yet stopped
        via `stop_request`. The prompts of active requests are stored so they
        can be used during speculation for the same request.
        """
        return self._local_trees.keys()

    @property
    def cached_requests(self) -> KeysView:
        """
        Returns a view of all request IDs that have their responses cached in
        the global suffix tree. The response for the cached request can be used
        during speculation for other requests, until the response is evicted.
        """
        return self._req_to_seq_id.keys()

    def start_request(
        self,
        req_id: Hashable,
        prompt_token_ids: np.ndarray | Sequence[int],
    ):
        """
        This method should be called when starting to process a new request. It
        will store the prompt for the request, allowing future speculations for
        the same request to use the prompt context. The prompt will be stored
        until `stop_request` is called. If `max_cached_requests != 0`, then a
        new slot is allocated in the global cache for the response, triggering
        cache eviction (FIFO order) if needed.

        Args:
            req_id (Hashable): The request identifier. Must be a hashable value
                that uniquely identifies the request.
            prompt_token_ids (np.ndarray | Sequence[int]): A sequence of token
                IDs representing the prompt of the request.

        Raises:
            ValueError: If a request with the same `req_id` is already active
                or cached.
        """
        if req_id in self._local_trees:
            raise ValueError(f"Request '{req_id}' is already active")

        if isinstance(prompt_token_ids, np.ndarray):
            # If input is a numpy array, use the zero-copy ndarray overload.
            self._validate_ndarray(prompt_token_ids)
            extend_func = SuffixTree.extend_ndarray
        else:
            extend_func = SuffixTree.extend

        self._local_trees[req_id] = SuffixTree(self._max_tree_depth)
        extend_func(self._local_trees[req_id], 0, prompt_token_ids)
        if self._max_cached_requests != 0:
            # Global cache is enabled.
            if req_id in self._req_to_seq_id:
                # Evict existing cached response for the request if present.
                self.evict_cached_response(req_id)
            # Allocate a new seq_id for the request.
            self._generate_seq_id(req_id)

    def stop_request(self, req_id: Hashable):
        """
        This method should be called when a request is completed. It will evict
        the prompt for the request, freeing up memory. The request's response
        may still be cached in the global cache until it is evicted.

        Args:
            req_id (Hashable): The request identifier. Must be a hashable value
                that uniquely identifies the request.

        Raises:
            ValueError: If the request with the given `req_id` is not active.
        """
        if req_id not in self._local_trees:
            raise ValueError(f"Request '{req_id}' is not active")
        del self._local_trees[req_id]

    def add_active_response(
        self,
        req_id: Hashable,
        token_ids: np.ndarray | Sequence[int],
    ):
        """
        Update the cached response for a given request by appending token(s) to
        its end. Once the response is updated, the new tokens can be used for
        future speculations for all requests.

        Args:
            req_id (Hashable): The unique identifier for the request.
            token_ids (np.ndarray | Sequence[int]): A sequence of token IDs to
                be appended to the response for the given request.

        Raises:
            ValueError: If the request with the given `req_id` is not active.
        """
        if req_id not in self._local_trees:
            raise ValueError(f"Request '{req_id}' is not active")

        if isinstance(token_ids, np.ndarray):
            # If input is a numpy array, use the zero-copy ndarray overload.
            self._validate_ndarray(token_ids)
            extend_func = SuffixTree.extend_ndarray
        else:
            extend_func = SuffixTree.extend

        # Update the local tree for the active request.
        extend_func(self._local_trees[req_id], 0, token_ids)

        # Also update the response if the request is in the global cache (it
        # may be evicted from the global cache before the request is stopped).
        if req_id in self._req_to_seq_id:
            seq_id = self._req_to_seq_id[req_id]
            extend_func(self._global_tree, seq_id, token_ids)

    def evict_cached_response(self, req_id: Hashable):
        """
        Evicts the given request's response from the global cache. `req_id` can
        be safely reused for a new request after eviction.

        Args:
            req_id (Hashable): The unique identifier for the request that
                should be evicted.

        Raises:
            ValueError: If no response exists for the given request identifier.
        """
        if req_id not in self._req_to_seq_id:
            raise ValueError(f"Request '{req_id}' is not cached")
        seq_id = self._req_to_seq_id.pop(req_id)
        self._seq_to_req_id.pop(seq_id)
        self._global_tree.remove(seq_id)

    def speculate(
        self,
        req_id: Hashable,
        context: np.ndarray | Sequence[int],
        max_spec_tokens: Optional[int] = None,
        max_spec_factor: float = 1.0,
        max_spec_offset: float = 0.0,
        min_token_prob: float = 0.1,
        use_tree_spec: bool = False,
    ) -> SuffixDecodingDraft:
        """
        Speculates and returns the most likely continuation of a given token
        context using the request's prompt and the global cache of previous
        responses. This method can only be called for active requests (i.e.
        after calling `start_request` and before calling `stop_request`).

        Args:
            req_id (Hashable): The unique identifier for the request.
            context (np.ndarray | Sequence[int]): A sequence of token IDs to
                match and speculate subsequent tokens from.
            max_spec_tokens (int): Maximum number of tokens to speculate. If 0,
                uses the cache's max_depth.
            max_spec_factor (float): Factor that limits speculation based on
                matched context length. The number of speculated tokens is
                limited by `max_spec_factor * match_length + max_spec_offset`.
            max_spec_offset (float): Offset that limits speculation based on
                matched context length. The number of speculated tokens is
                limited by `max_spec_factor * match_length + max_spec_offset`.
            min_token_prob (float): Minimum estimated probability threshold for
                draft tokens.
            use_tree_spec (bool): If True, uses tree-based speculation.
        
        Returns:
            The speculation result containing the most likely continuation
            tokens, their probabilities, and overall score.

        Raises:
            ValueError: If the request with the given `req_id` is not active.
        """
        if req_id not in self._local_trees:
            raise ValueError(f"Request '{req_id}' is not active")

        if isinstance(context, np.ndarray):
            # If input is a numpy array, use the zero-copy ndarray overload.
            self._validate_ndarray(context)
            spec_func = SuffixTree.speculate_ndarray
        else:
            spec_func = SuffixTree.speculate

        if max_spec_tokens is None:
            max_spec_tokens = self.max_depth

        if len(context) > self._max_tree_depth:
            context = context[-self._max_tree_depth :]

        draft1 = spec_func(
            self._local_trees[req_id],
            context,
            max_spec_tokens,
            max_spec_factor,
            max_spec_offset,
            min_token_prob,
            use_tree_spec)

        draft2 = spec_func(
            self._global_tree,
            context,
            max_spec_tokens,
            max_spec_factor,
            max_spec_offset,
            min_token_prob,
            use_tree_spec)

        draft = draft1 if draft1.score >= draft2.score else draft2

        return SuffixDecodingDraft.from_native(draft)

    def _generate_seq_id(self, req_id: Hashable) -> int:
        # Find the next available seq_id not used by an active request.
        while True:
            seq_id = self._next_seq_id
            # Increment to the next non-negative int32_t value.
            self._next_seq_id = (self._next_seq_id + 1) & 0x7FFFFFFF
            if (seq_id not in self._seq_to_req_id or
                    self._seq_to_req_id[seq_id] not in self._local_trees):
                break
        # Check if the seq_id is used by an inactive but cached request.
        if seq_id in self._seq_to_req_id:
            # This seq_id is already used, should be a very rare case that
            # only happens when the seq_id has wrapped around and collided.
            # We evict the old cached request to free up the seq_id.
            del self._req_to_seq_id[self._seq_to_req_id[seq_id]]
            del self._seq_to_req_id[seq_id]
            self._global_tree.remove(seq_id)
        # Allocate the seq_id to the new req_id.
        self._req_to_seq_id[req_id] = seq_id
        self._seq_to_req_id[seq_id] = req_id
        self._maybe_evict_requests(seq_id)
        return seq_id

    def _maybe_evict_requests(self, new_seq_id: int):
        if self._max_cached_requests < 0:
            # Negative value means no global cache size limit.
            return
        assert self._max_cached_requests != 0  # Global cache must be enabled.
        while len(self._req_to_seq_id) > self._max_cached_requests:
            # Evict the first eligible request. Should be FIFO order in Python
            # 3.7+ since dict preserves insertion order. Avoid evicting the
            # request that was just added (new_seq_id).
            for req_id, seq_id in self._req_to_seq_id.items():
                if seq_id != new_seq_id:
                    self.evict_cached_response(req_id)
                    break

    def _validate_ndarray(self, arr: np.ndarray):
        if arr.ndim != 1:
            raise ValueError(f"ndarray input must have ndim=1, "
                             f"got ndim={arr.ndim}")
        if arr.dtype != np.int32:
            raise ValueError(f"ndarray input must have dtype=int32, "
                             f"got dtype={arr.dtype.name}")
        if not arr.flags["CONTIGUOUS"]:
            raise ValueError(f"ndarray input must be contiguous")
