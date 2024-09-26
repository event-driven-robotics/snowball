Code to go with publication "An Asynchronous Quasi-Delay_Insensitive Bit-Serial Variable-Length Relative Address-Event Codec for Distributed Neuromorphic Systems", Bamford and Bartolozzi, 2024. IIT-EDPR Admins: this repo should remain here in perpetuity.

To run this code, first install ACT from this repository (which requires a linux installation), following its own instructions: https://github.com/asyncvlsi/act

Then, to recreate the simulation results in the paper for the incrementer/encoder:

In the folder "encoder", excute:

`aflat test_enc.act > test_enc.prs`

This will convert the act code to a production rule set.

Then execute:

`prsim test_enc.prs`

This will open the command ine of the prsim tool. From that command line, execute:

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

A snowball gains size and momentum as it rolls down a hill; the name is a metaphor for the events moving through the incrementer chain.



