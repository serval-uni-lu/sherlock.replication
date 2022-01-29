#!/bin/bash
repo=$1
project=$2
dest=$3 #"results"

python3 run.py -repo $repo -project $project -dest $dest -postfix .java 

