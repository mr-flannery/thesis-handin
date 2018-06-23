# Thesis Handin

This repository contains additional material associated with my master thesis.

## datasetGenerator.py

`datasetGenerator.py` is the script used to generate the dataset used for the evaluation.
It takes a sample CSV file as input and generates a dataset as well as SQL statements for setting up authorization so that the same experiments I ran for my thesis can be run on this dataset.
The script was tested with `2.7.10` and `3.6.5`.

### Usage

```
usage: datasetGenerator.py [-h]
                           samplePath recordsPerAufnr aufnrPerCc
                           hierarchyDepth selectivitySteps [outputDirectory]

Generate a dataset and corresponding authorizations from a sample dataset.

positional arguments:
  samplePath        Path to the sample CSV file
  recordsPerAufnr   Number of records per internal order.
  aufnrPerCc        Number of internal orders per cost center.
  hierarchyDepth    Depth of the generated cost center hierarchies.
  selectivitySteps  Number of selectivity steps (the data will be generated
                    such that there is an equal amount of records per
                    selectivity step).
  outputDirectory   Directory where the output files are stored to. Defaults
                    to "output/".

optional arguments:
  -h, --help        show this help message and exit
```

## diagrams

The `diagrams` directory contains all the diagrams generated from the measurements that can be found in the evaluation chapter and the appendix of the thesis.
Additionally, it includes the raw CSV files parsed from the various traces of the evaluation application, the application layer and the database.