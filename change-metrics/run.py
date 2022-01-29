"""
collect change metrics (age, developers, # of unique changes) for a specific commit of a target project
"""
import get_classes
import generate_cm
import combine_cm_and_sbfl
import argparse
import os
import add_sm 

parser = argparse.ArgumentParser()
parser.add_argument("-dst", "--dest", type = str)
parser.add_argument("-project", "--project_name", type = str, default = None,
    help = "e.g., apache/pulsar")
parser.add_argument("-target", "--target_data_file", type = str, default = "targets/data.tsv",
    help = "the tsv file of the spreadsheet")
parser.add_argument("-sbfl", "--sbfl_dir", type = str, default = "../projects",
    help = "a directory that contains gzoltar results of all the target projects")
parser.add_argument("-repo", "--root_repo", type = str, default = "benchmarks",
    help = "a directory where all prgithub repositories of all the target proejcts are stored")
parser.add_argument("-postfix", type = str, default = ".java")
# for generate_cm
parser.add_argument("-renamed", "--file_renamed_file", type = str, default = None,
    help = "e.g., commit_changes/results/pulsar.rename_history.json")
parser.add_argument("-chginfo", "--commit_chginfo_file", type = str, 
    help = "a file that contains commit changes information per modified file. \
        e.g., commit_changes/results/pulsar.commit_chgs.pf.pkl")

args = parser.parse_args()

sbfl_result_dirs = {
    'apache/hbase':os.path.join(args.sbfl_dir, 'hbase'), 
    'apache/ignite':os.path.join(args.sbfl_dir, 'ignite'), 
    'apache/pulsar':os.path.join(args.sbfl_dir, 'pulsar'), 
    'Alluxio/alluxio':os.path.join(args.sbfl_dir, 'alluxio'),
    'neo4j/neo4j':os.path.join(args.sbfl_dir, 'neo4j')}

repos = {'apache/hbase':os.path.join(args.root_repo,'hbase'), 
    'apache/ignite':os.path.join(args.root_repo,'ignite'),
    'apache/pulsar':os.path.join(args.root_repo,'pulsar'),
    'Alluxio/alluxio':os.path.join(args.root_repo,'alluxio'),
    'neo4j/neo4j':os.path.join(args.root_repo,'neo4j')}

project_full_names = {'hbase':'apache/hbase', 'ignite':'apache/ignite', 
    'pulsar':'apache/pulsar', 'alluxio':'Alluxio/alluxio', 'neo4j':'neo4j/neo4j'}

project_name = args.project_name
project_id = project_full_names[project_name]
repo = repos[project_id]
sbfl_result_dir = sbfl_result_dirs[project_id]

print ("Processing: {}".format(project_name))

# get & save a list of tests and the classes executed by the tests
get_classes.main(args = args, 
    project_name = project_name, project_id = project_id, repo = repo, sbfl = sbfl_result_dir)
#print ("covered classes recorded")

# process change information of individual files modified in each commit & generate change metrics  
generate_cm.main(args = args, 
    project_name = project_name, project_id = project_id, repo = repo, sbfl = sbfl_result_dir)
print ("change metrics generated")

# combine change metrics and sbfl score metrics
change_metric_dir = os.path.join(args.dest, project_name)
combine_cm_and_sbfl.main(args = args, 
    project_name = project_name, project_id = project_id, repo = repo, sbfl = sbfl_result_dir,
    change_metric_dir = change_metric_dir)
print ("sbfl metrics added (class gran)")

# add static metrics 
cm_sbfl_file = os.path.join(args.dest, "{}/sbfl_chgs_{}.csv".format(project_name, project_name))
sm_file = "../static-metrics/analysis/results/sm_{}.csv".format(project_name)
add_sm.main('../model-generation/data', cm_sbfl_file, sm_file, project_name)
print ("static metrics (flakiness & size) added & final data file generated")
