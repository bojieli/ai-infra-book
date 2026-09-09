---
license: cc-by-nc-sa-4.0
language:
- zh
base_model: Qwen/Qwen3-8B
pipeline_tag: translation
library_name: transformers
tags:
- braille
- chinese-braille
- 盲文
- 国家通用盲文方案
- GF-0019-2018
- accessibility
- curriculum-learning
- qwen3
datasets:
- Violet-yo/Chinese-Braille-Dataset-Full-Tone
- Violet-yo/Passage-Chinese-Braille-Dataset-Full-Tone
---

# Vision-Braille-Qwen3-8B

<p align="center">
  📃 <a href="https://github.com/AlanYWu/VisionBraille" target="_blank">[Paper]</a> •
  💻 <a href="https://github.com/AlanYWu/VisionBraille" target="_blank">[Code]</a> •
  📖 <a href="https://huggingface.co/datasets/Violet-yo/Chinese-Braille-Dataset-Full-Tone" target="_blank">[Sentence corpus]</a> •
  📖 <a href="https://huggingface.co/datasets/Violet-yo/Passage-Chinese-Braille-Dataset-Full-Tone" target="_blank">[Passage corpus]</a> •
  🎬 <a href="https://visionbraille.org" target="_blank">[Demo]</a>
</p>

Chinese Braille → written Chinese translation. A full supervised fine-tune of
**Qwen3-8B** trained through the four-stage curriculum described in **"Vision-Braille: A
Curriculum Learning Toolkit and Braille–Chinese Corpus for Braille Translation"**
(EMNLP 2026 Main Conference).

This is the checkpoint behind the paper's headline number: **83.28 BLEU-4** on passage-level
translation at 10% tone retention, using open weights only, with no proprietary API.

## Results

Passage-level test set, 10% tone retention (`stage3_passage_train_br2zh_r100_test_r10`):

| Metric | Value |
|---|---|
| BLEU-4 | **83.28** |
| chrF++ | 66.06 |
| CER | 9.94 |
| TER | 50.0 |

Decoded with vLLM at temperature 0.95, top-p 0.7, top-k 50.

## Usage

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "Violet-yo/Vision-Braille-Qwen3-8B"
tok = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, dtype="bfloat16", device_map="auto")

braille = "⠎⠕⠄⠊⠄⠐⠕⠄⠵⠖⠄⠛⠳⠆⠛⠾⠂⠙⠡⠆⠃⠔⠄⠌⠢⠆⠉⠆⠃⠊⠄⠎⠪⠆⠛⠊⠁⠓⠺⠆⠇⠳⠂⠛⠮⠄⠇⠮⠂⠝⠔⠆⠓⠢⠂⠞⠔⠁⠐⠆⠘"

messages = [
    {"role": "system", "content": "你是一个中国盲文翻译助手，请把通用盲文转换成为汉字。"},
    {"role": "user", "content": f"请把以下通用盲文转换成为汉字：\n盲文内容是:\n{braille}"},
]
prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
out = model.generate(**tok(prompt, return_tensors="pt").to(model.device),
                     max_new_tokens=1024, do_sample=True,
                     temperature=0.95, top_p=0.7, top_k=50)
print(tok.decode(out[0], skip_special_tokens=True))
```

The model replies in the form `对应的中文内容是：\n<Chinese>`. Strip that nine-character
prefix to recover the translation.

For batch evaluation, vLLM is what the paper used and is considerably faster.

## Prompt format

The system prompt fixes the direction; there are no direction tokens.

| Direction | System prompt |
|---|---|
| Braille → Chinese | `你是一个中国盲文翻译助手，请把通用盲文转换成为汉字。` |

The user turn is `请把以下通用盲文转换成为汉字：\n盲文内容是:\n{braille}` with nothing appended,
and the assistant turn opens with `对应的中文内容是：\n`.

Reproduce these strings byte for byte. Note in particular that `盲文内容是:` ends in an ASCII
colon (`:`) while the instruction and the reply prefix both use the fullwidth `：`. Every one
of the 331,381 training examples uses exactly this form, so a substitution here is off-distribution.

## Vocabulary

The tokenizer extends Qwen3-8B with the **63 Chinese Braille cells** used by GF 0019-2018,
taking it from 151,669 to **151,732** tokens; the embedding matrix is resized to match.

`<BRAILLE_END>` and `<TRANSLATION_END>` are **not** vocabulary entries, and they do not occur
in the training data either. They belong to an earlier experiment lineage and were dropped
before the runs that produced these weights, so do not put them in your prompts. If you
rebuild the base model with `pre_processing/addSpecialTokens.py`, do not pass
`--add_end_tokens`: that yields vocab 151,734 and will not match these weights.

## Training

Four stages, each resuming from the previous checkpoint, with the cosine schedule reset at
every stage and sub-stage.

| Stage | Data | Tone retention | Epochs |
|---|---|---|---|
| S1 Foundation | sentence | r = 100 | 1 |
| S2 Long-range | passage | r = 100 | 1 |
| S3 Tone curriculum | passage | r = 100 → 10, ten sub-stages | 1 each |
| S4 Consolidation | passage | r = 10 | 3 |

Tone markers are deleted independently at random at rate `1 - r/100` under a fixed seed,
rather than by hand-coding the 省写 conventions, so the model must recover tone from context.

| Hyperparameter | Value |
|---|---|
| Base model | Qwen3-8B |
| Fine-tuning | Full SFT, all parameters |
| Precision | bf16 |
| Optimizer | AdamW |
| Learning rate | 1e-4, cosine, 5% warmup |
| Max sequence length | 2048 |
| Distributed | DeepSpeed ZeRO-3 |
| Hardware | 8 × NVIDIA H20 |

Software: PyTorch 2.7.0, Transformers 4.52.4, DeepSpeed 0.16.9, vLLM 0.9.2,
LLaMA-Factory 0.9.5, CUDA 12.6.

Configs to reproduce every stage are in
[`train_config/`](https://github.com/AlanYWu/VisionBraille/tree/main/train_config).

## Limitations

**This is a research prototype, not a deployable assistive tool.** The results above are on
clean, synthetically generated Braille. Two shifts degrade it substantially:

- **Real, human-produced Braille.** Training Braille comes from a rule-based converter and
  carries none of the transcription slips, contraction choices, or layout conventions of
  Braille written by people.
- **OCR-recovered Braille.** On held-out photographed exam pages passed through the OCR
  front end, performance drops sharply and a minority of pages degenerate into repetition
  loops. Whole-page, cross-domain real-OCR input is outside what this checkpoint handles
  reliably.

Word division is a further mismatch worth knowing about: the passage stages trained on
Braille with no U+2800 word division, while the sentence stage trained on word-divided
Braille. Inputs with word division present are closer to the sentence-stage distribution.

The model inherits the risks and biases of Qwen3-8B, documented in its
[technical report](https://arxiv.org/abs/2505.09388).

## License

**CC BY-NC-SA 4.0**, for non-commercial research use, matching the corpora. The base model
Qwen3-8B carries its own license from Alibaba Cloud.

## Citation

```bibtex
@inproceedings{wu2026visionbraille,
  title     = {Vision-Braille: A Curriculum Learning Toolkit and Braille--Chinese Corpus for Braille Translation},
  author    = {Wu, Alan Yo and Yuan, Ye and Xiao, Zhiping and Zhang, Ming},
  booktitle = {Proceedings of the 2026 Conference on Empirical Methods in Natural Language Processing},
  year      = {2026}
}
```
