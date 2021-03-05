# MTurk Processing

This library is intended to transform datastructures output by jspsych experiments
run with a psiturk server into pandas dataframes. Responses are scored and annotated
with basic metrics, such as which list they came from or whether the participant
clicked off the experiment during a list. There is the additional option to exclude
responses based on behavior that is unreasonable for a given task.

There is a second module that is intended to streamline the management of mturk
data, as well as interface with the psiturk database.

# Instructions

To use this library, please clone this repository and run `pip install ./MTurk_Processing`.

The process_all_MTurk.py file in the post_processing module provides a command line entry point.
Running this script with the `-h` flag will print out a brief description of the parameters needed
to run cleaning on an experiment.


# Modules 

## post process



## worker management








