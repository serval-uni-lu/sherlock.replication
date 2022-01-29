"""
Utility functions file
"""
import git 
import process 
import pandas as pd

def get_previous_commits(repo, commit = None, before_date = None):
    """
    return a list of commits before a given commit
    """
    g = git.Git(repo)

    entire_commits = {'commits':[], 'unix_ts':[]} #[] # will be the latest to the oldest
    if before_date is None:
        loginfo = g.log("--pretty=oneline", "-w", "--pretty=%H %at")
    else:
        loginfo = g.log("--pretty=oneline", "-w", '--before=\"{}\"'.format(before_date), "--pretty=%H %at") # e.g., 2015-7-3

    for logline in loginfo.split("\n"):
        _commit, unix_ts = logline.split(" ")
        entire_commits['commits'].append(_commit)
        entire_commits['unix_ts'].append(int(unix_ts))

    if commit is not None:
        idx_to_target_commit = entire_commits['commits'].index(commit)
        commits_in_range = entire_commits['commits'][idx_to_target_commit+1:]
        matching_unix_ts = entire_commits['unix_ts'][idx_to_target_commit+1:]
    else:
        commits_in_range = entire_commits['commits']
        matching_unix_ts = entire_commits['unix_ts']

    return commits_in_range, matching_unix_ts


