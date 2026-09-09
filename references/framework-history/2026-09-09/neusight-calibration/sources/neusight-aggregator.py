
import pandas as pd

def replicate_layer(trace, model_name, n_layer, options=""):

    if n_layer == 0:
        return trace

    if "bert" in model_name.lower():
        start = trace['Name'].loc[lambda x: x=="bert_encoder_layer_0_attention_self_query"].index.item()
        end = trace['Name'].loc[lambda x: x=="bert_encoder_layer_0_output_layer_norm"].index.item() + 1
    elif "gpt" in model_name.lower():
        if "transformer_h_0_ln_1_grad" in trace['Name'].values:
            start = trace['Name'].loc[lambda x: x=="transformer_h_0_ln_1_grad"].index
        else:
            start = trace['Name'].loc[lambda x: x=="transformer_h_0_ln_1"].index
        start = start.item()
        end = trace['Name'].loc[lambda x: x=="add_15"].index.item() + 1
    elif "opt" in model_name.lower():
        start = trace['Name'].loc[lambda x: x=="model_decoder_layers_0_self_attn_layer_norm"].index.item()
        end = trace['Name'].loc[lambda x: x=="view_11"].index.item() + 1
    elif "switch" in model_name.lower():
        # no need to convert
        return trace
    # elif "megatron" in model_name.lower():
    #     start = trace['Name'].loc[lambda x: x=="language_model_encoder_layers_0_input_layernorm"].index.item()
    #     end = trace['Name'].loc[lambda x: x=="make_viewless_tensor_1"].index.item() + 1
    else:
        assert(0)

    prologue = trace.iloc[:start]
    layer = trace.iloc[start:end]
    epilogue = trace.iloc[end:]

    df = pd.concat([prologue, *([layer]*n_layer), epilogue])
    df = df.reset_index(drop=True)

    return df

def aggregate_gpt(trace, model_name, n_layer):
    trace = replicate_layer(trace, model_name, n_layer)
    # print(trace.columns)
    e2e = trace[f"e2e_latency"].sum(axis=0)
    fw = trace[f"fw_latency"].sum(axis=0)
    bw = trace[f"bw_latency"].sum(axis=0)
    bwall = trace[f"bwall_latency"].sum(axis=0)
    acc = trace[f"acc_latency"].sum(axis=0)

    return e2e, fw, bw, bwall, acc

def aggregate_tp(trace, model_name, tp_degree, n_layer):
    # replicate layers
    trace = replicate_layer(trace, model_name, n_layer)
    pred_e2e = trace[f"e2e_latency"].sum(axis=0)
    return pred_e2e

def aggregate_dp(trace, model_name, dp_degree, n_layer):
    # replicate layers
    trace = replicate_layer(trace, model_name, n_layer)

    # acc fw latency
    fw_e2e = trace[f"fw_latency"].sum(axis=0)

    rows = []
    for i, r in trace.iterrows():
        r = dict(r)
        r["bw_latency"] = r["bwall_latency"]
        rows.append(dict(r))
    rows = rows[::-1]

    # sum up compute latency and record communication ops
    compute_latency = 0
    comm_ops = [] # (start_time, latency)
    for r in rows:
        if r["Name"].endswith("_grad"):
            comm_ops.append((compute_latency, r["bw_latency"]))
        else:
            compute_latency += r["bw_latency"]

    # when does comm ends?
    end_time = 0
    for start_time, lat in comm_ops:
        end_time = max(end_time, start_time) + lat

    # acc fw latency
    bw_e2e = max(end_time, compute_latency)

    pred_e2e = fw_e2e + bw_e2e
    return pred_e2e

