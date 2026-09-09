import torch
from torch import nn
import torch.distributed
from torch.optim import Adam
from transformers import GPT2Config, GPT2LMHeadModel
from tqdm import tqdm
import os
from galvatron.utils import set_seed, distributed_dataloader, print_loss
from galvatron.core import initialize_galvatron, GalvatronProfiler
from galvatron.models.gpt_hf.GPTModel_hybrid_parallel import get_hybrid_parallel_configs, construct_hybrid_parallel_model
from galvatron.models.gpt_hf.dataloader import DataLoaderForGPT
from galvatron.models.gpt_hf.meta_configs import config_from_meta, set_model_config, model_name, model_layer_configs
from galvatron.models.gpt_hf.arguments import model_args
from galvatron.core.initialize import init_empty_weights
from megatron.arguments import _print_args
from galvatron.flexsp_solver import flexSPCostModel, flexSPOptimizer
optimizer_param_dict = {
    'gpt-7b' :{
        'act_per_token' : 4.480441895,
         'cpt_alpha1' : 5.128 * 1e-6,
         'cpt_alpha2' : 183.9576 * 1e-3,
         'cpt_beta1' : 629.3563,
         'hidden_size': 4096,
         'layer_num': 32,
         'param_size_B': {4: 6.51, 192: 7.1174468994140625, 384: 7.8498687744140625},
    },
    'gpt-13b' : {
        'act_per_token': 4.220439453,
         'cpt_alpha1' : 9.2852 * 1e-6,
         'cpt_alpha2' : 306.0189 * 1e-3,
         'cpt_beta1' : 1132.5632,
         'hidden_size': 5120,
         'layer_num': 40,
         'param_size_B': {4: 12.3568, 192: 13.11605453491211, 384: 14.03158187866211},
    },
    'gpt-30b' : {
        'act_per_token' : 3.417381836,
         'cpt_alpha1' : 15.4262 * 1e-6,
         'cpt_alpha2' : 803.5742 * 1e-3,
         'cpt_beta1' : 2789.3644,
         'hidden_size': 6656,
         'layer_num': 60,
         'param_size_B': {4: 30.538, 192: 31.52513885498047, 384: 32.71532440185547},
    }
}
def train(args):
    local_rank = args.local_rank
    rank = torch.distributed.get_rank()
    torch.cuda.set_device(local_rank)
    device = torch.device("cuda", local_rank)
    world_size = torch.distributed.get_world_size()
    max_len = args.seq_length
    config = config_from_meta(args.model_size)
    config = set_model_config(config, args, False)
    config.max_position_embeddings = max_len
    args.seq_length = max_len
    if local_rank == 0:
        print(config)
        _print_args("arguments", args)
    
    hybrid_parallel_configs = get_hybrid_parallel_configs(model_config=config, training_args=args)
    if local_rank == 0:
        print("Creating Model...")
    if args.initialize_on_meta:
        with init_empty_weights(True):
            gpt_model = GPT2LMHeadModel(config)
    else:
        gpt_model = GPT2LMHeadModel(config)
    
    param_size_B = sum(p.numel() for p in gpt_model.parameters()) / 1024**3
    if rank == 0:
        print(param_size_B)
    memory_limit_gb = torch.cuda.get_device_properties(torch.cuda.current_device()).total_memory / (1024**3)
    if args.use_packing:
        assert args.use_flash_attn, "packing is only supported by flash attention"
    if args.use_flexSP:
        assert args.use_ulysses and args.use_packing, "ulysses, packing and FlexSP all must be satisfied"
        if args.model_size == 'gpt-7b' and world_size == 16:
            optimizer_param_dict[args.model_size]['act_per_token'] = 2.668764648
        flexSP_cost_model = flexSPCostModel(
                 cluster_size = torch.distributed.get_world_size(),
                 hidden_size = args.hidden_size,
                 layer_num = args.num_hidden_layers,
                 param_size_B = param_size_B, 
                 zero_stage = 3 if args.sdp == 1 else 3 if args.default_dp_type == "zero3" else 2,
                 mixed_precision = True,
                 act_per_token = optimizer_param_dict[args.model_size]['act_per_token'], 
                 cpt_alpha1 = optimizer_param_dict[args.model_size]['cpt_alpha1'], 
                 cpt_alpha2  = optimizer_param_dict[args.model_size]['cpt_alpha2'], 
                 cpt_beta1 = optimizer_param_dict[args.model_size]['cpt_beta1'],
                alltoall_bandwidth_dict_gbs = {1: 1e10, 2: 119.54, 4: 104.07, 8: 96.5, 16: 10.33, 32:5.94, 64:4.87}, 
        )
        param_dict = {
            "limits/time": 10,
        }
        flexSP_optimizer = flexSPOptimizer(
            cluster_size = torch.distributed.get_world_size(),
            memory_limit_gb = 28, 
            costmodel = flexSP_cost_model,
            hide_scipoutput=True,
            hide_alloutput = True,
            concurrent = False,
            scip_param_dict = param_dict,
            strategy = args.flexSP_strategy,
        )
        flexSP_optimizer.fix_sp_size = 64 if max_len > 192000 else 32
        if 'wikipedia' in args.dataset and max_len >= 192000:
            flexSP_optimizer.fix_sp_size = 64
        flexSP_optimizer.fix_sp_size = min(flexSP_optimizer.fix_sp_size, torch.distributed.get_world_size())
        
    model = construct_hybrid_parallel_model(
        model=gpt_model, 
        model_config=config, 
        training_args=args, 
        hybrid_parallel_configs=hybrid_parallel_configs
    )

    if args.selective_checkpoint:
        from galvatron.models.gpt_hf.GPTModel_tensor_parallel import GPTLayer_tp, GPTMLP_tp, GPTAttention_tp
        layer_num = len(hybrid_parallel_configs['checkpoint_flags_enc'])
        if args.model_size == 'gpt-7b':
            ckpt_mlp_num = 12 if world_size >= 32 else layer_num
            ckpt_flag = [0]+[1]*ckpt_mlp_num+[0]*(layer_num-ckpt_mlp_num)+[0,0]
            model.model.wrap_pipeline_modules_checkpoint(ckpt_flag, wrap_block_name=[GPTMLP_tp])
        elif args.model_size == 'gpt-13b':
            ckpt_flag = [0]+[1]*layer_num+[0,0]
            model.model.wrap_pipeline_modules_checkpoint(ckpt_flag, wrap_block_name=[GPTMLP_tp])
        elif args.model_size == 'gpt-30b':
            ckpt_attn_num = layer_num*4//5
            ckpt_flag = [0]+[1]*ckpt_attn_num+[0]*(layer_num-ckpt_attn_num)+[0,0]
            model.model.wrap_pipeline_modules_checkpoint(ckpt_flag, wrap_block_name=[GPTAttention_tp])
            ckpt_flag = [0]+[1]*layer_num+[0,0]
            model.model.wrap_pipeline_modules_checkpoint(ckpt_flag, wrap_block_name=[GPTMLP_tp])

    if local_rank == 0:
        print("Creating Dataset...")
    trainloader = distributed_dataloader(
        dataset=DataLoaderForGPT(args, device),
        global_bsz=args.global_train_batch_size,
        shuffle=False,
        args=args,
        group = model.dp_groups_whole[0].group if not args.use_flexSP else torch.distributed.new_group(ranks = [torch.distributed.get_rank()]),
        flexSP_optimizer_ = None if not args.use_flexSP else flexSP_optimizer,
    )
    
    optimizer = Adam(model.parameters(), lr=args.lr, weight_decay=args.adam_weight_decay)
    profiler = args.profiler

    if local_rank == 0:
        print("Start training...")
    for ep in range(args.epochs):
        if not args.check_loss and not args.profile:
            trainloader = tqdm(trainloader)
        for iter, batch in enumerate(trainloader):
            if iter == 0:
                continue
            from galvatron.core import get_args
            if not get_args().use_packing:
                batch = [batch]
            loss = model.forward_backward(batch, iter, profiler)
            profiler.profile_time_start(iter)
            optimizer.step()
            
            optimizer.zero_grad()
            
            if local_rank == 0:
                print_loss(args, loss, ep, iter)
            profiler.profile_time_end(iter)
            profiler.profile_time_iter_end(iter)

            torch.distributed.barrier()

if __name__ == '__main__':
    args = initialize_galvatron(model_args, mode='train_dist')
    set_seed()
    train(args)
