#!/bin/bash 

project=$1
repo=$2 #e.g., ./benchmarks
renamed=$3
chginfo=$4
dest=$5 

python3 run.py -dst $dest -project $project -sbfl ../projects/ -repo $repo -postfix .java -renamed $renamed -chginfo $chginfo
