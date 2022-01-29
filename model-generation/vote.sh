#!/bin/bash

dest=$1
model_dir=$2
top_n=$3
foldfile='data/data_folds.tsv'

python3 main_vote.py -dst $dest -result ${model_dir} -fold $foldfile -vote rank -weighted -top_n $top_n
