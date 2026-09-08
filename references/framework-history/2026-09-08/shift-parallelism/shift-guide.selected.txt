
.. _shift-parallel:

=================
Shift Parallelism
=================

Shift Parallelism is a dynamic inference parallelism strategy that adapts
between tensor parallelism (TP) and Arctic sequence parallelism (SP) in real
time, optimizing for latency, throughput, and cost efficiency — all within a
single deployment. Instead of statically tuning for one metric, Shift
Parallelism responds to real-world traffic by switching modes based on batch
size: using TP for small batches (minimizing output token latency), and SP for
large batches (maximizing throughput and minimizing time-to-first-token).

To enable the shift parallelism, the user sets ``--enable-shift-parallel``.  The
shift between parallelisms is triggered by a threshold, which is set by
``--shift-parallel-threshold`` argument. When shift parallelism is enabled, the
default threshold is 256 and should be a good value in most cases.  In this
case, when batch size is equal or smaller than 256, tensor parallelism is used
with the degree ``SP x TP``, where tp is set with ``--tensor-parallel-size`` and
sp is set with ``--ulysses-sequence-parallel-size``.  Otherwise, a combination
of of SP and TP is applied with respected degrees.

For example, consider a node with eight GPUs, and a model that fits into two. In
this case, we use (SP=4, TP=2) configuration: TP=2 is required to enable the
solution in the first place, and the rest of the GPUs are uitilized with SP=4,
and the engine spanse SPxTP=8 GPUs. In prefill, you want to use (SP=4, TP=2)
rather than full (TP=8) because SP is more efficient with large batch sizes.
Therefore the threshold must be chosen accordingly. In decode, when the
concurrency is low, the batch size is smaller than the threshold and the
parallelism is shifted automatically to TP=8, until batch size is larger again.

This seamless switching is enabled by KV cache invariance — the cache layout
remains consistent between TP and SP as long as ``TP x SP = P`` (total
parallelism), allowing the system to transition modes without disruption.

For more details, refer to the `Snowflake blog post
<https://www.snowflake.com/en/engineering-blog/arctic-inference-shift-parallelism/>`_.

---------------------------
Usage with Arctic Inference
---------------------------

To use Shift Parallelism with Arctic Inference, select a compatible `Llama-3
<https://huggingface.co/models?other=llama-3>`_ model and launch vLLM with a
tensor and sequence parallel configuration where `TP x SP` equals the number of
GPUs.

Arctic Inference will automatically detect traffic conditions and activate the
most optimal mode at runtime.

Here is an example of how run Shift Parallelism with the
`meta-llama/Llama-3.3-70B-Instruct
<https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct>`_ model:

.. code-block:: bash

    export ARCTIC_INFERENCE_ENABLED=1

    python -m vllm.entrypoints.openai.api_server \
        --model meta-llama/Llama-3.3-70B-Instruct \
        --enable-shift-parallel \
        --tensor-parallel-size 4 \
        --ulysses-sequence-parallel-size 2 \
        --shift-parallel-threshold 256

This enables Arctic Inference to dynamically balance latency and throughput
without manual intervention or separate deployments.
