from __future__ import annotations
import os
import lighteval.models.vllm.vllm_model as vllm_model

from typing import Optional
from tqdm import tqdm
from dataclasses import dataclass
from vllm import LLM

from lighteval.data import GenerativeTaskDataset
from lighteval.models.model_output import GenerativeResponse
from lighteval.tasks.requests import GreedyUntilRequest
from lighteval.models.model_input import GenerationParameters
from lighteval.utils.utils import EnvConfig, as_list


@dataclass
class VLLMMODELConfigEdit:
    pretrained: str
    gpu_memory_utilization: float = 0.9  # lower this if you are running out of memory
    revision: str = "main"  # revision of the model
    dtype: str | None = None
    tensor_parallel_size: int = 1  # how many GPUs to use for tensor parallelism
    pipeline_parallel_size: int = 1  # how many GPUs to use for pipeline parallelism
    data_parallel_size: int = 1  # how many GPUs to use for data parallelism
    max_model_length: int | None = (
        None  # maximum length of the model, ussually infered automatically. reduce this if you encouter OOM issues, 4096 is usually enough
    )
    swap_space: int = 4  # CPU swap space size (GiB) per GPU.
    seed: int = 1234
    trust_remote_code: bool = False
    use_chat_template: bool = False
    add_special_tokens: bool = True
    multichoice_continuations_start_space: bool = (
        True  # whether to add a space at the start of each continuation in multichoice generation
    )
    pairwise_tokenization: bool = (
        False  # whether to tokenize the context and continuation separately or together.
    )
    generation_parameters: GenerationParameters = (
        None  # sampling parameters to use for generation
    )
    enforce_eager: bool = None
    enable_prefix_caching: bool = None
    enable_chunked_prefill: bool = None

    subfolder: Optional[str] = None

    def __post_init__(self):
        if not self.generation_parameters:
            self.generation_parameters = GenerationParameters()


vllm_model.VLLMModelConfig = VLLMMODELConfigEdit


def _create_auto_model(self, config: vllm_model.VLLMModelConfig, env_config: EnvConfig) -> Optional[LLM]:  # type: ignore
    """
    Creates an instance of the pretrained HF model.

    Args:
        pretrained (str): The name or path of the pretrained model.
        revision (str): The revision of the model.
        subfolder (Optional[str], optional): The subfolder within the model. Defaults to None.
        max_memory (Optional[dict], optional): The maximum memory to allocate for the model per GPU. Defaults to None.
        device_map (Optional[dict], optional): The device mapping for the model. Defaults to None.
        torch_dtype (Optional[Union[str, torch.dtype]], optional): The torch data type for the model. Defaults to None.
        quantization_config (Optional[Union[BitsAndBytesConfig, GPTQConfig]], optional): The quantization configuration for the model. Defaults to None.
        trust_remote_code (bool, optional): Whether to trust remote code. Defaults to False.
        cache_dir (str, optional): The cache directory for the model. Defaults to "/scratch".

    Returns:
        transformers.PreTrainedModel: The created auto model instance.
    """

    quant_method = os.environ["QUANT_METHOD"]
    self.model_args = {
        "model": config.pretrained,
        "gpu_memory_utilization": float(config.gpu_memory_utilization),
        "revision": config.revision
        + (f"/{config.subfolder}" if config.subfolder is not None else ""),
        "dtype": config.dtype,
        "trust_remote_code": config.trust_remote_code,
        "tensor_parallel_size": int(config.tensor_parallel_size),
        "pipeline_parallel_size": int(config.pipeline_parallel_size),
        "max_model_len": self._max_length,
        "swap_space": 4,
        "seed": config.seed,
        "enforce_eager": config.enforce_eager,
        "enable_prefix_caching": config.enable_prefix_caching,
        "enable_chunked_prefill": config.enable_chunked_prefill,
        "quantization": quant_method,
    }
    if int(config.data_parallel_size) > 1:
        self.model_args["distributed_executor_backend"] = "ray"
        self._batch_size = "auto"
        return None

    model = LLM(**self.model_args)

    # If the max_length can't get extracted from the config, it will be inferred from the model
    # Inferring from the tokenizer will cause vllm to bug for models with mismatches between model
    # config and tk config, like mistralai/Mistral-7B-v0.1
    if self._max_length is None:
        self._max_length = model.llm_engine.model_config.max_seq_len_to_capture

    return model


