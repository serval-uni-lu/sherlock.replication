"""
Combine collected metrics
"""
import pandas as pd
import process 
import os
from tqdm import tqdm
import utils
import numpy as np

DATA_INFO = ['project', 'commit', 'coveredClass', 'coveredClassPath']
STATIC_METRICS = ['sm_dates', 'sm_randoms', 'sm_io', 'sm_collections', 'sm_threads', 'sm_networks']
CHANGE_METRICS = ['uniq_changes', 'developers', 'age']
LABEL = 'isSusFlaky'
SBFL_formulas = ['dstar', 'ochiai', 'tarantula', 'barinel']
EXCLUDE_NON_EXIST = True

def get_sbfl_susps_file(resultdir, sbfl_formula):
    """
    """
    sbfl_susps_files = []
    for subdir, dirs, files in os.walk(resultdir):
        for file in files:
            if file == '{}.ranking.csv'.format(sbfl_formula):
                sbfl_susps_files.append(os.path.join(subdir, file))
    
    assert len(sbfl_susps_files) > 0, resultdir 
    if len(sbfl_susps_files) > 1:
        filtered = list(filter(lambda path: 'method' not in path, sbfl_susps_files))
        sbfl_susp_file = filtered[0] 
    else:
        sbfl_susp_file = sbfl_susps_files[0]
    return sbfl_susp_file


def get_sbfl_susps(susp_file):
    """
    """
    susp_raw_df = process.read_susps(susp_file)
    is_method = "#" in susp_raw_df.name.values[0]
    
    sps_vs = {}
    for elemn_id, sps_v in susp_raw_df.values:
        class_id = elemn_id.split(":")[0]
        if is_method:
            class_id = class_id.split('#')[0]

        if class_id not in sps_vs.keys():
            sps_vs[class_id] = []
        sps_vs[class_id].append(sps_v)

    # take the best (larget) -> class-level aggregation
    for class_id in sps_vs.keys():
        sps_vs[class_id] = np.max(sps_vs[class_id])

    return sps_vs

 
def get_file_part_of_class(aclass):
    """
    """
    matching_file = "/".join(aclass.split("$")[:2]).replace(".",'/') + ".java"
    return matching_file

def get_suspected_classes(target_data_file, project_name):
    """
    """
    import re  
    target_df = utils.get_targets(target_data_file, project_name, w_gt = True)[project_name]
    suspected_classes = {
        commit:[v.strip() if not v.strip().endswith(".java") else v.strip()[:-5] for v in modules.replace("|", ",").split(",")] 
           for commit, modules in target_df[['Commit', 'Module suspected to be flaky']].values}
    return suspected_classes


def get_isSusFlaky(coveredClasses, suspected_classes):
    """
    """
    import re
    isSusFlaky_vs = np.zeros(len(coveredClasses))
    for i, coveredClass in enumerate(coveredClasses):
        for suspected_class in suspected_classes:
            ####
            if suspected_class[-1] in ['$', '#']:
                suspected_class = suspected_class[:-1]
            if suspected_class.endswith('*'):
                if suspected_class[-2] in ['$', '#']:
                    suspected_class = suspected_class[:-2]

            is_ends_with = coveredClass.endswith(suspected_class)
            if is_ends_with:
                isSusFlaky_vs[i] = 1
                break 
            elif suspected_class in coveredClass:
                classes_parts = coveredClass.split("$")[1:] # should be this
                is_part_of = suspected_class in classes_parts
                if is_part_of:
                    isSusFlaky_vs[i] = 1
                    break
            elif suspected_class.startswith("*"): # alluxio's c5b1283b8d8561cbeab1c3bc4b63d5a9f6a74e8c
                pattern_to_match = '.' + suspected_class
                classes_parts = coveredClass.split("$")[1:] # should be this
                for class_part in classes_parts:
                    if bool(re.match(pattern_to_match, class_part)):
                        isSusFlaky_vs[i] = 1
                        break 
            else:
                continue
    return isSusFlaky_vs 


