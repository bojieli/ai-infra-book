# Vision-Braille

Research code for **"Vision-Braille: A Curriculum Learning Toolkit and Braille–Chinese Corpus for Braille Translation"**, accepted to the **EMNLP 2026 Main Conference**.

Alan Yo Wu (Cornell University), Ye Yuan (Peking University), Zhiping Xiao (UCLA), Ming Zhang (Peking University, corresponding author).

Live demo: [visionbraille.org](https://visionbraille.org) · [xinshiye.cc](https://xinshiye.cc)

## Abstract

We present Vision-Braille, the first publicly available end-to-end system for translating Chinese Braille extracted from images into written Chinese. This system addresses the unique challenges of limited annotated resources and tone omission. It integrates a robust Braille OCR pipeline with an LLM fine-tuned for sequence-to-sequence translation. We construct a synthetic Braille-Chinese corpus, including tone-omission variants that mimic authentic Braille writing habits. We fine-tune the model using a four-stage curriculum: starting with sentence-level data with full tone markers, progressing to passage-level data, then applying a tone-omission schedule of decreasing retention, and finally consolidating on passages with heavy tone omission. On passage-level translation with 10% tone retention, Curriculum-Braille achieves 83.28 BLEU using only the open-weights fine-tuned model with no reliance on any proprietary API; an optional post-hoc polishing step further improves quality but is not required for our core results.

## Artifacts

| Artifact | Location |
|---|---|
| Sentence corpus (r=100) | [`Violet-yo/Chinese-Braille-Dataset-Full-Tone`](https://huggingface.co/datasets/Violet-yo/Chinese-Braille-Dataset-Full-Tone) |
| Passage corpus (r=100) | [`Violet-yo/Passage-Chinese-Braille-Dataset-Full-Tone`](https://huggingface.co/datasets/Violet-yo/Passage-Chinese-Braille-Dataset-Full-Tone) |
| Model weights | [`Violet-yo/Vision-Braille-Qwen3-8B`](https://huggingface.co/Violet-yo/Vision-Braille-Qwen3-8B) |
| Braille OCR | [AngelinaReader](https://github.com/IlyaOvodov/AngelinaReader) (RetinaNet), see [Braille OCR](#braille-ocr) |

## Result being reproduced

| Metric | Value |
|---|---|
| Passage BLEU-4 (r=10) | **83.28** |
| chrF++ | 66.06 |
| CER | 9.94 |
| TER | 50.0 |

Test set: `stage3_passage_train_br2zh_r100_test_r10`, passage-level with 10% tone retention.
Inference with vLLM, temperature 0.95, top-p 0.7, top-k 50.

## Pipeline

### 1. Base model

Download `Qwen3-8B` and inject the Braille vocabulary (63 Braille characters), resizing the
embedding matrix accordingly:

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/Qwen/Qwen3-8B models/Qwen3-8B
cd models/Qwen3-8B && git lfs pull && cd ../..

python pre_processing/addSpecialTokens.py \
  --original_model_dir ./models/Qwen3-8B \
  --output_dir ./models/Qwen3-8B-Braille
```

In mainland China, substitute `https://hf-mirror.com/Qwen/Qwen3-8B`.

This takes the base tokenizer from 151,669 tokens to **151,732**, matching the released
checkpoint. `<BRAILLE_END>` and `<TRANSLATION_END>` are *not* added to the vocabulary, and
they do not appear in the training data either; they are a remnant of an earlier experiment
lineage. Passing `--add_end_tokens` adds them (vocab 151,734), which will **not** match the
released weights; the flag exists only to reproduce those earlier runs.

### 2. Data

See [`data/README.md`](data/README.md). Training reads LLaMA-Factory ShareGPT JSONL from
`data/cleaned_2345_v3/`, derived from the two Hugging Face corpora above by the
tone-reduction scripts in `data/`.

To regenerate the corpus from raw sources instead, `get_raw_dataset/get_raw_sentence_data/README.md`
documents the full extraction pipeline: Leipzig Corpora download, slicing, Braille
conversion, and JSON packaging.

### 3. Training

Four stages, each resuming from the previous checkpoint, with the cosine schedule reset at
every stage and sub-stage. Paper stage names map to the config directories as follows:

| Paper | Config | Data | Tones | Epochs |
|---|---|---|---|---|
| S1 Foundation | `train_config/stage1_sentence/` | sentence | r=100 | 1 |
| S2 Long-range | `train_config/stage2_passage/` | passage | r=100 | 1 |
| S3 Tone curriculum | `train_config/stage3_curriculum/` | passage | r=100 → r=10, 10 sub-stages | 1 each |
| S4 Consolidation | `train_config/stage4_consolidation/` | passage | r=10 | 3 |

```bash
# S1
FORCE_TORCHRUN=1 llamafactory-cli train train_config/stage1_sentence/train_sentence.yaml

# S2 — set model_name_or_path to the S1 checkpoint first
FORCE_TORCHRUN=1 llamafactory-cli train train_config/stage2_passage/train_passage_100pc.yaml

# S3 — chains all ten sub-stages, r100 down to r10
bash train_config/stage3_curriculum/run_curriculum.sh saves/Qwen3-8B-Braille/stage2_passage

# S4 — set model_name_or_path to the final S3 (r10) checkpoint first
FORCE_TORCHRUN=1 llamafactory-cli train train_config/stage4_consolidation/train_passage_10pc.yaml
```

The YAMLs contain `checkpoint-XXXX` placeholders where a stage resumes from the previous
one. Each stage saves once per epoch, so there is one checkpoint per epoch to choose from.

### 4. Evaluation

```bash
FORCE_TORCHRUN=1 llamafactory-cli train train_config/testing/test_passage.yaml

python evaluation/eval_bleu_predict.py results/stage4_consolidation/passage_test/generated_predictions.jsonl
python evaluation/eval_translation_metrics.py results/stage4_consolidation/passage_test/generated_predictions.jsonl
```

`eval_bleu_predict.py` computes character-level BLEU-4 and ROUGE-1/2/L.
`eval_translation_metrics.py` computes chrF++, CER, and TER, and merges them into
`predictions_score.json`. `eval_bleu_model_comparison.py` runs the one-way ANOVA with
effect size used for the cross-model comparison.

## Braille OCR

The OCR front end is RetinaNet with a Feature Pyramid Network backbone, as described in the
paper. We use [AngelinaReader](https://github.com/IlyaOvodov/AngelinaReader) rather than
redistributing a fork. Character-level error is below 1% on clean single-sided pages and
rises to roughly 15% when dots from the reverse side of the sheet interfere.

## Hardware

Training used 8 × NVIDIA H20 with DeepSpeed ZeRO-3 and bf16. Learning rate 1e-4, cosine
schedule with 5% warmup, maximum sequence length 2048.

## Repository layout

```
.
├── data/                    Tone-reduction scripts; corpora live on Hugging Face
├── evaluation/              BLEU-4, ROUGE, chrF++, CER, TER, ANOVA
├── get_raw_dataset/         Raw-corpus download and Braille-conversion pipeline
├── pre_processing/          Braille special-token injection for the base model
├── train_config/
│   ├── deepspeed/           ZeRO-2 and ZeRO-3 configs
│   ├── stage1_sentence/     S1 Foundation
│   ├── stage2_passage/      S2 Long-range
│   ├── stage3_curriculum/   S3 Tone curriculum (template + runner)
│   ├── stage4_consolidation/  S4 Consolidation
│   └── testing/             Passage test config
├── LICENSE                  MIT, covers the code
└── LICENSE-DATA             CC BY-NC-SA 4.0, covers the corpora and model weights
```

## License

Code is MIT. The Braille–Chinese corpora and the released model weights are
CC BY-NC-SA 4.0, for non-commercial research use, matching the ethics statement in the
paper. Source corpora remain the property of their original owners; the sentence-level
Chinese text comes from the Leipzig Corpora Collection and the passage-level text from
publicly available Braille books on The Braille Online Platform of China.

## Citation

```bibtex
@inproceedings{wu2026visionbraille,
  title     = {Vision-Braille: A Curriculum Learning Toolkit and Braille--Chinese Corpus for Braille Translation},
  author    = {Wu, Alan Yo and Yuan, Ye and Xiao, Zhiping and Zhang, Ming},
  booktitle = {Proceedings of the 2026 Conference on Empirical Methods in Natural Language Processing},
  year      = {2026}
}
```