def greedy_until(
    self,
    requests: list[GreedyUntilRequest],
    override_bs: Optional[int] = None,
) -> list[GenerativeResponse]:
    """
    Generates responses using a greedy decoding strategy until certain ending conditions are met.

    Args:
        requests (list[Request]): list of requests containing the context and ending conditions.
        override_bs (int, optional): Override the batch size for generation. Defaults to None.

    Returns:
        list[GenerateReturn]: list of generated responses.
    """
    for request in requests:
        request.stop_sequence = as_list(request.stop_sequence) + [
            self.tokenizer.eos_token
        ]
        request.tokenized_context = self.tok_encode(request.context)

    dataset = GenerativeTaskDataset(
        requests=requests, num_dataset_splits=self.DATASET_SPLITS
    )
    results = []

    for _ in tqdm(
        dataset.splits_start_end_iterator(),
        total=dataset.num_dataset_splits,
        desc="Splits",
        position=0,
        disable=False,  # self.disable_tqdm,
    ):
        # For chat models, generation stops with EOS token, so we don't need to specify stop tokens
        if self.use_chat_template:
            stop_tokens = []
        else:
            # NOTE: we are assuming all items in a batch behave similarly (same
            # stop_tokens and max_tokens genrated) which is not necessarily
            # the case! Because of that we only use batch size of 1
            stop_tokens = dataset[0].stop_sequence

        max_new_tokens = (
            self._config.generation_parameters.max_new_tokens
            or dataset[0].generation_size
        )
        returns_logits = dataset[0].use_logits
        num_samples = dataset[0].num_samples

        context = [c.context for c in dataset]
        tokenized = self.tokenizer(context, add_special_tokens=self.add_special_tokens)

        # The main question for this step is the following:
        # Would we rather truncate the prompt to allow generation to go to max_new_tokens, at the risk
        # of losing some meaning, or have some generations that are exceedingly short?
        # The choice we go for here is to avoid truncating the prompt if we can, since it
        # should have been managed by the prompt creator/few shot manager if requested by the user.
        inputs = tokenized["input_ids"]
        # context_size = len(inputs[0])

        # # left truncate the inputs to the maximum length
        # if max_new_tokens is not None:
        #     if context_size + max_new_tokens > self.max_length:
        #         logger.warning(
        #             f"{context_size + max_new_tokens=} which is greater than {self.max_length=}. Truncating context to {self.max_length - max_new_tokens} tokens."
        #         )
        #         context_size = self.max_length - max_new_tokens
        #         if context_size < 0:
        #             logger.critical(
        #                 f"{context_size=} is less than 0, either reduce the max_new_tokens or increase model max length."
        #             )
        #             raise ValueError("Context size is less than 0.")
        #         inputs = [input[-context_size:] for input in inputs]
        # else:
        #     if context_size > self.max_length:
        #         logger.warning(
        #             f"{context_size=} which is greater than {self.max_length=}. Truncating context to {self.max_length} tokens."
        #         )
        #         context_size = self.max_length
        #         inputs = [input[-context_size:] for input in inputs]

        vllm_outputs = self._generate(
            inputs=inputs,
            max_new_tokens=max_new_tokens,
            stop_tokens=stop_tokens,
            returns_logits=returns_logits,
            num_samples=num_samples,
        )

        for vllm_output in vllm_outputs:
            output_token_ids = [outputs.token_ids for outputs in vllm_output.outputs]
            logprobs = [output.logprobs for output in vllm_output.outputs] or []
            logprobs = [
                logprob[token_id].logprob
                for token_id, logprob in zip(output_token_ids[0], logprobs[0])
            ]
            result = [output.text for output in vllm_output.outputs]
            input_token_ids = vllm_output.prompt_token_ids

            cur_response = GenerativeResponse(
                result=result,
                logits=logprobs,
                generated_tokens=list(output_token_ids),
                input_tokens=input_token_ids,
            )
            results.append(cur_response)

    return dataset.get_original_order(results)


vllm_model.VLLMModel.greedy_until = greedy_until
vllm_model.VLLMModel._create_auto_model = _create_auto_model