def list_existing_files(commit, repo, postfix = ".java"):
    """
    """
    import subprocess
    import os
    cwd = os.getcwd()
    os.chdir(repo)

    cmd = "git ls-tree --name-only -r %s" % (commit)
    result = subprocess.run([cmd], stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
    files = result.stdout.decode('ascii').split("\n")
    if postfix is None:
        target_files = files
    else:
        target_files = [file for file in files if file.endswith(postfix)]
    os.chdir(cwd)
    return target_files


def get_renamed_files(target_commit, 
    comp_commit,
    file_rename_history = None, 
    repo = None, 
    g = None):
    """
    """
    if file_rename_history is None and g is None:
        assert repo is not None
        g = git.Git(repo)

    if file_rename_history is None:
        diffinfo = g.diff("--name-status", "-M95", target_commit, comp_commit)
        diff_lines = [line for line in diffinfo.split("\n") if bool(line.strip())]
        renamed = {}
        for diff_line in diff_lines:
            if diff_line.startswith("R") or diff_line.startswith("C"): # rename-edit
                target_file, comp_file = diff_line.split("\t")[1:]
                renamed[target_file] = comp_file
    else:
        if target_commit in file_rename_history.keys():
            renamed = file_rename_history[target_commit]
        else:
            renamed = {}

    return renamed


def update_renamed_files(file_rename_history, renamed):
    """
    file_rename_history: key = initial file, value: a history of file-rename (list)
    renamed: 
        key: initial file, value: renamed-to-file
    """
    # update file_rename_history
    for target_file, renamed_history in file_rename_history.items():
        # the target_file has been renamed -> update
        if renamed_history[-1] in renamed.keys():
            file_rename_history[target_file].append(renamed[renamed_history[-1]])

    return file_rename_history


def get_list_of_existing_files(target_commit, repo, postfix = ".java"):
    """
    return a list of existing files in target_commit of a project cloned in repo
    """
    existing_files = list_existing_files(target_commit, repo, postfix = postfix)
    return existing_files

def get_commit_infos_and_order(repo, only_ordered_commit = False):
    """
    return a list of all commits in reverse order: from the latest to the oldest
    """
    if only_ordered_commit:
        entire_commits_in_rev, _  = get_previous_commits(repo)
        return entire_commits_in_rev
    else:
        import commit_changes.utils as commit_change_utils
        entire_commits_in_rev_info = commit_change_utils.get_previous_commits(None, repo, with_author_and_date = True, parse_date = True)
        # to keep the order
        entire_commits_in_rev = [commit_info[0] for commit_info in entire_commits_in_rev_info] 
        entire_commits_infos = {commit_info[0]:commit_info[1:3] for commit_info in entire_commits_in_rev_info} 
        return entire_commits_in_rev, entire_commits_infos

def get_target_and_prev_commits(repo, target_commit, entire_commits_in_rev = None):
    """
    return a list of commits that includes both commits prior to the target and the target itself.
    Sorted in the reverse order.  
    """
    if entire_commits_in_rev is None:
        entire_commits_in_rev, _ = get_commit_infos_and_order(repo, only_ordered_commit = True)
        
    idx_to_target = entire_commits_in_rev.index(target_commit) if target_commit is not None else 0
    return entire_commits_in_rev[idx_to_target:]


def get_targets(datafile, project_name, ret_all = False, w_gt = False):
    """
    datafile: stores a dataframe that contains all information about the target (the spreadsheet file)
    colums: (['Name', 'Commit', 'GitHub URL', 'Parent commit', 'Test Name', 'Date',
       'Modyfing', 'Unnamed: 7', 'Comments', 'Module suspected to be flaky',
       'Line rank', 'Method rank', 'Class rank'],
      dtype='object')
    """
    df = pd.read_csv(datafile, delimiter = '\t').dropna(subset = ['Class rank']) 
    ret_dfs = {}
    if project_name is not None:
        df = df.loc[df.Name == project_name].dropna(subset = ['Module suspected to be flaky'])
        if not w_gt:
            ret_dfs[project_name] = df[
                ['Commit', 'Parent commit']] if not ret_all else df
        else:
            ret_dfs[project_name] = df[
                ['Commit', 'Parent commit', 'Module suspected to be flaky']] if not ret_all else df
    else:
        project_names = df.Name.unique()
        for project_name in project_names:
            p_df = df.loc[df.Name == project_name].dropna(subset = ['Module suspected to be flaky'])
            if not w_gt:
                ret_dfs[project_name] = p_df[[
                    'Commit', 'Parent commit']] if not ret_all else p_df
            else:
                ret_dfs[project_name] = p_df[
                    ['Commit', 'Parent commit', 'Module suspected to be flaky']] if not ret_all else p_df
    return ret_dfs

def change_commit_id_to_full(commits, ref_commits):
    """
    """
    full_commits = []
    for commit in commits:
        full_commit = None
        for ref_commit in ref_commits:
            if ref_commit.startswith(commit):
                full_commit = ref_commit 
                break 
        assert full_commit is not None, commit 
        full_commits.append(full_commit)
    return full_commits


def get_matching_dir(pattern):
    """
    """
    import os, glob
    parent_dir = os.path.dirname(pattern)
    for adir in glob.glob(parent_dir + "/*"):
        # because, sometime the directory doesn't use full commit id
        if adir in pattern: 
            return adir 
    return None

def get_commits_to_inspect(target_data_file, project_name, commits_within_range):
    """
    commits_within_range: must cover all the target. sorted in reverse order
    """
    target_df = get_targets(target_data_file, project_name)[project_name]
    num_targets = len(target_df)

    commits_to_inspect = {}
    for i in range(num_targets):
        row = target_df.iloc[i]     
        parent_commit = row['Parent commit']
        fix_commit = row['Commit']
        fix_commit = change_commit_id_to_full([fix_commit], commits_within_range)[0]
        if pd.isnull(parent_commit): 
            idx_to_fix_commit = commits_within_range.index(fix_commit)
            parent_commit = commits_within_range[idx_to_fix_commit+1]
        else:
            parent_commit = change_commit_id_to_full([parent_commit], commits_within_range)[0]     

        if fix_commit[:8] == 'a5b86dd7': # we will skip this one
            continue  
        commits_to_inspect[fix_commit] = parent_commit

    return commits_to_inspect


def find_file(resultdir, file_basename):
    """
    e.g., file_basename: spectra.csv.
    This one actually coveres get_spectra_files from combine_metircs. -> extract all the functions that
    can be categorised under utility and generate a utility file
    """
    import os
    files_found = []
    for subdir, dirs, files in os.walk(resultdir):
        for file in files:
            if file == file_basename:
                files_found.append(os.path.join(subdir, file))
    
    assert len(files_found) > 0, resultdir 
    if len(files_found) > 1:
        filtered = list(filter(lambda path: 'method' not in path, files_found))
        #assert len(filtered) == 1, filtered
        file_found = filtered[0] # ok to choose the first one. repeated ones will be filtered later
    else:
        file_found = files_found[0]
    return file_found