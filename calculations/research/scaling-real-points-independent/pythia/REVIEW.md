# Pythia v2 N and validation-loader review

Source revision: GPT-NeoX d36f623fa2634f7824eaa83671f81f4c5773e120, resolving the recorded d36f623 run hash. Seven selected run segments cover five model sizes. Small implementation originals and their lock are in this directory; run config JSON remains in the author's pythia/v2-loss-runs.json. No fitting or new loss filtering was performed.

## Parameter definition

Recorded no_weight_tying=true, rotary positions, GELU, LayerNorm, padded vocabulary50304 and the fixed implementation give N=12*L*H²+13*L*H+2*H+2*50304*H. This includes independent embedding and output matrices, attention/MLP biases, two affine layer norms per layer and final affine norm. Rotary has no learned position matrix. Column/row linear defaults include bias; the vocabulary output is explicitly bias-free. These config/source counts are70426624,162322944,405334016,1414647808,2775208960 for the five selected shapes. They are not rounded70e6/160e6/... labels, nor nonembedding N. Checkpoint tensor metadata was not independently downloaded or checked.

## Evaluation sample progression

training.evaluate repeatedly consumes the supplied iterator; it does not create a fresh validation iterator at each evaluation. Nonpipeline evaluation has eval_iters outer calls times gradient_accumulation_steps microbatches; pipeline evaluation delegates accumulation to eval_batch. The chosen configs have train_batch_size1024 and eval_iters10, giving a declared20971520 token-position budget per evaluation at length2048, subject to the recorded parallel-engine contract.

The iterator is created only by build_train_valid_test_data_iterators. At resume, its batch sampler starts at ((iteration*gradient_accumulation_steps)//eval_interval)*eval_iters modulo loader length. The validation dataset's requested sample count itself depends on eval_interval: (train_iters//eval_interval+1)*eval_iters*train_batch_size. Thus shared seed/path does not establish identical checkpoint evaluation samples, especially across changed intervals/restarts. Nonmonotonic loss is not grounds to discard points.

## More material issue: recorded paths do not establish held-out data

Every selected config records the same path for train_data_paths, valid_data_paths and test_data_paths: /fsx/pile/pile_20B_tokenizer_text_document, with weight1. Although split='969,30,1' also appears, the fixed data_utils.py follows the nonempty train_data_paths branch. That branch calls build_weighted_datasets and then build_the_dataset separately for train_i/valid_i/test_i. build_the_dataset supplies np.arange(0,total_num_of_documents) for every one of these datasets. The split string is used only by the alternative data_path branch.

Therefore, under the recorded paths and pinned source, validation samples are drawn from the same document pool supplied for training, with separately named/indexed ordering. The evidence does not support calling these losses held-out validation. Actual file identity/content hashes were not available, so no stronger claim of specific duplicated token positions is made; nonetheless an unrecorded disjoint split cannot be assumed. Any adapter must label the target as recorded training-pool evaluation unless new independent evidence proves disjoint data. This issue is distinct from statistical comparability of different sample counts.

Different samples from a genuinely shared held-out population can legitimately be modeled as noisy estimates, provided protocol, loss/tokenizer and sensitivity are stated. Same deterministic samples are not a universal prerequisite. Likewise these Pythia observations may support a separately declared training-pool evaluation analysis, but cannot silently substitute for a held-out-loss target. Keep N>=2e9 as the predeclared scale holdout, retain all nonmonotonic points, and report sparse design/identifiability rather than changing the split or filtering losses.