def combine_all(change_metrics, sps_per_formula, project_name = None):
    """
    change_metrics -> dataframe
    """
    classes = list(sps_per_formula[SBFL_formulas[0]].keys())
    # uniq_changes,developers,age
    # convert change_metrics to per class 
    #
    change_metrics = change_metrics.set_index('file')
    files_to_lookat = change_metrics.index.values
    # coveredClassPath -> a path to the file that contains covered class path
    combined = {'coveredClass':[], 'coveredClassPath':[], 
        'uniq_changes':[], 'developers':[], 'age':[],
        'dstar':[], 'ochiai':[], 'tarantula':[], 'barinel':[]}

    for aclass in tqdm(classes):
        # get the path to the file that contains the class 'aclass'
        afile_id_from_class = get_file_part_of_class(aclass)
        matching = lambda v:v.endswith(afile_id_from_class)

        in_which_files = np.where(change_metrics.index.map(matching).values)[0]
        max_age = 1 * np.max(change_metrics.age.values) # to handle the case where fail to collect metrics
        # sometime, the change metrics are missing due to:
        #   the class out of scope (zookeeper from pulsar) (mostly here) or failing to capture (really rare)
        if len(in_which_files) == 0:#
            if not EXCLUDE_NON_EXIST:
                combined['coveredClass'].append(aclass) 
                # add sbfl susps 
                combined['dstar'].append(sps_per_formula['dstar'][aclass]) 
                combined['ochiai'].append(sps_per_formula['ochiai'][aclass]) 
                combined['tarantula'].append(sps_per_formula['tarantula'][aclass]) 
                combined['barinel'].append(sps_per_formula['barinel'][aclass]) 

                ### this part should be changed -> either exclude or ...
                combined['coveredClassPath'].append(None)
                # add change metrics
                combined['uniq_changes'].append(1) # the smallest value
                combined['developers'].append(1) # the smallest value
                combined['age'].append(max_age) 
            continue
       
        assert len(in_which_files) == 1, "{} -> {}".format(aclass, afile_id_from_class)

        combined['coveredClass'].append(aclass) 
        # add sbfl susps 
        combined['dstar'].append(sps_per_formula['dstar'][aclass]) 
        combined['ochiai'].append(sps_per_formula['ochiai'][aclass]) 
        combined['tarantula'].append(sps_per_formula['tarantula'][aclass]) 
        combined['barinel'].append(sps_per_formula['barinel'][aclass]) 

        idx_to_file = in_which_files[0]
        afile_class_belong = files_to_lookat[idx_to_file]
        combined['coveredClassPath'].append(afile_class_belong if project_name is None 
            else os.path.join(project_name, afile_class_belong))

        # add change metrics
        combined['uniq_changes'].append(change_metrics.uniq_changes[afile_class_belong])
        combined['developers'].append(change_metrics.developers[afile_class_belong])
        combined['age'].append(change_metrics.age[afile_class_belong])

    return combined  

