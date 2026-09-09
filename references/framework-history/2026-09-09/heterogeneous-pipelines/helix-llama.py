from typing import List, Optional

import torch
import torch.nn as nn
from transformers import LlamaConfig

from vllm.model_executor.layers.layernorm import RMSNorm
from vllm.model_executor.layers.linear import (LinearMethodBase)
from vllm.model_executor.layers.logits_processor import LogitsProcessor
from vllm.model_executor.layers.sampler import Sampler
from vllm.model_executor.layers.vocab_parallel_embedding import (
    DEFAULT_VOCAB_PADDING_SIZE, ParallelLMHead, VocabParallelEmbedding)
from vllm.model_executor.models.llama import LlamaDecoderLayer
from vllm.model_executor.sampling_metadata import SamplingMetadata
from vllm.sequence import SamplerOutput


class LlamaPipelineStage(nn.Module):
    packed_modules_mapping = {
        "qkv_proj": [
            "q_proj",
            "k_proj",
            "v_proj",
        ],
        "gate_up_proj": [
            "gate_proj",
            "up_proj",
        ],
    }

    embedding_modules = {
        "embed_tokens": "input_embeddings",
        "lm_head": "output_embeddings",
    }
    embedding_padding_modules = ["lm_head"]

    def __init__(
            self,
            config: LlamaConfig,
            linear_method: Optional[LinearMethodBase] = None,
            lora_config=None,
    ) -> None:
        super().__init__()
        self.config = config
        self.linear_method = linear_method
        self.vocab_size = config.vocab_size

        layer_id = config.layer_id
        self.layer_id = layer_id

        self.decoder_layer = LlamaDecoderLayer(config, linear_method)
        if layer_id == 0:
            self.embed_tokens = VocabParallelEmbedding(
                self.vocab_size,
                config.hidden_size,
                org_num_embeddings=config.vocab_size,
            )

        if layer_id == self.config.num_hidden_layers - 1:
            self.unpadded_vocab_size = config.vocab_size
            self.norm = RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
            self.lm_head = ParallelLMHead(
                self.unpadded_vocab_size,
                config.hidden_size,
                org_num_embeddings=config.vocab_size,
                padding_size=DEFAULT_VOCAB_PADDING_SIZE
                # We need bigger padding if using lora for kernel
                # compatibility
                if not lora_config else lora_config.lora_vocab_padding_size,
            )

            if lora_config:
                self.unpadded_vocab_size += lora_config.lora_extra_vocab_size

            logit_scale = getattr(config, "logit_scale", 1.0)
            self.logits_processor = LogitsProcessor(self.unpadded_vocab_size,
                                                    config.vocab_size, logit_scale)
            self.sampler = Sampler()

    def forward(self, **kwargs):
        positions = kwargs["positions"]
        kv_cache = kwargs["kv_cache"]
        attn_metadata = kwargs["attn_metadata"]
        if self.layer_id == 0:
            input_ids = kwargs["input_ids"]
            inputs_embeds = (kwargs["input_embeds"]
                             if "input_embeds" in kwargs else None)
            if inputs_embeds is not None:
                hidden_states = inputs_embeds
            else:
                hidden_states = self.get_input_embeddings(input_ids)
            residual = None
            hidden_states, residual = self.decoder_layer(
                positions,
                hidden_states,
                kv_cache,
                attn_metadata,
                residual,
            )
        else:
            hidden_states = kwargs["hidden_states"]
            residual = None
            hidden_states, residual = self.decoder_layer(
                positions,
                hidden_states,
                kv_cache,
                attn_metadata,
                residual,
            )
            if self.layer_id == self.config.num_hidden_layers - 1:
                hidden_states = self.norm(hidden_states)
        return hidden_states

    def get_input_embeddings(self, input_ids: torch.Tensor) -> torch.Tensor:
        return self.embed_tokens(input_ids)

    def load_weights(self,
                     model_name_or_path: str,
                     cache_dir: Optional[str] = None,
                     load_format: str = "auto",
                     revision: Optional[str] = None):
        # FIXME: fix this part
        raise NotImplementedError()

    def compute_logits(self, hidden_states: torch.Tensor,
                       sampling_metadata: SamplingMetadata) -> torch.Tensor:
        logits = self.logits_processor(self.lm_head.weight, hidden_states,
                                       sampling_metadata)
        return logits

    def sample(
            self,
            logits: torch.Tensor,
            sampling_metadata: SamplingMetadata,
    ) -> Optional[SamplerOutput]:
        next_tokens = self.sampler(logits, sampling_metadata)
        return next_tokens


from vllm.model_executor.models import _MODELS, llama

_MODELS["LlamaForCausalLM"] = ("llama", "LlamaPipelineStage")
llama.LlamaPipelineStage = LlamaPipelineStage
