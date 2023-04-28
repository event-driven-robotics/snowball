Code to go with publication "An Asynchronous Bit-Serial Variable-Length Address-Event Codec with Relative Addressing", Bamford and Bartolozzi, 2023. Admins: this repo should remain here in perpetuity.

To run this code, first install ACT from this repository (which requires a linux installation), following its own instructions: https://github.com/asyncvlsi/act

Then, to recreate the simulation results in the paper for the incrementer/encoder:

In the folder "incrementer", excute:

`aflat test_incMerge.act > test_incMerge.prs`

This will convert the act code to a production rule set.

Then execute:

`prsim test_incMerge.prs`

This will open the command ine of the prsim tool. From that command line, execute:

`source src_incMerge.src`

This will apply the instructions in the source file, which will first initialise the simulation and aplly global reset signals, and will then provide a series of tokens to a chain of communication blocks, containing increment and merge. You will see a burst of output in the terminal as state transitions occur, which may last several seconds. Then you will be able to inspect the output file, called `output_R.dec`.

There is also a file corresponding to a chain of 8 communication blocks, for which the two files to use as above are:

`prsim test_incMergeX8.prs`

`source src_incMergeX8.src`

Back on the linux command line, to generate a netlist, which you could use for onward simulations in spice, execute:

`prs2net -p 'incMerge<>' test_incMerge.act`

To test the code in the "decrementer" folder, the corresponding instructions are:

`aflat test_dec.act > test_dec.prs` 

`prsim test_dec.prs`

`source src_dec.src`

`prs2net -p 'dec<>' test_dec.act`

This will produce two output files; one for thedownstream communications blocks, called `output_R.dec`, and one for the local event receiver, called `output_T.dec`. 

A snowball gains size and momentum as it rolls down a hill; the name is a metaphor for the events moving through the incrementer chain.