def main(args = None, **kwargs):
    import argparse, pickle
    if args is None:
        parser = argparse.ArgumentParser()
        parser.add_argument("-dst", "--dest", type = str, default = ".")
        parser.add_argument("-project", "--project_name", type = str, default = None,   
            help = "e.g., pulsar")
        parser.add_argument("-project_id", "--full_project_name", type = str, default = None,
            help = "e.g., apache/pulsar")
        parser.add_argument("-target", "--target_data_file", type = str, default = "targets/data.tsv",
            help = "the tsv file of the spreadsheet")
        parser.add_argument("-sbfl", "--sbfl_result_dir", type = str, default = "../projects/pulsar",
            help = "a directory that contains gzoltar results of all commits of a target project")
        parser.add_argument("-repo", type = str, default = "benchmarks/pulsar",
            help = "a github repository of a proejct")
        parser.add_argument("-cm", "--change_metric_dir", type = str, 
            help = "a directory that contains change metrics: change_metric_dir/$\{commit\}/file")

        args = parser.parse_args()

    if 'project_name' in kwargs.keys():
        project_name = kwargs['project_name']
    else:
        project_name = args.project_name

    if 'project_id' in kwargs.keys():
        full_project_name = kwargs['project_id']
    else:
        full_project_name = args.full_project_name

    if 'repo' in kwargs.keys():
        repo = kwargs['repo']
    else:
        repo = args.repo

    if 'sbfl' in kwargs.keys():
        sbfl_result_dir = kwargs['sbfl']
    else:
        sbfl_result_dir = args.sbfl_result_dir

    if 'change_metric_dir' in kwargs.keys():
        change_metric_dir = kwargs['change_metric_dir']
    else:
        change_metric_dir = args.change_metric_dir

    execution_info_file = os.path.join("targets/test_and_class_info_{}.pkl".format(project_name))
    with open(execution_info_file, 'rb') as f:
        # key: (short) project -> commit -> Class or Test 
        exec_classes_and_tests_info = pickle.load(f)
    exec_classes_and_tests_info = exec_classes_and_tests_info[project_name]

    entire_commits_in_rev, _  = utils.get_commit_infos_and_order(repo)
    # commits_to_inspect(dict): key = fix_commit, value: parent commit of the fix
    commits_to_inspect = utils.get_commits_to_inspect(args.target_data_file, full_project_name, entire_commits_in_rev)
    #
    suspected_classes_per_fault = get_suspected_classes(args.target_data_file, full_project_name)

    final_combined_df = None
    for fix_commit,_ in tqdm(list(commits_to_inspect.items())):
        print ("Commit : {}".format(fix_commit))
        resultdir_to_lookat = os.path.join(sbfl_result_dir, fix_commit)
        if not os.path.exists(resultdir_to_lookat):
            resultdir_to_lookat = utils.get_matching_dir(resultdir_to_lookat)
            if resultdir_to_lookat is None:
                print ("directory for commit {} not exists for {}".format(fix_commit, full_project_name))
                continue

        sps_per_formula = {}
        for sbfl_formula in SBFL_formulas:
            sps_file_to_lookat = get_sbfl_susps_file(resultdir_to_lookat, sbfl_formula)
            # retrieve sbfl results 
            sps_p_class = get_sbfl_susps(sps_file_to_lookat)
            sps_per_formula[sbfl_formula] = sps_p_class

        # for ccm 
        chg_metric_file = os.path.join(change_metric_dir, "{}/ccm_metrics.pf.csv".format(fix_commit))
        change_metrics = pd.read_csv(chg_metric_file)
        
        # combine ccm and sbfl
        sps_chg_metrics_df = combine_all(change_metrics, sps_per_formula, project_name=project_name)
        # add commits
        sps_chg_metrics_df['commit'] = [fix_commit] * len(sps_chg_metrics_df['coveredClass'])
        sps_chg_metrics_df = pd.DataFrame(sps_chg_metrics_df)
        
        ## add labels 
        isSusFlaky_vs = get_isSusFlaky(sps_chg_metrics_df['coveredClass'], suspected_classes_per_fault[fix_commit])
        sps_chg_metrics_df['isSusFlaky'] = isSusFlaky_vs
        
        ## additional filtering -> filter out those classes that have never been executed 
        if exec_classes_and_tests_info is not None:
            sps_chg_metrics_df = sps_chg_metrics_df.loc[
                sps_chg_metrics_df.coveredClass.isin(exec_classes_and_tests_info[fix_commit]['Class'])]

        if final_combined_df is None:
            final_combined_df = sps_chg_metrics_df
        else:
            final_combined_df = final_combined_df.append(sps_chg_metrics_df, ignore_index = True)

    print ("final combined: {}".format(len(final_combined_df)))
    # add project
    metric_names = [
        'project', 'commit', 'coveredClass', 'coveredClassPath',
        'dstar', 'ochiai', 'tarantula', 'barinel',
        'uniq_changes', 'developers', 'age',
        'isSusFlaky']

    final_combined_df['project'] = [project_name] * len(final_combined_df.coveredClassPath)
    final_combined_df = final_combined_df[metric_names]

    dest = os.path.join(args.dest, project_name)
    os.makedirs(dest, exist_ok= True)
    destfile = os.path.join(dest, "sbfl_chgs_{}.csv".format(project_name))
    
    print ("saved to {}".format(destfile))
    final_combined_df.to_csv(destfile, index = False)


if __name__ == "__main__":
    main()