---
library_name: transformers
license: apache-2.0
datasets:
- attn-signs/kolmogorov-3
- attn-signs/russian-code
language:
- ru
base_model:
- Qwen/Qwen3-8B
---

# Qwen3-8B-ru

- [EN]  
Qwen3-based model, adapted for russian text generation tasks.  
- [RU]  
Finetune версия Qwen3, адаптированная для генерации русского текста.  

## Model Details / Детализация модели
- [EN]  
LoRA supervised finetuning was performed on 2xA100 NVIDIA GPUs for 12h for 1 epoch on datasets:  
attn-signs/kolmogorov-3;  
attn-signs/russian-code;

- [RU]  
LoRA SFT цикл был выполнен на двух NVIDIA A100, обучение длилось около 12 часов.  
Прогон полной эпохи датасетов:  
attn-signs/kolmogorov-3;  
attn-signs/russian-code;


### Model Description / Описание модели

- **Developed by:** [Reisen Raumberg (Attention Signs team)]
- **Language(s) (NLP):** [RU/EN]
- **Finetuned from model:** [Qwen3]

Utilized DeepSpeed (Stage 3), HF.Accelerator for distributed training and fused AdamW.  
**GPU hours**: 12h of NVIDIA A100

Для обучения использовались HuggingFace Accelerator с Microsoft DeepSpeed (Stage 3) для распределения параметров и стейта оптимизатора, а так же зафьюженный AdamW  
**GPU часы**: 12 часов NVIDIA A100

