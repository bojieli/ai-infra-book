# RASSM
ASPLOS 2025 RASSM Artifact

### Download Instructions
Clone this repository using `git clone https://github.com/gt-tinker/RASSM.git`

### Pre-requisites
1. C++ compiler such as gcc-13 or Intel Classic Compiler ICC (preffered) -- https://www.intel.com/content/www/us/en/developer/articles/news/intel-c-compiler-classic-2021-2-1-release.html
2. cmake (version 3.10+)
3. boost (1.65 - 1.74) -- https://www.boost.org/users/history/version_1_68_0.html

### Downloading the dataset
A script to download the dataset has been provided, `/scripts/download_large_40M.sh`. The dataset requires around 45GB of space when uncompressed. The script will download all the matrices in our test suite and extract them in the format expected by the runscripts. The following steps can be used:
1. `export RASSM_DATASET=<desired download location>`
2. `export RASSM_HOME=<path to cloned repository>`
3. `bash $RASSM_HOME/scripts/download_large_40M.sh`

### Build Instructions

To build this repository, you will require a vectorizing C++ compiler that supports `c++-17`. We strongly suggest using the Intel Classic Compiler available from https://www.intel.com/content/www/us/en/developer/articles/news/intel-c-compiler-classic-2021-2-1-release.html for best reproducibility.

#### Build steps:

1. `export RASSM_HOME=<path to cloned repository>` or `export RASSM_HOME=$PWD` if at the base level of the cloned repository
2. `cd $RASSM_HOME`
3. `mkdir build`
4. `export RASSM_BUILD=$RASSM_HOME/build`
5. `cd build`
6. `cmake ../code`
7. `make`

If everything goes smoothly, the `rassm` executable should be produced.

#### Suggestions
1. If you are using the suggested ICC compiler and building boost from source, you will need to run, `export BOOST_ROOT=<path to boost installation base>`, `export CC=icc`, and `export CXX=icpc`.
2.

### Basic Testing
Once you have built the executable `rassm`, use the provided `$RASSM_HOME/scripts/run_basic_test.sh` script using `bash $RASSM_HOME/scripts/run_basic_test.sh`. This should run the `rassm` program for all the baselines and `rassm` itself for the SpMM kernel and make sure all the baselines are functional.

### Reproducing Figure 6 from the paper
To reproduce Figure 6 from the associated paper, the following sequence of commands should be used, assuming you are in `$RASSM_HOME`:
1. `bash scripts/run-all.sh` -- This will require several hours to finish and we recommend not using the system during this time. One way to use this command and exit the shell instance is via `nohup`. The command will then be `nohup bash scripts/run-all.sh > run-all.log &`

2. `bash scripts/extract_stats.sh`
3. Open the Jupyter notebook and hit the run button. Make sure the `working_dir` variable in the second block points to the output directory where the `extract_stats.sh` script generated the csv files.


You should now be able to see the plots from Figure 6 of the paper. Recall that the exact numbers will vary on several factors such as the machine used, background processes, etc. However, the general trends should be similar.

Please don't hesitate to reach out to us if you have any issues using this code.