def aggregate_pp(trace, model_name, pp_degree, n_layer, num_micro_batch):

    assert(n_layer % pp_degree == 0)
    assert(num_micro_batch == 1) # only support this for now
    per_device_layer = n_layer // pp_degree

    # single layer latency
    start = trace['Name'].loc[lambda x: x=="transformer_h_0_ln_1"].index.item()
    end = trace['Name'].loc[lambda x: x=="add_15"].index.item() + 1

    begin = trace.iloc[:start]
    layer = trace.iloc[start:end]
    sendrecv = trace.iloc[end:end+1]
    end = trace.iloc[end+1:]

    begin_fw_latency = begin[f"fw_latency"].sum(axis=0)
    end_bw_latency = begin[f"bwall_latency"].sum(axis=0)

    layer_fw_latency = layer[f"fw_latency"].sum(axis=0)
    layer_bw_latency = layer[f"bwall_latency"].sum(axis=0)

    per_device_layer_fw_latency = layer_fw_latency * per_device_layer
    per_device_layer_bw_latency = layer_bw_latency * per_device_layer

    sendrecv_fw_latency = sendrecv[f"fw_latency"].sum(axis=0)
    sendrecv_bw_latency = sendrecv[f"bwall_latency"].sum(axis=0)

    end_fw_latency = end[f"fw_latency"].sum(axis=0)
    begin_bw_latency = end[f"bwall_latency"].sum(axis=0)

    pred_e2e = 0

    # # move to the last rank device
    # pred_e2e += begin_fw_latency + (per_device_layer_fw_latency + sendrecv_fw_latency*2)*(pp_degree-1)

    # # remaining fw and bw on the last rank device
    # pred_e2e += (per_device_layer_fw_latency + end_fw_latency)*(num_micro_batch) # last rank device does not need to send
    # pred_e2e += (begin_bw_latency + per_device_layer_bw_latency)*(num_micro_batch) # last rank device does not need to send
    # pred_e2e += sendrecv_bw_latency*2 # send to the next device

    # # move to the first rank device
    # pred_e2e += (per_device_layer_bw_latency + sendrecv_bw_latency*2)*(pp_degree-1)
    # pred_e2e -= sendrecv_bw_latency*2 # last bw layer does not need to send
    # pred_e2e += end_bw_latency

    # move to the last rank device
    print(per_device_layer_fw_latency, sendrecv_fw_latency, per_device_layer_bw_latency, sendrecv_bw_latency, sep=", ")
    print(begin_fw_latency, begin_bw_latency, end_fw_latency, end_bw_latency, sep=", ")

    pred_e2e = \
                begin_fw_latency \
              + (per_device_layer_fw_latency + sendrecv_fw_latency*2)*(pp_degree - 1) \
              + (per_device_layer_fw_latency + end_fw_latency + sendrecv_fw_latency)*(num_micro_batch) \
              + (per_device_layer_bw_latency + begin_bw_latency + sendrecv_bw_latency)*(num_micro_batch) \
              + (per_device_layer_bw_latency + sendrecv_bw_latency)*(pp_degree - 1) \
              + end_bw_latency \
        # + end_fw_latency*(num_micro_batch) \
        # + begin_bw_latency*(num_micro_batch) \

    return pred_e2e

def aggregate_latency(
        df, 
        model_name, 
        distributed,
        dp_degree,
        pp_degree,
        pp_num_microbatch,
        tp_degree,
        fusion,
        n_layer,
):

    fw = 0
    bw = 0
    bwall = 0
    acc = 0

    if distributed:
        if dp_degree > 1:
            e2e = aggregate_dp(df, model_name, dp_degree, n_layer)
        elif tp_degree > 1:
            e2e = aggregate_tp(df, model_name, tp_degree, n_layer)
        elif pp_degree > 1:
            e2e = aggregate_pp(df, model_name, pp_degree, n_layer, pp_num_microbatch)
    elif fusion:
        e2e, fw, bw, bwall, acc = aggregate_gpt(df, model_name, 0)
    else:
        e2e, fw, bw, bwall, acc = aggregate_gpt(df, model_name, n_layer)

    return e2e, fw, bw, bwall, acc