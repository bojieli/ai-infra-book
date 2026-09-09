# Evaluation Results

This folder contains miscellaneous evaluation results collected in the Pythia paper.

## Directory Structure

- `/pythia-v1` contains benchmark results over the course of training, for the official Pythia suite.
- `/pythia-v0` contains benchmark results over the course of training, for v0 of the Pythia suite. The v0 models can be found at https://huggingface.co/models?other=pythia_v0 and more information can be found in the Pythia paper.
- `/opt` contains benchmark results for the fully-trained OPT suite up to 66b parameters, as a baseline to compare to the Pythia models.
- `/bloom` contains results on the fully-trained BLOOM suite, up to 7.1b parameters, as a baseline.
- `/bias-evals` contains results on the gendered pronoun-intervened Pythia models we trained for the corresponding case study in the Pythia paper. More information on these evaluations can be found in `../case-studies/README.md`.