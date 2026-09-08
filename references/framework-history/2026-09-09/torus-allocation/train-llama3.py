"""
echo "source /home/$USER/miniconda3/bin/activate nccl
python ./ml/dtrain_llama3.py" > ./ml/run

mpirun -np 2 --mca plm_base_verbose 10  --hostfile ./hostfile -x NCCL_DEBUG=INFO -x MASTER_ADDR=10.0.0.0 -x MASTER_PORT=12345   bash ./ml/run
"""

import os
import torch
from torch.utils.data import DataLoader
from torch.utils.data.distributed import DistributedSampler
from torch.nn.parallel import DistributedDataParallel as DDP
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
)
import time
from datasets import load_from_disk
import torch.distributed as dist
from torch.optim import AdamW
from mpi4py import MPI
import numpy as np
from torch.profiler import profile, record_function, ProfilerActivity
from datetime import datetime


def log(message):
    with open("ft_worker.log", "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        second = datetime.now().timestamp()
        log_file.write(f"{timestamp} - {second} - {message}\n")


def log_tp(message):
    with open("ft_worker_tp.csv", "a") as log_file:
        total_seconds = datetime.now().timestamp()
        log_file.write(f"{total_seconds},{message}\n")


EPOCH = 10
BATCH_SIZE = 8
GRADIENT_ACCUMULATION_STEPS = 1
epoch_times = []
token_list = []

# Set random seed for reproducibility
def set_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    os.environ['PYTHONHASHSEED'] = str(seed)

def setup_distributed():
    """Initialize distributed environment."""
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    world_size = comm.Get_size()
    dist.init_process_group(
        backend="nccl",  # Use "gloo" for CPU-only training
        init_method="env://",
        rank=rank,
        world_size=world_size,
    )
    local_rank = int(os.getenv("LOCAL_RANK", rank % torch.cuda.device_count()))
    torch.cuda.set_device(local_rank)
    return world_size, rank, local_rank


def cleanup_distributed():
    """Cleanup the distributed environment."""
    dist.destroy_process_group()


def main():
    set_seed(42)
    world_size, rank,local_rank = setup_distributed()

    # Load the Wikitext-103 dataset
    dataset_path = "./wikitext_103_dataset"
    dataset = load_from_disk(dataset_path)

    # Tokenize the dataset
    model_path = "./Llama-3.2-1B"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path)

    if tokenizer.pad_token is None:
        tokenizer.add_special_tokens({"pad_token": "[PAD]"})
        model.resize_token_embeddings(len(tokenizer))

    def tokenize_function(examples):
        return tokenizer(
            examples["text"], truncation=True, padding="max_length", max_length=512
        )

    tokenized_datasets = dataset.map(
        tokenize_function, batched=True, remove_columns=["text"]
    )

    # Prepare for training
    train_dataset = tokenized_datasets["train"].shuffle(seed=42).select(range(128))
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    # Use DistributedSampler for training data

    train_sampler = DistributedSampler(
        train_dataset, num_replicas=world_size, rank=rank, shuffle=True
    )
    train_dataloader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        sampler=train_sampler,
        collate_fn=data_collator,
    )

    # Move model to the appropriate GPU and wrap with DDP
    model.to(local_rank)
    model = DDP(model, device_ids=[local_rank])

    # Optimizer
    optimizer = AdamW(model.parameters(), lr=5e-5)

    # Training loop
    gradient_accumulation_steps = GRADIENT_ACCUMULATION_STEPS

    with profile(activities=[ProfilerActivity.CUDA], record_shapes=True, profile_memory=False) as prof:
        for epoch in range(EPOCH):
            total_tokens = 0
            start = time.time()
            model.train()
            train_sampler.set_epoch(epoch)  # Shuffle data differently each epoch

            for step, batch in enumerate(train_dataloader):
                iter_start = time.time()
                inputs = batch["input_ids"].to(local_rank)
                labels = batch["input_ids"].to(local_rank)

                outputs = model(inputs, labels=labels)
                loss = outputs.loss
                loss = loss / gradient_accumulation_steps
                loss.backward()

                if (step + 1) % gradient_accumulation_steps == 0:
                    optimizer.step()
                    optimizer.zero_grad()

                    if rank == 0:
                        print(f"Epoch {epoch}, Step {step}, Loss: {loss.item()}")

                total_tokens += batch["input_ids"].numel()
                iter_end = time.time()
                log_tp(batch["input_ids"].numel() / (iter_end - iter_start))

            end = time.time()
            print(f"Rank {rank} Epoch {epoch} took {end-start} seconds")
            log(f"Rank {rank} Epoch {epoch} took {end-start} seconds")
            print(f"Rank {rank} Total tokens processed: {total_tokens}")
            throughput = total_tokens / (end - start)
            print(f"Rank {rank} throughput {throughput} tokens/second")
            log(f"Rank {rank} Total tokens processed: {total_tokens}")

            if rank == 0:
                # Save checkpoint
                checkpoint_path = f"./checkpoint_epoch_{epoch}.pt"
                torch.save(model.state_dict(), checkpoint_path)
                print(f"Checkpoint saved at {checkpoint_path}")
                epoch_times.append(end - start)
                token_list.append(total_tokens)

            # if rank == 0:

            #     model.eval()
            #     sample_text = "Once upon a time"
            #     inputs = tokenizer(sample_text, return_tensors="pt").to(local_rank)
            #     with torch.no_grad():
            #         outputs = model.module.generate(inputs["input_ids"], max_length=512)
            #     generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            #     print(f"===EVAL===: {generated_text}")

    # Save the model (only on rank 0)
    if rank == 0:
        print("Training complete")
        log("Training complete")
        # Print epoch times
        print("Epoch Times:", epoch_times)
        log(f"Epoch Times: {epoch_times}")
        # Print average time per epoch
        print("Average Time per Epoch:", np.mean(epoch_times))
        log(f"Average Time per Epoch: {np.mean(epoch_times)}")
        # Print standard deviation of epoch times
        print("Standard Deviation of Epoch Times:", np.std(epoch_times))
        # Print total time taken
        print("Total Time Taken:", sum(epoch_times))
        log(f"Total Time Taken: {sum(epoch_times)}")

        # Print throughput
        print("Average Throughput per GPU:", sum(token_list) / sum(epoch_times), "tokens/second")
        log(f"Average Throughput per GPU: {sum(token_list) / sum(epoch_times)} tokens/second")

    cleanup_distributed()
    if rank == 0:
        print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=10))


if __name__ == "__main__":
    main()
