
from pathlib import Path
import pandas as pd
import json
import ast
import torch
import numpy as np
import os
from ..Model.model_provider import model_provider
from ..Tracing.parse import parse_trace
from ..Tracing.trace import trace_graph
from .aggregator import aggregate_latency

ops_dict = {
    "add" : 1.,
    "addu": 1.,
    "mul" : 1.,
    "mulu": 1.,
    "pow" : 1.,
    "powu": 1.,
    "div" : 1.,
    "divu": 1.,
    "tanh": 1.,
    "ln"  : 6., # mean, var, sum, div, sqrt, acc
    "softmax" : 5.,
    "relu" : 1.,
    "gelu" : 1.,
    "MEM" : 0.,
}


def reduce_mul(myList):
    # Multiply elements one by one
    result = 1
    for x in myList:
        result = result * x
    return result

def dump_df(df, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)

class MLPredictor:
    def __init__(self, predictor_path, meta_table_path):
        config_path = predictor_path/"config.json"

        self.model = model_provider(config_path)

        if os.path.isfile(predictor_path/"model.pth"):
            self.model.load_state(load_path=predictor_path/"model.pth")

        if hasattr(self.model, "set_meta_table") and meta_table_path != "":
            self.model.set_meta_table(meta_table_path)
        
    def predict(self, opname, kernel_arguments, device_config):

        all_params = kernel_arguments
        all_params.update(device_config)

        inputs = []
        for kw in self.model.features:
            inputs.append(all_params[kw])
        inputs = torch.tensor(inputs).float()
        inputs = inputs.reshape(1, -1)

        # to device
        inputs = inputs.to(self.model.device)
        self.model = self.model.to(self.model.device)

        # predict runtime with model
        culib = "cu121"
        pred = self.model(opname=opname, x=inputs, device=all_params["Device"], culib=culib)
        pred = pred.detach().cpu()
        pred = np.maximum(pred, 0) # for habitat
        pred = float(pred.squeeze().item())

        return pred

