import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
import torch
from ..Dataset.dataset import Dataset

class MetaTable():
    def __init__(self, table_path, features, device_list=None):
        # print("loading meta table : ", features)
        self.features = features
        self.df = Dataset(table_path, device_list=device_list).get_df()
        self.device_set = None

    def set_device(self, device):
        assert(len(self.df) != 0)
        assert(device is not None)
        self.device_set = device

    def closest_point(self, point, df):

        # 'B', 'H', 'Num_Sm', 'SingleFLOPs', 'Dev_Mem', 'Mem_Bw', 'L2Cache',

        point = point.cpu().numpy()

        dist = cdist(point, df[self.features])

        topk = 1
        idx = np.argpartition(dist, topk)
        idx = idx[:,:topk]
        return df.iloc[idx.squeeze(0)]

    def get_df(self):
        return self.df

    def get_tile(self, x, culib, opname):
        # only for test
        assert(len(opname) == 1) 
        opname = opname[0]
        assert(opname not in ["ln", "softmax"])

        if opname == "fused_relu_add":
            opname = "relu"

        # df = self.df[self.df["CUDA Version"] == culib]
        df = self.df
        assert(len(df) != 0)
        df = df[df["OPName"] == opname]
        if(len(df) == 0):
            print("")
            print(opname)
            assert(0)
        found = self.closest_point(x, df)
        return torch.Tensor([found["Tile1"].item(), found["Tile2"].item()])

    def get_exact_match(self, x, culib, opname, B, H):
        if opname == "ones":
            return None, None

        df = self.df[self.df["Device"] == self.device_set]
        assert(len(df) != 0)
        
        assert(len(opname) == 1) 
        opname = opname[0]
        df = df[df["OPName"] == opname]
        assert(len(df) != 0)

        found = self.closest_point(x, df)

        if (B.item() != int(found["B"].item()) or H.item() != int(found["H"].item())): # missing
            # print("missing dimension in tile table")
            # print(opname)
            # print("query")
            # print(int(B.item()))
            # print(int(H.item()))
            # print("found")
            # print(found["B"].item())
            # print(found["H"].item())
            return None, None

        return found["Latency"].item(), found["Mem_Bw"].item()