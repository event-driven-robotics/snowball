#!/bin/sh

#
#  ./run_repeated.sh [number of runs] [start from run number]
#

fail=0
faildirs=""
proc=""
bold=$(tput bold)
normal=$(tput sgr0)
und=$(tput smul)

failed=0
iteration=0
numberofruns=100

# Define arrays of files and their corresponding stimulus files
files=("decoder/test_dec.act" "encoder/test_enc.act" "encoder/test_encX8.act")
extra_files=("decoder/src_dec.src" "encoder/src_enc.src" "encoder/src_encX8.src")

#
#  run_test name [option]
#
run_test () {
    echo "Testing ${bold}$1 ${normal} for $2 random delay run with $3 stimulus"
    cd ${1%/*}
    # clear run directory
    if [ -d run/$2 ]; then
	    rm -rf run/$2
    fi
    mkdir -p run/$2
    if aflat "../"$1 >> run/$2/test.prs; then
            echo -e "random_seed $2" > run/$2/prsim.in
	    cat "../"$3 >> run/$2/prsim.in
	    cat run/$2/prsim.in | prsim -r run/$2/test.prs > run/$2/prsim.out
	    if [ $? -ne 0 ] || egrep -q '(WRONG|WARNING|Node)' run/$2/prsim.out ; then
	        echo "${bold}*** simulation failed seed: $2 ***${normal}"
	        faildirs="${faildirs} ${1}-sim($2)"
	        failed=1
	        echo	
	    fi
    else
	    echo "${bold}*** circuit construction failed ***${normal}"
	    faildirs="${faildirs} ${1}-ckt"
	    failed=1
        echo
    fi
    cd ..
}

if [ ! $(command -v aflat) ]; then #&& ! command -v prsim ]; then
    echo "${bold}Error:${bold} aflat & prsim necessary for tests."
    exit 1
fi

# run all test except single one is specified
if [ ! -z $2 ]; then 
  iteration=$2
fi
if [ ! -z $1 ]; then 
  numberofruns=$1
fi

while [ $iteration -lt $numberofruns ]; do
    # Loop through each file
    for i in "${!files[@]}"; do
        file="${files[i]}"
        extrafile="${extra_files[i]}"

        if [ -f "$file" ]; then

                run_test "$file" $iteration "$extrafile"
        fi
    done
    iteration=$((iteration + 1))
done
iteration=0  # Reset iteration for next file

echo $failed
if [ $failed -eq 1 ]; then
    echo "${bold}*********************************"
    echo "* FAILED TESTS:${normal}$faildirs ${bold}*"
    echo "*********************************${normal}"
fi

exit $failed


