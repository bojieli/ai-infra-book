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

import argparse
from dataclasses import dataclass

from vllm.engine.arg_utils import AsyncEngineArgs, EngineArgs
from vllm.utils import FlexibleArgumentParser

from arctic_inference.patching import ArcticPatch


@dataclass
class ArcticArgs:

    ulysses_sequence_parallel_size: int = 1
    enable_shift_parallel: bool = False
    shift_parallel_threshold: int = 512


@dataclass
class ArcticEngineArgs(EngineArgs, ArcticArgs):
    pass


@dataclass
class ArcticAsyncEngineArgs(AsyncEngineArgs, ArcticArgs):
    pass


_current_arctic_args: ArcticArgs = None


def get_current_arctic_args() -> ArcticArgs:
    return _current_arctic_args


class EngineArgsPatch(ArcticPatch[EngineArgs]):

    _orig_add_cli_args = EngineArgs.add_cli_args
    _orig_from_cli_args = EngineArgs.__dict__["from_cli_args"].__wrapped__
    _orig_create_engine_config = EngineArgs.create_engine_config

    def __new__(cls, *args, **kwargs):
        # Override __new__ to return an ArcticEngineArgs instead of an
        # EngineArgs when creating a new instance of the class.
        if cls is EngineArgs:
            return ArcticEngineArgs.__new__(ArcticEngineArgs,
                                            *args, **kwargs)
        return super(EngineArgs, cls).__new__(cls)

    @staticmethod
    def add_cli_args(parser: FlexibleArgumentParser) -> FlexibleArgumentParser:
        parser = EngineArgsPatch._orig_add_cli_args(parser)
        parser.add_argument(
            "--ulysses-sequence-parallel-size",
            type=int,
            default=ArcticEngineArgs.ulysses_sequence_parallel_size,
            help="Number of Ulysses sequence parallel replicas",
        )
        parser.add_argument(
            "--enable-shift-parallel",
            action='store_true',
            help='If True, enable shift parallelism.')
        parser.add_argument(
            "--shift-parallel-threshold",
            type=int,
            default=ArcticEngineArgs.shift_parallel_threshold,
            help=("Ulysses sequence parallel if batch size > threshold, "
                  "otherwise tensor parallel across the whole world size"),
        )
        return parser

    @classmethod
    def from_cli_args(cls, args: argparse.Namespace):
        if cls is EngineArgs:
            return EngineArgsPatch._orig_from_cli_args(ArcticEngineArgs, args)
        if cls is AsyncEngineArgs:
            return EngineArgsPatch._orig_from_cli_args(ArcticAsyncEngineArgs,
                                                       args)
        return EngineArgsPatch._orig_from_cli_args(cls, args)

    def create_engine_config(self, *args, **kwargs):
        # Temporarily makes the engine args available as a global variable when
        # running this method so that the customized config classes can grab
        # their values during initialization.
        global _current_arctic_args
        try:
            _current_arctic_args = self
            return self._orig_create_engine_config(*args, **kwargs)
        finally:
            _current_arctic_args = None


class AsyncEngineArgsPatch(ArcticPatch[AsyncEngineArgs]):

    def __new__(cls, *args, **kwargs):
        # Override __new__ to return an ArcticAsyncEngineArgs instead of an
        # AsyncEngineArgs when creating a new instance of the class.
        if cls is AsyncEngineArgs:
            return ArcticAsyncEngineArgs.__new__(ArcticAsyncEngineArgs,
                                                 *args, **kwargs)
        return super(AsyncEngineArgs, cls).__new__(cls)
