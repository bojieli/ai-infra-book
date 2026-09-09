def full_flops(dataset_size, hidden_size, num_heads, num_layers, seq_len=2048, vocab_size=32000, ffw_size=None):
    if ffw_size is None:
        ffw_size = 4 * hidden_size
    embeddings_flops = 2 * seq_len * vocab_size * hidden_size
    attention_kqv_proj = 2 * 3 * seq_len * hidden_size * hidden_size
    attention_kq_logits = 2 * seq_len * seq_len * hidden_size
    attention_softmax = 3* num_heads* seq_len * seq_len
    attention_softmax_q_red = 2 * seq_len * seq_len * hidden_size
    attention_final_layer = 2 * seq_len * hidden_size * hidden_size
    dense_flops = 2 * seq_len * (hidden_size * ffw_size + ffw_size * hidden_size)
    final_logits = 2 * seq_len * hidden_size * vocab_size
    total_flops = embeddings_flops + num_layers*(attention_kqv_proj + attention_kq_logits +\
         attention_softmax + attention_softmax_q_red + attention_final_layer + \
            dense_flops) + final_logits
    return total_flops*3 * dataset_size/seq_len

def params(hidden_size, num_heads, num_layers, seq_len=2048, vocab_size=32000, ffw_size=None, relative_attention=False):
    if ffw_size is None:
        ffw_size = 4 * hidden_size
    per_layer = 4*hidden_size*hidden_size # attention
    per_layer += 4*hidden_size # attention bias
    per_layer += 2 * ffw_size * hidden_size # dense
    per_layer += ffw_size + hidden_size # dense bias
    per_layer += 2 * hidden_size # layer norm
    if relative_attention:
        per_layer += hidden_size*hidden_size # relative position embeddings according to Dai et al.
    embeddings = 1 * hidden_size*vocab_size + vocab_size
    if not relative_attention:
        embeddings += seq_len*hidden_size
    N = num_layers * (per_layer) + embeddings
    return N

def simple_flops(dataset_size, hidden_size, num_heads, num_layers, seq_len=2048, vocab_size=32000, ffw_size=None, relative_attention=False):
    if ffw_size is None:
        ffw_size = 4 * hidden_size
    return 6 * params(hidden_size=hidden_size, num_heads=num_heads, num_layers=num_layers, seq_len=seq_len, vocab_size=vocab_size, ffw_size=ffw_size, relative_attention=relative_attention) * dataset_size

def get_dataset_size(flops, hidden_size, num_heads, num_layers, seq_len=2048, vocab_size=32000, ffw_size=None, relative_attention=True):
    return flops / (6 * params(hidden_size=hidden_size, num_heads=num_heads, num_layers=num_layers, seq_len=seq_len, vocab_size=vocab_size, ffw_size=ffw_size, relative_attention=relative_attention))
