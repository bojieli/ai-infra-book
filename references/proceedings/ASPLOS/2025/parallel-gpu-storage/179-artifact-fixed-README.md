# NF2FS

The source code of paper: "<u>Simplifying and Accelerating NOR Flash I/O Stack for RAM-Restricted Microcontrollers</u>". Published on the ACM International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS'25), Rotterdam, The Netherlands.

## Introduction

NF2FS is a NOR flash file system that achieves high-performance I/O and long lifespan under extremely RAM restrictions (e.g., 2216 B in our tests), and the source code is in ***/NF2FS_code***.

We deploy NF2FS on Positive Atomic STM32H750 Polaris development board to test its I/O efficiency, and the source code is in ***/board_environment***.

We also construct an emulated NOR flash environment to verify the correctness of NF2FS on PC. Moreover,  since the lifespan test is time consuming (even on PC), we accelerate it through storage layout simulation. The source code are in ***/emulated_environment***.

Finally, the design and evaluation details are in the paper ***/doc/NF2FS.pdf***.

## Board Environment Setup

**1. Clone NF2FS from Github:**

~~~shell
git clone https://github.com/HIT-HSSL/NF2FS.git
~~~

**2. Download Keil**

Keil uVision5 is available in https://www.keil.com/demo/eval/c51.htm.

<img src=".\image\Keil.jpg" alt="Keil" />

**3. Open the board environment**

Open the file ***/board_environment/USER/NORENV.uvprojx*** with Keil uVision5.

**4. Configurations**

First, click the button ***Options for Target***.

<img src=".\image\Options-button.png" alt="Options-button" />


Then, in ***Device***, choose STM32H750XBHx as the target development board.

<img src=".\image\Device.png" alt="Device" style="zoom: 50%;" />

In ***Target***, set ***Read/Only*** and ***Read/Write Memory Areas*** to store to be downloaded binary.

<img src=".\image\Target.png" alt="Target" style="zoom:50%;" />

In ***C/C++***, choose ***O0 optimization***, ***One ELF Section per Function***, ***C99 Mode***.

<img src=".\image\C-C++.png" alt="C-C++" style="zoom:50%;" />

In ***Linker***, click the button ***Use Memory Layout from Target Dialog***.

<img src=".\image\Linker.png" alt="Linker" style="zoom:50%;" />

Finally, Click the button ***OK*** to save configurations.

<img src=".\image\OK.png" alt="OK" style="zoom:50%;" />

**5. Build binary**

Click the button ***Rebuild*** to build the binary.

<img src=".\image\Rebuild.png" alt="Rebuild" />

**6. Link development board to PC**

We choose ***Positive Atomic STM32H750 Polaris*** as the target development board, which uses ***ST-Link*** (① in figure) to download binary. Moreover, we use ***XCOM*** (② in figure) to receive message from board to PC. Note that ST-Link is a hardware, while XCOM is a software, and they both use USB interface to link with PC.

<img src=".\image\Board.png" alt="Board" />

<img src=".\image\XCOM.png" alt="XCOM" />

**7. Download binary to development board**

Finally, click the button ***Download***, and NF2FS will run on the development board automatically!

<img src=".\image\Download.png" alt="Download" />

## Emulated Environment Setup

To ensure the reproducibility of our experiments, we provide a simple docker environment to run NF2FS on PC. The user can run basic I/O test in the non-docker/docker environment.

**1. Clone NF2FS from Github:**

~~~shell
git clone https://github.com/HIT-HSSL/NF2FS.git
~~~

**2. Run NF2FS in the emulated environment**

**2.1 Run NF2FS in the docker environment**

First, build the docker image.
~~~shell
docker build . -t nf2fs-artifact
~~~

Then, run the docker container.
~~~shell
docker run --rm -it nf2fs-artifact
~~~

Inside docker, the code is located in /emulated_environment/normal_test, simply run the following command to test NF2FS.
~~~shell
cd /emulated_environment/normal_test
make test
~~~

**2.2 Run NF2FS in the non-docker environment**

~~~shell
cd ./NF2FS/emulated_environment
cd ./normal_test
make test
~~~

**3. Run Lifespan Test**

We conduct lifespan test through storage layout simulation, which are stored in ***/emulated_environment/lifespan_test*** as jupyter files. The reason is that running lifespan test takes too much time to wear out NOR flash (e.g., 10K P/E cycle), even if in the emulated NOR flash environment.
