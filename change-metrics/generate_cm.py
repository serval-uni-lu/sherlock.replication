"""
Combine metrics collected for each commit for the current version
"""
import os
import pandas as pd 
import process
from tqdm import tqdm
import json
import utils

def get_src_files(spectra_file, repo, target_commit, 
    postfix = '.java', project = None, with_log = False):
    """
    return a list of files to inspect
    """
    all_existing_files = utils.get_list_of_existing_files(target_commit, repo, postfix = postfix)

    elements_df = process.read_elements(spectra_file)
    paths = elements_df.path.apply(lambda v:v.split("#")[0]).unique() #should be unique 
    # convert to general file format
    convert_to_filepath = lambda v: ("/".join(v.split("$")[:2])).replace(".", "/") + ".java"
    converted = list(map(convert_to_filepath, paths))
    
    cnt = 0; out_of_scope =0
    files_to_inspect = []
    for afile in set(converted):
        findout = False
        for full_path_file in all_existing_files:
            if full_path_file.endswith(afile):
                files_to_inspect.append(full_path_file)
                findout = True
                break 
        cnt += int(findout)
        if not findout: # fail to match with None
            print (afile)
            if project is not None:
                out_of_scope += int(project.lower() not in afile.lower())

    if with_log:
        num_cand = len(set(converted))
        print ("Among {} cands, we find out that {} have physical files at the same location".format(
            num_cand, cnt))
        if project is not None:
            print ("\tand {} of them are out of scope, meaning that we actually misssed {} ".format(
                out_of_scope, num_cand - cnt - out_of_scope))

    return files_to_inspect


def get_matched_file(target_to_match, candidate_files):
    """
    """
    for cand in candidate_files:
        if cand.endswith(target_to_match):
            return cand 
    return None


def combine(commits_prior_to_and_is_target, 
    commit_chginfo_per_file, files_to_inspect, 
    entire_commits_infos, recorded_renameds, 
    with_log = False): 
    """
    keys: commit 
        keys: 'history' (metric type)
            keys: 'uniq_changes', 'developers', 'age' (three history metrics)
                keys: paths to modified files
                values: matching metric values
    return:
    """
    metric_per_file = {afile:{'uniq_changes':None, 'developers':None, 'age':None} for afile in files_to_inspect}
    time_of_target = entire_commits_infos[commits_prior_to_and_is_target[0]][1]
    # for tracking file-renaming
    file_rename_history = {file_to_inspect:[file_to_inspect] for file_to_inspect in files_to_inspect}

    cnt = 0; miss_cnt = 0
    for commit in tqdm(commits_prior_to_and_is_target):
        # due to skping meaningless commits
        if commit not in commit_chginfo_per_file.keys():
            continue 
        modifieds = commit_chginfo_per_file[commit]['history']
        author_of_commit, time_of_commit = entire_commits_infos[commit]
        time_dist_to_target = (time_of_target - time_of_commit).total_seconds()
        modified_files = list(modifieds['uniq_changes'].keys())
        
        # for tracking file-naming
        # since we have file_rename_history, we only need to specify the commit to chcek
        renamed = utils.get_renamed_files(commit, None, file_rename_history = recorded_renameds) 
        utils.update_renamed_files(file_rename_history, renamed)
        # each file in the_last_ver_target_files is one-to-one mapped with files_to_inspect
        the_last_ver_files_to_inspect = [file_rename_history[file_to_inspect][-1] for file_to_inspect in files_to_inspect]
        for modified_file in modified_files:
            # only the file renaming../ 
            matched_file = get_matched_file(modified_file, the_last_ver_files_to_inspect) 
            if matched_file is not None:
                idx_to_matched = the_last_ver_files_to_inspect.index(matched_file)
                matched_file_at_target = files_to_inspect[idx_to_matched]
                # unique changes
                # since it has been modified at this commit and thereby matched, we have to reflect it
                n_uniq_changes = modifieds['uniq_changes'][modified_file] + 1 
                metric_per_file[matched_file_at_target]['uniq_changes'] = n_uniq_changes

                # developers
                developers = modifieds['developers'][modified_file]
                developers.add(author_of_commit)
                n_developers = len(developers)
                metric_per_file[matched_file_at_target]['developers'] = n_developers

                # age -> the time difference between the target and the commit that changes the file
                metric_per_file[matched_file_at_target]['age'] = time_dist_to_target

                # drop this file as we already inspected it
                files_to_inspect.remove(matched_file_at_target) # drop it as we already inspect & gather all metrics 
                the_last_ver_files_to_inspect.remove(matched_file) # also, drop the last version of the matched file

                # logging
                cnt += 1
            else:
                miss_cnt += 1
    # check msising 
    if with_log:
        print ("\nOut of {} files, we have failed to collect metrics for {}".format(
            len(metric_per_file), len(files_to_inspect)))
        for afile in files_to_inspect:
            print ("\tfailed: {}".format(afile))
        
    return metric_per_file