class OperatorPredictor():
    def __init__(
        self, 
        predictor_path, 
        tile_dataset_dir,
    ):

        if str(tile_dataset_dir) == "":
            linear_tile_dataset = ""
            bmm_tile_dataset = ""
            vec_tile_dataset = ""
        else:
            linear_tile_dataset = tile_dataset_dir/"linear.csv"
            bmm_tile_dataset = tile_dataset_dir/"bmm.csv"
            vec_tile_dataset = tile_dataset_dir/"vec.csv"

        predictor_path = Path(predictor_path)

        self.linear_predictor = MLPredictor(predictor_path/"LINEAR", meta_table_path=linear_tile_dataset)
        self.bmm_predictor = MLPredictor(predictor_path/"BMM", meta_table_path=bmm_tile_dataset)
        self.vec_predictor = MLPredictor(predictor_path/"VEC", meta_table_path=vec_tile_dataset)
        self.softmax_predictor = MLPredictor(predictor_path/"SOFTMAX", meta_table_path=vec_tile_dataset)
        self.ln_predictor = MLPredictor(predictor_path/"LN", meta_table_path=vec_tile_dataset)

    def predict_phase(
                self,
                opname,
                device_config,
                input_shapes,
                output_shape,
                ops,
    ):
        latency = 0
    
        if opname == "fused":
            assert(input_shapes is not None)
            assert(output_shape is not None)

            if ops == []:
                return 0

            # find representative vec op
            rep_op = ops[-1]

            # count mem
            num_input_elem = [reduce_mul(s) for s in input_shapes]
            num_input_elem = sum(num_input_elem) 
            num_output_elem = reduce_mul(output_shape)
            # num_inter_elem = 0
            # for op in ops:
            #     opname, args = op
            #     if opname == "ln":
            #         B, H = args
            #         num_inter_elem += B*H*2

            memPerO = (num_input_elem + num_output_elem) * 4 / num_output_elem

            # count ops
            acc_ops = 0.
            for op in ops:
                opname, args = op
                opname = opname.replace("VEC", "")
                if opname == "MEM":
                    ops = 0.
                else:
                    opsPerO = ops_dict[opname]
                    ops = opsPerO * args[0] * args[1]
                acc_ops += ops
            opsPerO = acc_ops / num_output_elem

            # call predictor
            opname, args = rep_op
            if opname.startswith("VEC"):
                opname = opname.replace("VEC", "")
                B, H = args
                if "softmax" in opname.lower():
                    latency += self.softmax_predictor.predict(opname=[opname],kernel_arguments={"B":B,"H":H, "MemPerO":memPerO, "OpsPerO":opsPerO},device_config=device_config)
                    # print("last bw util", self.softmax_predictor.model.last_bw_util)
                elif "ln" in opname.lower():
                    latency += self.ln_predictor.predict(opname=[opname],kernel_arguments={"B":B,"H":H, "MemPerO":memPerO, "OpsPerO":opsPerO},device_config=device_config)
                    # print("last bw util", self.ln_predictor.model.last_bw_util)
                else:
                    latency += self.vec_predictor.predict(opname=[opname],kernel_arguments={"B":B,"H":H, "MemPerO":memPerO, "OpsPerO":opsPerO},device_config=device_config)
                    # print("last bw util", self.vec_predictor.model.last_bw_util)


            elif opname == "MEM":
                mem = (num_input_elem + num_output_elem) * 4
                latency += mem / (self.mem_bw * (2**30))
            elif opname == "misc":
                assert(0)
            else:
                raise NotImplementedError

        else:
            for op in ops:
                opname, args = op
                
                if opname == "Linear":
                    B = 1
                    M, N, K = args
                    latency += self.linear_predictor.predict(opname=["linear"],kernel_arguments={"B":B,"M":M,"N":N,"K":K},device_config=device_config)
                
                elif opname == "BMM":
                    B, M, N, K = args
                    latency += self.bmm_predictor.predict(opname=["bmm"],kernel_arguments={"B":B,"M":M,"N":N,"K":K},device_config=device_config)
                
                elif opname.startswith("VEC"):
                    assert(input_shapes is not None)
                    assert(output_shape is not None)
                    opname = opname.replace("VEC", "")
                    B, H = args
                    num_input_elem = [reduce_mul(s) for s in input_shapes]
                    num_input_elem = sum(num_input_elem) 
                    num_output_elem = reduce_mul(output_shape)
                    memPerO = (num_input_elem + num_output_elem) * 4 / num_output_elem
                    opsPerO = ops_dict[opname]

                    if "softmax" in opname.lower():
                        latency += self.softmax_predictor.predict(opname=[opname],kernel_arguments={"B":B,"H":H, "MemPerO":memPerO, "OpsPerO":opsPerO},device_config=device_config)
                    elif "ln" in opname.lower():
                        latency += self.ln_predictor.predict(opname=[opname],kernel_arguments={"B":B,"H":H, "MemPerO":memPerO, "OpsPerO":opsPerO},device_config=device_config)
                    else:
                        latency += self.vec_predictor.predict(opname=[opname],kernel_arguments={"B":B,"H":H, "MemPerO":memPerO, "OpsPerO":opsPerO},device_config=device_config)

                elif opname == "MEM":
                    mem = 0
                    for shape in args:
                        mem += reduce_mul(shape)*4
                    latency += mem / (self.mem_bw * (2**30))
                
                elif opname == "ALLREDUCE" or opname=="ALLREDUCE_ASYNC":
                    buffer_size = args[0]
                    num_gpu = 4
                    latency += (buffer_size * 4) / (self.link_bw * (2**30)) * (num_gpu - 1)
                    # latency += (buffer_size * 4) * self.bw_coeff + self.bw_bias

                elif opname == "SENDRECV":
                    buffer_size = args[0]
                    latency += (buffer_size * 4) / (self.link_bw * (2**30))
                    # latency += (buffer_size * 4) * self.bw_coeff + self.bw_bias
                
                elif opname == "misc":
                    assert(0)
                
                else:
                    print(opname)
                    raise NotImplementedError
            
        return latency


    def predict(
                self,
                device_config,
                x,
    ):

        opname = x.loc["OpName"] 
        input_shapes = x.loc["InputShapes"]
        output_shape = x.loc["OutputShape"]
        device_name = device_config['Device']

        self.mem_bw = float(device_config["Mem_Bw"]) # gb/s

        self.util = 0.72
        if device_name == "NVIDIA H100 80GB HBM3":
            self.link_bw = 900 * self.util / 2 # in GB/s
        elif device_name == "NVIDIA A100-PCIE-40GB" or device_name == "NVIDIA A100-SXM4-40GB":
            self.link_bw = 600 * self.util / 2 # in GB/s
        else:
            self.link_bw = None

        # for habitat
        if hasattr(self.vec_predictor.model, "meta_table"):
            habitat_vec_ref_device="Tesla V100-PCIE-32GB" if device_name != "Tesla V100-PCIE-32GB" else "Tesla P100-PCIE-16GB"
            self.vec_predictor.model.meta_table.set_device(habitat_vec_ref_device)
            self.ln_predictor.model.meta_table.set_device(habitat_vec_ref_device)
            self.softmax_predictor.model.meta_table.set_device(habitat_vec_ref_device)

        fw_ops = x.loc["FwOps"]
        bw_ops = x.loc["BwOps"]
        acc_ops = x.loc["AccOps"]
        
        fw_latency = self.predict_phase(device_config=device_config, input_shapes=input_shapes, output_shape=output_shape, ops=fw_ops, opname=opname)
        bw_latency = self.predict_phase(device_config=device_config, input_shapes=input_shapes, output_shape=output_shape, ops=bw_ops, opname=opname)
        acc_latency = self.predict_phase(device_config=device_config, input_shapes=input_shapes, output_shape=output_shape, ops=acc_ops, opname=opname)

        return pd.Series([fw_latency * 1000, bw_latency * 1000, acc_latency * 1000]) # sec to ms

