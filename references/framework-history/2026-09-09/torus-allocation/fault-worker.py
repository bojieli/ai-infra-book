import subprocess
import sys
import socket
from datetime import datetime

HOST = "192.168.171.200"
PORT = 65432
mpi_run_cmd_1 = "mpirun -np 2 --prefix /home/dd687/miniconda3/envs/nccl --hostfile ./hostfile  -x NCCL_DEBUG=INFO -x NCCL_IB_DISABLE=1 -x NCCL_SOCKET_IFNAME=eno12409,eno12419 -x MASTER_ADDR=10.0.0.0 -x MASTER_PORT=12345   bash ./ml/run"
mpi_run_cmd_2 = "mpirun -np 2 --prefix /home/dd687/miniconda3/envs/nccl --hostfile ./hostfile_n  -x NCCL_DEBUG=INFO -x NCCL_IB_DISABLE=1 -x NCCL_SOCKET_IFNAME=eno12409,eno12419 -x MASTER_ADDR=10.0.0.0 -x MASTER_PORT=12345   bash ./ml/run"

switch_config_1 = [(0, '='), (1, 'x'), (2, 'x'), (3, 'x'), (4, 'x'), (5, '='), (6, 'x'), (7, '='), (8, '='), (9, 'x'), (10, '='), (11, 'x'), (12, '='), (13, '='), (14, 'x'), (16, 'x'), (17, 'x'), (18, '='), (19, '='), (21, 'x'), (23, '='), (24, '='), (25, 'x'), (26, '='), (28, 'x'), (29, 'x'), (30, 'x'), (31, '='), (34, 'x'), (35, 'x'), (36, '='), (38, '='), (39, 'x'), (40, 'x'), (41, 'x'), (42, '='), (44, '='), (45, '='), (46, '='), (47, 'x'), (48, 'x'), (49, 'x'), (50, 'x'), (51, 'x'), (53, 'x'), (54, '='), (55, 'x'), (57, 'x'), (58, '='), (59, 'x'), (60, 'x'), (61, 'x'), (64, 'x'), (65, 'x'), (68, 'x'), (69, 'x'), (71, 'x')]

switch_config_2 = [(0, 'x'), (1, 'x'), (2, '='), (4, 'x'), (6, '='), (7, 'x'), (8, '='), (9, 'x'), (10, '='), (12, '='), (13, '='), (15, '='), (16, 'x'), (19, 'x'), (21, 'x'), (25, 'x'), (26, 'x'), (29, 'x'), (31, 'x'), (35, 'x'), (36, 'x'), (40, 'x'), (42, 'x'), (45, 'x'), (46, '='), (47, '='), (48, '='), (50, 'x'), (51, 'x'), (53, 'x'), (54, 'x'), (55, 'x'), (59, 'x'), (60, 'x'), (61, 'x'), (64, '='), (65, 'x'), (68, 'x'), (69, 'x'), (71, 'x')]


def log(message):
    with open("ft_worker.log", "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        second = datetime.now().timestamp()
        log_file.write(f"{timestamp} - {second} - {message}\n")


def launch_mpi_process(command):
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("MPI process completed successfully.")

        log("MPI process completed successfully.")
            
        print("Output:", result.stdout.decode())
        log(f"Output: {result.stdout.decode()}")
    except subprocess.CalledProcessError:
        print("MPI process failed.")
        log("MPI process failed.")
        # print("Error:", e.stderr.decode())
        fault_handler()

def fault_handler():
    # ping the server to do reconfiguration
    ping_server(switch_config_2)
    print("Handling fault...")

    # update hostfile
    with open('hostfile_n', 'w') as hostfile:
        hostfile.write("arjun@192.168.171.195 slots=1\n")
        hostfile.write("dd687@192.168.171.197 slots=1\n")
    # restart the MPI process
    log("Start moving checkpoint")
    subprocess.run(["scp", "./checkpoint_epoch_0.pt", "dd687@192.168.171.197:~/"])
    log("Moving dataset")
    subprocess.run(["scp", "-r", "./wikitext_103_dataset", "dd687@192.168.171.197:~/"])

    print("Restarting the MPI process...")
    log("Restarting the MPI process...")
    mpi_command = mpi_run_cmd_2.split()
    launch_mpi_process(mpi_command)

def ping_server(switch_config):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect((HOST, PORT))
            print(f"Connected to the server at {HOST}:{PORT}")

            # Receive initial instructions from the server
            data = client_socket.recv(1024).decode()
            print(data)

            puc_list = switch_config

            print(f"Sending PUC List: {puc_list}")

            # ports_message = f"{','.join(map(str, input_ports))};{','.join(map(str, output_ports))}\n"
            ports_message = f"{puc_list}\n"

            client_socket.sendall(ports_message.encode())

            # Receive server responses
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                print(data.decode(), end='')
                log(data.decode())
        except ConnectionRefusedError:
            print("Failed to connect to the server. Is it running?")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    ping_server(switch_config_1)
    command = mpi_run_cmd_1.split()
    launch_mpi_process(command)
