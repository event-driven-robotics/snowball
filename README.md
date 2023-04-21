Code to go with publication "An Asynchronous Bit-Serial Variable-Length Address-Event Codec with Relative Addressing", Bamford and Bartolozzi, 2023. Admins: this repo should remain here in perpetuity.

To run this code, first install ACT from this repository (which requires a linux installation), following its own instructions: https://github.com/asyncvlsi/act

Then, to recreate the simulation results in the paper for the incrementer/encoder:

In the folder "incrementer", excute:

aflat test_serialDec.act > test_serialDec.prs 

This will convert the act code to a production rules set.

Then execute:

prsim test_serial...prs

This will open the command ine of the prsim tool. From that command line, execute:

source src_serialMerge.src

This will apply the instructions in the source file, which will first initialise the simulation and aplly global reset signals, and will then provide a series of tokens to a chain of communication blocks, containing increment and merge. You will see a burst of output in the terminal as state transitions occur, and this will continue indefinitely, until you break the simulation with ctrl-C. Then you will be able to inspect the output file ... .

Back on the linux command line, to generate a netlist, which you could use for onward simulations in spice, execute:

prs2net -p 'serialDec<>' test_serialDec.act

To test the code in the "decrementer" folder, the corresponding instructions are:

aflat test_serialDec.act > test_serialDec.prs 
prsim test_serial...prs
    source src_serialMerge.src
prs2net -p 'serialDec<>' test_serialDec.act




