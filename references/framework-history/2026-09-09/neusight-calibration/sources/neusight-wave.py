
import torch
import torch.nn as nn
from .model import ModelBase
import pickle
from .meta import MetaTable

class MLPBlock(nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dim, num_layers, act, dropout_rate):
        super().__init__()

        self.dropout = nn.Dropout(p=dropout_rate)

        assert(num_layers >= 2)

        self.layers = nn.ModuleList()

        self.act = act

        self.layers.append(nn.Linear(input_dim, hidden_dim))
        self.layers.append(self.act)
        self.layers.append(self.dropout)

        for idx in range(num_layers-2):
            self.layers.append(nn.Linear(hidden_dim, hidden_dim))
            self.layers.append(self.act)
            self.layers.append(self.dropout)

        self.layers.append(nn.Linear(hidden_dim, output_dim)) # no activation on output

    def forward(self, x):
        for layer in self.layers:
            x = layer(x)

        return x

class MLPWave(ModelBase):
    def __init__(self, config, tag, device,num_tile_inputs):
        super().__init__(config,tag=tag,device=device) # name and feature

        self.lr = self.config["lr"]
        self.train_batch = int(self.config["train_batch"])
        self.val_batch = int(self.config["val_batch"])
        self.loss = self.config["loss"]

        self.f2i_dict = dict(zip(self.features, range(len(self.features))))

        # for amd gpus
        if "SingleFLOPsMM" in config["features"]:
            self.singleflops_feature_name = "SingleFLOPsMM"
        elif "SingleFLOPsVEC" in config["features"]:
            self.singleflops_feature_name = "SingleFLOPsVEC"
        else:
            self.singleflops_feature_name = "SingleFLOPs"

        bw_features = [self.singleflops_feature_name,"Dev_Mem","Mem_Bw","L2Cache"]

        self.bw_features = self.f2i(bw_features)

        self.sigmoid = nn.Sigmoid()
        self.leakyrelu = nn.LeakyReLU()
        self.relu = nn.ReLU()
        self.tanh = nn.Tanh()
        self.prelu = nn.PReLU()
        self.gelu = nn.GELU()

        self.softplusp1 = nn.Softplus(beta=.1)
        self.softplus = nn.Softplus(beta=1)
        self.softplus10 = nn.Softplus(beta=10)
        self.softplus100 = nn.Softplus(beta=100)
        self.softplus1000 = nn.Softplus(beta=1000)

        act_dict = {
            "sigmoid" : self.sigmoid,
            "leakyrelu" : self.leakyrelu,
            "relu" : self.relu,
            "tanh" : self.tanh,
            "prelu" : self.prelu,
            "gelu" : self.gelu,
        }

        self.arch = config["arch"]

        if self.arch == "MLP":
            self.layer_size = config["hidden_size"]
            self.num_layers = config["num_layers"]
            self.act = config["act"]
            self.act = act_dict[self.act]
            self.dropout_rate = config["dropout_rate"]
            num_input = len(self.bw_features)
            # self.bw_utilization_net = MLPBlock(input_dim=num_input+num_tile_inputs+1, output_dim=3, hidden_dim=self.layer_size, num_layers=self.num_layers, act=self.act, dropout_rate=self.dropout_rate)
            # self.bw_utilization_net = MLPBlock(input_dim=num_input+1, output_dim=3, hidden_dim=self.layer_size, num_layers=self.num_layers, act=self.act, dropout_rate=self.dropout_rate)
            self.bw_utilization_net = MLPBlock(input_dim=num_input, output_dim=3, hidden_dim=self.layer_size, num_layers=self.num_layers, act=self.act, dropout_rate=self.dropout_rate)
        else:
            assert(0)

        self.record = False

        self.record_entries = []

        self.bus_m = []
        self.bus_s = []
        self.bias_m = []

        self.alpha_m = []
        self.alpha_s = []
        self.beta_m = []
        self.beta_s = []
        self.gamma_m = []
        self.gamma_s = []

        self.tpw_ape_list = []

        self.eval_ = False

        self.bias = torch.nn.Parameter(torch.ones(1) * 1e-5)

        # self.coeff = torch.Tensor([[1,-1,1,-1]]).to(device)

    def set_meta_table(self, table_name):
        self.meta_table = MetaTable(table_name, self.features)

    def get_feature(self, x, features):
        features_idx = self.f2i(features)
        x = x[:,features_idx]
        x = x.view(-1, len(features_idx))
        x = x
        return x

    def stats(self):
        bus_m = sum(self.bus_m) / len(self.bus_m)
        bus_s = sum(self.bus_s) / len(self.bus_s)

        alpha_m = sum(self.alpha_m) / len(self.alpha_m)
        alpha_s = sum(self.alpha_s) / len(self.alpha_s)
        beta_m = sum(self.beta_m) / len(self.beta_m)
        beta_s = sum(self.beta_s) / len(self.beta_s)
        gamma_m = sum(self.gamma_m) / len(self.gamma_m)
        gamma_s = sum(self.gamma_s) / len(self.gamma_s)

        bias_m = sum(self.bias_m) / len(self.bias_m)
        
        entry = {
            "BW Util Mean" : bus_m,
            "BW Util STD" : bus_s,
            "alpha" : alpha_m,
            "alpha std" : alpha_s,
            "beta" : beta_m,
            "beta std" : beta_s,
            "gamma" : gamma_m,
            "gamma std" : gamma_s,
            "bias" : bias_m,
        }

        # clear
        self.bus_m = []
        self.bus_s = []
        self.alpha_m = []
        self.alpha_s = []
        self.beta_m = []
        self.beta_s = []
        self.gamma_m = []
        self.gamma_s = []
        self.bias_m = []

        return entry

    def f2i(self, feature):
        if isinstance(feature, list):
            return list(map(lambda x: self.f2i_dict[x], feature))
        else:
            return [self.f2i_dict[feature]]
    
    def set_record(self, set):
        self.record = set
    
    def dump(self, dataset_name, dump_path):
        assert(self.record == True)
        file_name = dump_path
        file_name.parent.mkdir(parents=True, exist_ok=True)
        print(f"dumping pkl : {file_name}")

        with open(file_name, 'wb') as handle:
            pickle.dump(self.record_entries, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def compute_loss(self, criterion, pred, label):
        self.last_label = label
        return criterion(pred / self.last_num_wave, label / self.last_num_wave)

    def ceil_multiple(self, x, y):
        # round x to the cloest multiple of y
        return torch.ceil(x/y)*y

    def compute_eff_bw(self, x, tiles, num_wave, opname):

        # features
        dev_flops = self.get_feature(x, self.singleflops_feature_name) # in GFLOPS
        mem_bw = self.get_feature(x, "Mem_Bw") # in GB/s
        dev_mem = self.get_feature(x, "Dev_Mem") # in GB
        l2cache = self.get_feature(x, "L2Cache") # in MB

        # roofline bw
        op_arithinten = self.comptue_op_arithinten(x=x, opname=opname, tiles=tiles)
        roofline_bw = torch.min(dev_flops, op_arithinten * mem_bw)

        # input dims
        
        # "SingleFLOPs" (TFLOPS), "Mem_Bw" (GB/s), "Dev_Mem" (MB), "L2Cache" (KB), dev_arith]
        # tile_mem in MB and time_ops in GFLOPs
        # These units make the inputs similar in overall scale
        num_sm = self.get_feature(x, "Num_Sm")
        norm_bw_vec = torch.cat([dev_flops/1000/num_sm, mem_bw/num_sm, dev_mem*1024/num_sm, l2cache*1024/num_sm], dim=1)

        bw_util, alpha, beta, gamma = self.compute_bw_util(norm_bw_vec=norm_bw_vec, tiles=tiles, num_wave=num_wave, bw_utilization_net=self.bw_utilization_net, opname=opname, x=x)

        # ebw
        ebw = roofline_bw * bw_util
        self.last_bw_util = bw_util

        self.last_roofline_bw = roofline_bw
        self.roofline_bw = roofline_bw
        
        # stats
        if len(bw_util) > 1:
            self.bus_m.append(torch.mean(bw_util.squeeze()).item())
            self.bus_s.append(torch.std(bw_util.squeeze()).item())

        if len(alpha) > 1:
            self.alpha_m.append(torch.mean(alpha.squeeze()).item())
            self.alpha_s.append(torch.std(alpha.squeeze()).item())
        if len(beta) > 1:
            self.beta_m.append(torch.mean(beta.squeeze()).item())
            self.beta_s.append(torch.std(beta.squeeze()).item())
        if len(gamma) > 1:
            self.gamma_m.append(torch.mean(gamma.squeeze()).item())
            self.gamma_s.append(torch.std(gamma.squeeze()).item())

        self.bias_m.append(torch.mean(self.bias.squeeze()).item())

        return ebw

    def compute_bw_util(self, x, norm_bw_vec, tiles, num_wave, bw_utilization_net, opname):
        
        tile_ops = self.compute_tile_ops(x=x, tiles=tiles, opname=opname)
        tile_mem = self.compute_tile_mem(x=x, tiles=tiles, opname=opname)
        
        # "SingleFLOPs" (TFLOPS), "Mem_Bw" (GB/s), "Dev_Mem" (MB), "L2Cache" (KB), ArithInten (SingleFLOPs / Mem_Bw)]
        # bw_in = torch.cat([tile_ops, tile_mem, num_wave * tile_mem, num_wave * tile_mem, tile_ops/tile_mem], dim=1) / norm_bw_vec
        bw_in = torch.cat([tile_ops, tile_mem, num_wave * tile_mem, num_wave * tile_mem], dim=1) / norm_bw_vec
        bw_in = torch.log2(bw_in)

        bw_util_net_out = bw_utilization_net(bw_in)
        alpha = bw_util_net_out[:,0].unsqueeze(-1)
        beta = bw_util_net_out[:,1].unsqueeze(-1)
        gamma = bw_util_net_out[:,2].unsqueeze(-1)

        alpha = self.sigmoid(alpha)
        gamma = self.sigmoid(gamma)
        bw_util = gamma - alpha / num_wave

        self.last_alpha = alpha
        self.last_beta = beta
        self.last_gamma = gamma
        self.bw_in = bw_in

        return bw_util, alpha, beta, gamma
    
    def comptue_op_arithinten(self, x, opname, tiles):
        raise NotImplemented

    def compute_ops_per_wave(self, x, tiles, opname):
        raise NotImplemented

    def compute_num_block(self, x, tiles):
        raise NotImplemented
    
    def get_tiles(self, x, tiles, culib, opname):
        raise NotImplemented
    
    def compute_tile_arithinten(self, opname, tiles):
        raise NotImplemented

    def compute_tile_ops(self, x, opname, tiles):
        raise NotImplemented

    def compute_tile_mem(self, opname, tiles):
        raise NotImplemented

    def compute_wave_time(self, opname, x, tiles):
        # input dims
        num_sm = self.get_feature(x, "Num_Sm")

        # wave quantization
        num_block = self.compute_num_block(x, tiles)

        # wave quantization
        num_wave = torch.ceil(num_block / num_sm)

        # detach for training
        num_wave_detached = num_wave.detach() # use predicted ones

        ebw = self.compute_eff_bw(x=x, tiles=tiles, num_wave=num_wave_detached, opname=opname)

        ops_per_wave = self.compute_ops_per_wave(x=x, tiles=tiles, opname=opname)

        # time per wave
        time_per_wave = ops_per_wave / ebw

        # stats
        self.last_x = x
        self.last_num_wave = num_wave_detached
        self.last_time_per_wave = time_per_wave
        self.last_num_block = num_block

        return num_wave, time_per_wave

    def forward(self, opname, x, tiles=None, device=None, culib=None, label=None):
        tiles = self.get_tiles(x=x, tiles=tiles, culib=culib,opname=opname)

        # compute wave nums
        num_wave, time_per_wave = self.compute_wave_time(opname=opname, x=x, tiles=tiles)

        # prediction
        time = num_wave * time_per_wave
        # time += self.bias

        # stats
        self.last_pred = time

        # record for test pickle
        if self.record:
            entry = {
                "f2i" : self.f2i_dict,
                "input" : x.cpu().squeeze(),
                "pred" : self.last_pred.item(),
                "Latency" : label.item(),
                "opname" : opname[0],
                "bw_util" : self.last_bw_util.cpu().squeeze(),
            }
            self.record_entries.append(entry)

        return time
    