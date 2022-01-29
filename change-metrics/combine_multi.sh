#!/bin/bash

dest=$1

python3 combine_multipleMetrics.py -target target/data_final.tsv -project apache/pulsar -dst code_and_change_metrics/pulsar -exec_info target/test_and_class_info.pkl &
wait $!

#python3 combine_multipleMetrics.py -target target/data_final.tsv -project apache/ignite -dst code_and_change_metrics/ignite -exec_info target/test_and_class_info.pkl & 
#wait $!

#python3 combine_multipleMetrics.py -target target/data_final.tsv -project neo4j/neo4j -dst code_and_change_metrics/neo4j -exec_info target/test_and_class_info.pkl & 
#wait $!

#python3 combine_multipleMetrics.py -target target/data_final.tsv -project Alluxio/alluxio -dst code_and_change_metrics/alluxio -exec_info target/test_and_class_info.pkl & 
#wait $!

#python3 combine_multipleMetrics.py -target target/data_final.tsv -project apache/hbase -dst code_and_change_metrics/hbase -exec_info target/test_and_class_info.pkl & 
#wait $!
