
import torch
from .mlp_wave import MLPWave

class MLPWaveMM(MLPWave):
    def __init__(self, config, tag, device):
        num_tile_inputs = 2
        super().__init__(config,tag=tag,device=device,num_tile_inputs=num_tile_inputs) # name and feature

    def comptue_op_arithinten(self, x, opname, tiles):
        m = self.get_feature(x, "M")
        n = self.get_feature(x, "N")
        k = self.get_feature(x, "K")

        tm = tiles[:,0].unsqueeze(-1)
        tk = tiles[:,2].unsqueeze(-1)

        # op arithinten
        op_flops = 2.0 * (self.ceil_multiple(m,tm) * n * self.ceil_multiple(k,tk)) / (10**9)  
        op_mem = 4.0 * (m * n + n * k + m * k) / (2**30)
        op_arithinten  = op_flops / op_mem

        return op_arithinten

    def compute_ops_per_wave(self, x, tiles, opname):
        num_sm = self.get_feature(x, "Num_Sm")

        tile_m_dim = tiles[:,0].unsqueeze(-1)
        tile_n_dim = tiles[:,1].unsqueeze(-1)
        tile_k_dim = tiles[:,2].unsqueeze(-1)

        ops_per_sm = 2.0 * (tile_m_dim * tile_n_dim * tile_k_dim / (10**9))
        ops_per_wave = ops_per_sm * num_sm
        return ops_per_wave

    def compute_num_block(self, x, tiles):

        tile_m_dim = tiles[:,0].unsqueeze(-1)
        tile_k_dim = tiles[:,2].unsqueeze(-1)

        nb_m = torch.ceil(self.get_feature(x, "M") / tile_m_dim)
        nb_k = torch.ceil(self.get_feature(x, "K") / tile_k_dim)

        b = self.get_feature(x, "B")

        num_block = b * nb_m * nb_k
        return num_block
    
    def get_tiles(self, x, tiles, culib, opname):
        if tiles is None:
            tiles = self.meta_table.get_tile(x, culib, opname)
            tiles = tiles.to(self.device)
        tiles = tiles.view(-1,2)

        tm = tiles[:,1].unsqueeze(-1) # tile y
        tn = self.get_feature(x, "N")
        tk = tiles[:,0].unsqueeze(-1) # tile x

        tiles = torch.cat([tm, tn, tk], dim=1)
        
        self.last_tiles = tiles

        return tiles

    def compute_tile_ops(self, x, opname, tiles):
        tm = tiles[:,0].unsqueeze(-1)
        tn = tiles[:,1].unsqueeze(-1)
        tk = tiles[:,2].unsqueeze(-1)

        # op arithinten
        tile_flops = 2.0 * (tm * tn * tk) / (10**9)  # in GFLOPS

        return tile_flops

    def compute_tile_mem(self, x, opname, tiles):
        tm = tiles[:,0].unsqueeze(-1)
        tn = tiles[:,1].unsqueeze(-1)
        tk = tiles[:,2].unsqueeze(-1)

        tile_mem = 4.0 * (tm * tn + tn * tk + tm * tk) / (2**20) # in MB

        return tile_mem