class NeusightPredictor():
    def __init__(
        self,
        predictor_name,
        predictor_path,
        tile_dataset_dir,
    ):

        self.name = predictor_name

        if tile_dataset_dir != "":
            tile_dataset_dir = Path(tile_dataset_dir)

        self.predictor = OperatorPredictor(
                    predictor_path=predictor_path, 
                    tile_dataset_dir=tile_dataset_dir,
                )

    def predict(self, 
                device_config_path, # hardware description
                model_config_path, # model configuration
                sequence_length,
                batch_size,
                result_dir,
                model_name=None,
                execution_type="inf",
                options="", # additional options
            ):
        
        result_dir = Path(result_dir)

        is_train = (execution_type == "train")
        
        if model_name is None:
            model_name = Path(model_config_path).name.split(".")[0]

        # parse options
        fusion = False
        dp_degree = 1
        tp_degree = 1
        pp_degree = 1
        pp_num_microbatch = 1
        distributed = False
        single_layer = True

        import re

        if options == "":
            pass
        elif options == "fusion":
            fusion = True
            single_layer = False
        elif re.match(r"dp\d+", options):
            distributed = True
            dp_degree = int(options[2:])
        elif re.match(r"tp\d+", options):
            distributed = True
            tp_degree = int(options[2:])
        elif re.match(r"pp\d+_\d+", options):
            distributed = True
            pp_degree = int(options[2:].split("_")[0])
            pp_num_microbatch = int(options[2:].split("_")[1])
        else:
            assert(0)

        if "switch" in model_name or fusion:
            single_layer = False


        if fusion:
            model_tag = f"{model_name}-{execution_type}-{sequence_length}-{batch_size}-fusion"
            trace_name = result_dir/f"opgraph_raw/{model_name}-{execution_type}-{sequence_length}-{batch_size}-fusion.csv"
            parse_name = result_dir/f"opgraph/{model_name}-{execution_type}-{sequence_length}-{batch_size}-fusion.csv"
        elif distributed:
            model_tag = f"{model_name}-{execution_type}-{sequence_length}-{batch_size}-{options}"
            if dp_degree > 1:
                trace_name = result_dir/f"opgraph_raw/{model_name}-{execution_type}-{sequence_length}-{batch_size // dp_degree}.csv"
                parse_name = result_dir/f"opgraph/{model_name}-{execution_type}-{sequence_length}-{batch_size}-dp{dp_degree}.csv"
            elif tp_degree > 1:
                trace_name = result_dir/f"opgraph_raw/{model_name}-{execution_type}-{sequence_length}-{batch_size}.csv"
                parse_name = result_dir/f"opgraph/{model_name}-{execution_type}-{sequence_length}-{batch_size}-tp{tp_degree}.csv"
            elif pp_degree > 1:
                trace_name = result_dir/f"opgraph_raw/{model_name}-{execution_type}-{sequence_length}-{batch_size // pp_num_microbatch}.csv"
                parse_name = result_dir/f"opgraph/{model_name}-{execution_type}-{sequence_length}-{batch_size}-pp{pp_degree}_{pp_num_microbatch}.csv"
        else:
            model_tag = f"{model_name}-{execution_type}-{sequence_length}-{batch_size}"
            trace_name = result_dir/f"opgraph_raw/{model_tag}.csv"
            parse_name = result_dir/f"opgraph/{model_tag}.csv"

        device_config_path = Path(device_config_path)
        device_config_path = device_config_path.absolute()
        # print(device_config_path)
        with open(device_config_path, "r") as f:
            device_config = json.load(f)

        # trace raw operator graph
        print(trace_name)
        if os.path.exists(trace_name):
            print("already exists : ", os.path.realpath(trace_name))
            pass
        else:
            df, _ = trace_graph(
                                model_config_path=model_config_path, 
                                sequence_length=sequence_length, 
                                batch_size=batch_size, 
                                is_train=is_train, 
                                bench=False, 
                                single_layer=single_layer, 
                                fusion=fusion,
                                distributed=distributed,
                                dp_degree=dp_degree,
                                pp_degree=pp_degree,
                                pp_num_microbatch=pp_num_microbatch,
                                tp_degree=tp_degree,
                            )
            dump_df(df, trace_name)

        # parse operator graph
        print(parse_name)
        if os.path.exists(parse_name):
            print("already exists : ", os.path.realpath(parse_name))
            pass
        else:
            df = parse_trace(
                            trace_name, 
                            is_train=is_train, 
                            bench=False, 
                            fusion=fusion,
                            distributed=distributed,
                            dp_degree=dp_degree,
                            pp_degree=pp_degree,
                            pp_num_microbatch=pp_num_microbatch,
                            tp_degree=tp_degree,
                        )
            dump_df(df, parse_name)

        # annotate operator graph with prediction
        df = pd.read_csv(parse_name, converters={"FwOps": ast.literal_eval, "BwOps": ast.literal_eval, "AccOps": ast.literal_eval, "InputShapes": ast.literal_eval, "OutputShape": ast.literal_eval})
        df[[f"fw_latency", f"bw_latency", f"acc_latency"]] = df.apply(lambda x: self.predictor.predict(device_config, x), axis=1)
        df[f"bwall_latency"] = df[f"bw_latency"] + df[f"acc_latency"]
        df[f"e2e_latency"] = df[f"fw_latency"] + df[f"bw_latency"] + df[f"acc_latency"]

        with open(model_config_path) as f:
            config_json = json.load(f)
        if "gpt" in model_name:
            n_layer = config_json["n_layer"]
        elif "switch" in model_name:
            n_layer = config_json["num_layers"]
        else:
            n_layer = config_json["num_hidden_layers"]


        out_path = result_dir/f"prediction/{device_config['Device'].replace(' ', '_')}/{self.name}/{model_tag}.csv"
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)

        # accumulate latency
        e2e, fw, bw, bwall, acc = aggregate_latency(
                                                    df, 
                                                    model_name, 
                                                    distributed=distributed,
                                                    dp_degree=dp_degree,
                                                    pp_degree=pp_degree,
                                                    pp_num_microbatch=pp_num_microbatch,
                                                    tp_degree=tp_degree,
                                                    fusion=fusion,
                                                    n_layer=n_layer,
                                                )

        json_dict = {
            "num_layer": n_layer,
            "e2e_latency": float(e2e),
            "fw_latency": float(fw),
            "bwall_latency": float(bwall),
            "bw_latency": float(bw),
            "acc_latency": float(acc),
        }

        # Save the dictionary to a JSON file
        with open(out_path.with_suffix(".json"), 'w') as file:
            json.dump(json_dict, file, indent=4)

        print(f"E2E latency for {model_tag} on {device_config_path.name}:", round(e2e, 2), "ms")
