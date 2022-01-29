#!/bin/bash


dest=$1
datadir=$2
mode=$3

# GP will be repeated (end_v - start_v + 1) times, generating a model each with a differen random seed
start_v=0
end_v=30

foldfile="data/data_folds.tsv"
# contains the configuration of GP: e.g., the maximum tree depth of an individul model
configfile="config/gp.default.config"

# train
python3 main_learn2rank.py -data $datadir -dst $dest -algo gp -config $configfile -train -mode $mode -fold $foldfile -start $start_v -end $end_v &
wait $!

# test
python3 main_learn2rank.py -data $datadir -dst $dest -algo gp -config $configfile -test -mode $mode -fold $foldfile -start $start_v -end $end_v &
wait $!