### Model Config / Конфигурация обучения
```toml
[model]
model_name_or_path = "Qwen/Qwen3-8B"

[datasets]
dataset = [
    'attn-signs/kolmogorov-3',
    'attn-signs/russian-code',
]
dataset_ratio = [
    1,
    1
]
test_size = 0.05
conversation_field = "conversation"
generate_eval_examples = false
evaluation_strategy = "steps"
eval_steps = 500
dataloader_num_workers = 2
remove_unused_columns = true

[run]
save_strategy = "steps"
save_steps = 500
save_total_limit = 3
run_name = "sft-qwen3-8b"
report_to = "wandb"
logging_first_step = true
logging_steps = 1
output_dir = "models/attn-signs-qwen3-8b"
project_name = "sft-qwen3"

[training]
train_only_on_completions = true
per_device_train_batch_size = 1
per_device_eval_batch_size = 1
num_train_epochs = 1
learning_rate = 0.00004
gradient_accumulation_steps = 8
gradient_checkpointing = true
warmup_steps = 10
bf16 = true
seed = 42
use_peft = true
max_length = 4096

[fusion]
use_liger = true
attn_implementation = "flash_attention_2"

[lora]
lora_target_modules = [
    "k_proj",
    "v_proj",
    "q_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]
lora_r = 512
lora_alpha = 512

[tokenizer]
assistant_message_template = "<|im_start|>assistant"
pad_token = "<|endoftext|>"
eos_token = "<|im_end|>"
chat_template = "{%- if tools %}\n    {{- '<|im_start|>system\\n' }}\n    {%- if messages[0].role == 'system' %}\n        {{- messages[0].content + '\\n\\n' }}\n    {%- endif %}\n    {{- \"# Tools\\n\\nYou may call one or more functions to assist with the user query.\\n\\nYou are provided with function signatures within <tools></tools> XML tags:\\n<tools>\" }}\n    {%- for tool in tools %}\n        {{- \"\\n\" }}\n        {{- tool | tojson }}\n    {%- endfor %}\n    {{- \"\\n</tools>\\n\\nFor each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:\\n<tool_call>\\n{\\\"name\\\": <function-name>, \\\"arguments\\\": <args-json-object>}\\n</tool_call><|im_end|>\\n\" }}\n{%- else %}\n    {%- if messages[0].role == 'system' %}\n        {{- '<|im_start|>system\\n' + messages[0].content + '<|im_end|>\\n' }}\n    {%- endif %}\n{%- endif %}\n{%- set ns = namespace(multi_step_tool=true, last_query_index=messages|length - 1) %}\n{%- for message in messages[::-1] %}\n    {%- set index = (messages|length - 1) - loop.index0 %}\n    {%- if ns.multi_step_tool and message.role == \"user\" and not(message.content.startswith('<tool_response>') and message.content.endswith('</tool_response>')) %}\n        {%- set ns.multi_step_tool = false %}\n        {%- set ns.last_query_index = index %}\n    {%- endif %}\n{%- endfor %}\n{%- for message in messages %}\n    {%- if (message.role == \"user\") or (message.role == \"system\" and not loop.first) %}\n        {{- '<|im_start|>' + message.role + '\\n' + message.content + '<|im_end|>' + '\\n' }}\n    {%- elif message.role == \"assistant\" %}\n        {%- set content = message.content %}\n        {%- set reasoning_content = '' %}\n        {%- if message.reasoning_content is defined and message.reasoning_content is not none %}\n            {%- set reasoning_content = message.reasoning_content %}\n        {%- else %}\n            {%- if '</think>' in message.content %}\n                {%- set content = message.content.split('</think>')[-1].lstrip('\\n') %}\n                {%- set reasoning_content = message.content.split('</think>')[0].rstrip('\\n').split('<think>')[-1].lstrip('\\n') %}\n            {%- endif %}\n        {%- endif %}\n        {%- if loop.index0 > ns.last_query_index %}\n            {%- if loop.last or (not loop.last and reasoning_content) %}\n                {{- '<|im_start|>' + message.role + '\\n<think>\\n' + reasoning_content.strip('\\n') + '\\n</think>\\n\\n' + content.lstrip('\\n') }}\n            {%- else %}\n                {{- '<|im_start|>' + message.role + '\\n' + content }}\n            {%- endif %}\n        {%- else %}\n            {{- '<|im_start|>' + message.role + '\\n' + content }}\n        {%- endif %}\n        {%- if message.tool_calls %}\n            {%- for tool_call in message.tool_calls %}\n                {%- if (loop.first and content) or (not loop.first) %}\n                    {{- '\\n' }}\n                {%- endif %}\n                {%- if tool_call.function %}\n                    {%- set tool_call = tool_call.function %}\n                {%- endif %}\n                {{- '<tool_call>\\n{\"name\": \"' }}\n                {{- tool_call.name }}\n                {{- '\", \"arguments\": ' }}\n                {%- if tool_call.arguments is string %}\n                    {{- tool_call.arguments }}\n                {%- else %}\n                    {{- tool_call.arguments | tojson }}\n                {%- endif %}\n                {{- '}\\n</tool_call>' }}\n            {%- endfor %}\n        {%- endif %}\n        {{- '<|im_end|>\\n' }}\n    {%- elif message.role == \"tool\" %}\n        {%- if loop.first or (messages[loop.index0 - 1].role != \"tool\") %}\n            {{- '<|im_start|>user' }}\n        {%- endif %}\n        {{- '\\n<tool_response>\\n' }}\n        {{- message.content }}\n        {{- '\\n</tool_response>' }}\n        {%- if loop.last or (messages[loop.index0 + 1].role != \"tool\") %}\n            {{- '<|im_end|>\\n' }}\n        {%- endif %}\n    {%- endif %}\n{%- endfor %}\n{%- if add_generation_prompt %}\n    {{- '<|im_start|>assistant\\n' }}\n    {%- if enable_thinking is defined and enable_thinking is false %}\n        {{- '<think>\\n\\n</think>\\n\\n' }}\n    {%- endif %}\n{%- endif %}"
```

### Usage / Использование модели
```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "attn-signs/Qwen3-8B-ru"

# load the tokenizer and the model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)

# prepare the model input
prompt = "Give me a short introduction to large language model."
messages = [
    {"role": "user", "content": prompt}
]
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=True # Switches between thinking and non-thinking modes. Default is True.
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

# conduct text completion
generated_ids = model.generate(
    **model_inputs,
    max_new_tokens=32768
)
output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist() 

# parsing thinking content
try:
    # rindex finding 151668 (</think>)
    index = len(output_ids) - output_ids[::-1].index(151668)
except ValueError:
    index = 0

thinking_content = tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip("\n")
content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")

print("thinking content:", thinking_content)
print("content:", content)
```