def convert_nested_dict_to_df(target_dict):
    """
    """
    outer_keys = list(target_dict.keys()) # will be indices
    inner_keys = list(list(target_dict.values())[0].keys()) 
    vals = {'file':outer_keys}
    for inner_key in inner_keys:
        vals[inner_key] = []
        for outer_key in outer_keys:
            v = target_dict[outer_key][inner_key]
            vals[inner_key].append(v)
    df = pd.DataFrame(vals).set_index('file')
    return df 


def main(args = None, **kwargs):
    """
    """
    import argparse
    
    if args is None:
        parser = argparse.ArgumentParser()
        parser.add_argument("-dst", "--dest", type = str, default = ".")
        parser.add_argument("-chginfo", "--commit_chginfo_file", type = str, 
            help = "a file that contains commit changes information per modified file. \
                e.g., commit_changes/results/pulsar.commit_chgs.pf.pkl")
        parser.add_argument("-postfix", type = str, default = ".java")
        parser.add_argument("-renamed", "--file_renamed_file", type = str, default = None,
            help = "e.g., commit_changes/results/pulsar.rename_history.json")
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

    # entire_commits_infos -> key: commit, value: [author, time_of_commit]
    entire_commits_in_rev, entire_commits_infos  = utils.get_commit_infos_and_order(repo)
    # commits_to_inspect(dict): key = fix_commit, value: parent commit of the fix
    commits_to_inspect = utils.get_commits_to_inspect(
        args.target_data_file, full_project_name, entire_commits_in_rev)
    
    if args.file_renamed_file is None:
        recorded_renameds = None
    else:
        with open(args.file_renamed_file) as f:
            recorded_renameds = json.load(f)

    print ("--", args.commit_chginfo_file)
    with open(args.commit_chginfo_file, 'rb') as f: 
        import pickle
        commit_chginfo_per_file = pickle.load(f)

    dest = os.path.join(args.dest, project_name)
    for fix_commit, commit_to_inspect in tqdm(list(commits_to_inspect.items())):
        #print ("Commit : {} and parent is {}".format(fix_commit, commit_to_inspect))
        curr_dest = os.path.join(dest, fix_commit)
        os.makedirs(curr_dest, exist_ok=True)
        metric_file = os.path.join(curr_dest, 'ccm_metrics.pf.csv')
        if os.path.exists(metric_file): # skip for now
            print ("{} already exists. passing this one".format(metric_file))
            continue 

        print ("will be saved in {}".format(metric_file))
        resultdir_to_lookat = os.path.join(sbfl_result_dir, fix_commit)
        if not os.path.exists(resultdir_to_lookat):
            resultdir_to_lookat = utils.get_matching_dir(resultdir_to_lookat)
            if resultdir_to_lookat is None:# have checked. fine to do this
                print ("None!! {}".format(fix_commit))
                continue

        spectra_file_to_lookat = utils.find_file(resultdir_to_lookat, "spectra.csv")
        existing_files = get_src_files(
            spectra_file_to_lookat, repo, 
            commit_to_inspect, 
            postfix = args.postfix, project = project_name)
       
        commits_prior_to_and_is_target = utils.get_target_and_prev_commits(
            None, commit_to_inspect, entire_commits_in_rev = entire_commits_in_rev)

        print ("total {} number of commits to inpect".format(len(commits_prior_to_and_is_target)))
        print ("start combining...")
        metric_per_file = combine(commits_prior_to_and_is_target, 
            commit_chginfo_per_file, existing_files, entire_commits_infos, recorded_renameds)

        metric_per_file_df = convert_nested_dict_to_df(metric_per_file)
        print ("combine done!")
        metric_per_file_df.to_csv(metric_file)
    

if __name__ == "__main__":
    main()