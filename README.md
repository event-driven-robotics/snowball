Code to go with publication "An Asynchronous Quasi-Delay-Insensitive Bit-Serial Variable-Length Relative Address-Event Codec for Distributed Neuromorphic Systems", Bamford et al, 2025. IIT-EDPR Admins: this repo should remain here in perpetuity.

# Overview

This repo contains act-level designs for asynchronous address-event encoders and decoders, as well as code for simulating them, and additional code for working with the results of schematic simulations of the same designs.

There are three main folders contain the designs: 'encoder', 'decoder', and 'keeperised'; there is a folder 'outputs' containing expected test outputs, and there is a folder full of scripts, as explained below. 

# How to simulate the 'act' codecs

To run this code, first install ACT from this repository (which requires a linux installation), following its own instructions: https://github.com/asyncvlsi/act

Then, to recreate the simulation results in the paper for the incrementer/encoder:

In the folder "encoder", excute:

`aflat test_enc.act > test_enc.prs`

This will convert the act code to a production rule set.

Then execute:

`prsim test_enc.prs`

This will open the command line of the prsim tool. From that command line, execute:

`source src_enc.src`

This will apply the instructions in the source file, which will first initialise the simulation and apply global reset signals, and will then provide a series of tokens to a chain of communication blocks, containing increment and merge. You will see a burst of output in the terminal as state transitions occur, which may last several seconds. Then you will be able to inspect the output file, called `output_addr.dec`.

There is also a file corresponding to a chain of 8 communication blocks, for which the two files to use as above are:

`prsim test_encX8.prs`

`source src_encX8.src`

Back on the linux command line, to generate a netlist, which you could use for onward simulations in spice, execute:

`prs2net -p 'enc<>' test_enc.act`

To test the code in the "decoder" folder, the corresponding instructions are:

`aflat test_dec.act > test_dec.prs` 

`prsim test_dec.prs`

`source src_dec.src`

`prs2net -p 'dec<>' test_dec.act`

This will produce two output files; one for the downstream communications blocks, called `output_addr.dec`, and one for the local event receiver, called `output_local.dec`. 

# Keeperised design

The folder "keeperised" contains an alternative version of the inc and merge cells where the gates are not fully complementary but rather have keepers, and in which serial and parallel resets (gsr and gpr) have been replaced with a single reset signal (rst). These, along with other very minor modifications move the design from that used for the act/prsim simulations (as above) to the ams/spectre simulations used in the comparison to P-AER.

# Scripts

The contents of the scripts folder:

* The `act` simulations above can be run repeatedly with different random seeds, using `run_repeated.sh`.
* The one-of-four output sequences from the act simulations can be converted to actual serial addresses using `data_conversion.py`. This script also contains jupyter-style blocks for generating the histograms in the paper. 
* `calculate_slack_by_address.py` calculates how much slack there is from an average address in a chain of encoders downstream towards the exit. This was necessary in order to choose an equivalent amount of slack for the P-AER encoder comparison.
* `analyse_trace.py` takes the results of spectre simulations of both snowball and paer encoders and calculates latency and mean power metrics.
* `count_devices....py` scripts give transistor counts for the snowball encoder and the paer encoders generate for comparison.
* `scaling_diagram.py` contains the transcribed results of the above two scripts and creates the comparison diagram, which it then saves as an svg.
* `busify_wrapper...` scripts were used as part of the process of bringing the paer encoder designs (which were generated from `https://github.com/async-ic/actlib-neurosynaptic-perifery`) into a form where they could be included in a mixed-singnal simulation. Specifically, it converts verilog from a format where all inputs and outputs are listed as single pins and converts them to bus format. 
* `handshaking_diagram.py` and `spiral_diagram.py` are two scripts which only generate images for the paper. 

# Snowball

A snowball gains size and momentum as it rolls down a hill; the name is a metaphor for the events moving through the incrementer chain.



