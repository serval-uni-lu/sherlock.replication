import utils
import history
from tqdm import tqdm
import numpy as np

def read_modifieds_per_commit(changes_file):
    """
    """
    import json

    with open(changes_file) as f:
        changes = json.load(f)

    return changes

def read_files_and_authors(filename):
    """
    """
    import json
    with open(filename) as f:
        files_and_author_per_commit = json.load(f)

    return files_and_author_per_commit

def read_renamed(filename):
    """
    """
    import json
    with open(filename) as f:
        renamed = json.load(f)

    return renamed

def get_N(N, N_chunks):
    if N is not None and N > N_chunks - 1:
        if N > N_chunks - 1:
            return N_chunks - 1
    return N

def main(args = None, **kwargs):
    import argparse, os, git
    #import time
    import json

    if args is None:
        parser = argparse.ArgumentParser()
        parser.add_argument("-dest", type = str, default = "results",
            help = "path to the directory where collected code and change metrics are stored")
        parser.add_argument("-repo", type = str,
            help = "path to the git repository of the target project")
        parser.add_argument("-project", type = str,
            help = "a name of the target project")
        parser.add_argument("-postfix", type = str, default = ".java",
            help = "postfix of the target files")
        parser.add_argument("-changes_file", type = str, 
            help = "path to the file where a list of added, deleted, and modified lines\
            are stored per commit")
        parser.add_argument("-mode", type = int, default = 0,
            help = '0 if gathering all modified lines,\
            1 if recording modified files and author per commit,\
            2 if collecting file renamining informatio, \
            and 3 if normal metric collection mode')
        parser.add_argument("-files_and_authors_file", type = str,
            help = "a path to the file that stores a list of modified files\
            and author name per commit")
        parser.add_argument("-rename_hist_file", type = str,
            help = "a file that contain file rename history")
        #temporary due to memory erors 
        parser.add_argument("-N", type = int, default = None,
            help = "run on Nth chunks of commits. Here, the entire commits is divide into five chunks. \
                    if None, then all commits are processed together")

        args = parser.parse_args()

    if 'mode' in kwargs.keys():
        mode = kwargs['mode']
    else:
        mode = args.mode
    #if 'N_chunks' in kwargs.keys():
        #N_chunks = kwargs['N_chunks']
    #else:
        #N_chunks = 1

    g = git.Git(args.repo)
    os.makedirs(args.dest, exist_ok = True)
    if mode == 0: # collecting changes
        #print ("Collecting commit changes")
        entire_commits = utils.get_previous_commits(None, args.repo, g = g)
        # reset N_chunks
        #N = get_N(args.N, N_chunks)
        #commits_chunks = np.array_split(entire_commits, N_chunks)
        #target_commits_to_process = commits_chunks[N]

        # for each commit, the set of modified, added, deleted lines will be saved
        modifieds_per_commit = {}    
        lst_is_too_large = []; lst_is_wo_added = []; lst_is_both = []
        for commit in tqdm(entire_commits): #target_commits_to_process):
            is_commit_without_addedd_flag = utils.is_without_added(commit, args.repo, g = g, file_postfix = args.postfix)
            if is_commit_without_addedd_flag: # nothing added
                continue

            modifieds = utils.get_modified_lines(commit, args.repo, g = g, postfix = args.postfix)
            modifieds_per_commit[commit] = modifieds
        
        print ("{}/{}/{} out of {} is too large, without added line, and both".format(
            len(lst_is_too_large),
            len(lst_is_wo_added),
            len(lst_is_both),
            len(entire_commits)))
       
        #if N is None:
        mod_file = os.path.join(args.dest, "{}.changes.json".format(args.project))
        #else:
        #    mod_file = os.path.join(args.dest, "{}.changes.{}_{}.json".format(args.project, N, N_chunks))
        with open(mod_file, 'w') as f:
            f.write(json.dumps(modifieds_per_commit))

    elif mode == 1:
        # needed arguments: repo, project, dest & mode #
        # this is no-longer needed (was required for the review metrics)
        entire_commits = utils.get_previous_commits(None, args.repo, g = g)
        results = utils.record_modfied_files_and_author_per_commit(
            entire_commits, 
            args.repo, 
            g = g, 
            postfix = args.postfix)

        with open(os.path.join(args.dest, "%s.files.author.json" % args.project), 'w') as f:
            f.write(json.dumps(results))
    elif mode == 2: # collect all file rename in advance
        # needed arguments: project, dest, repo & mode #
        #print ("Collecting file renaming information")
        entire_commits = utils.get_previous_commits(None, args.repo, g = g)
    
        # key: commit where file rename happen, value: [renamed file, before rename]
        file_rename_history = {}
        current_commit = entire_commits[0]
        #N = get_N(args.N, N_chunks)
        #if N is not None:
            #commits_chunks = np.array_split(entire_commits, N_chunks)
            #target_commits_to_process = commits_chunks[N]
        #else:
            #target_commits_to_process = entire_commits[1:]

        for commit in tqdm(entire_commits): #target_commits_to_process):
            # renamed (dict)
            #     key: name of the modified & renamed file in target_commit, 
            #    value: the file name before the renaming
            renamed = utils.get_renamed_files(current_commit, 
                commit, 
                repo = args.repo, 
                g = g)
            if len(renamed) > 0:
                file_rename_history[current_commit] = renamed
            # update
            current_commit = commit
        
        #if args.N is None:
        destfile = os.path.join(args.dest, "{}.rename_history.json".format(args.project))
        #else:
        #    destfile = os.path.join(args.dest, "{}.rename_history.{}_{}.json".format(args.project, N, N_chunks))
        with open(destfile, 'w') as f:
            f.write(json.dumps(file_rename_history))

    else:# normal code and change metric collection mode
        #print ("Collecting metrics")
        if 'changes_file' in kwargs.keys():
            changes_file = kwargs['changes_file']
        else:
            changes_file = args.changes_file

        if 'files_and_authors_file' in kwargs.keys():
            files_and_authors_file = kwargs['files_and_authors_file']
        else:
            files_and_authors_file = args.files_and_authors_file  

        if 'rename_hist_file' in kwargs.keys():
            rename_hist_file = kwargs['rename_hist_file']
        else:
            rename_hist_file = args.rename_hist_file  
            
        modifieds_per_commit = read_modifieds_per_commit(changes_file)

        entire_commits_w_infos = utils.get_previous_commits(
            None, args.repo, g = g, with_author_and_date = True)
        entire_commits = [vs[0] for vs in entire_commits_w_infos]

        files_and_author_per_commit = read_files_and_authors(files_and_authors_file)
        file_renamed = read_renamed(rename_hist_file)
        hist_inst = history.History(args.repo, file_postfix = args.postfix)
        
        commits_to_inpect = list(modifieds_per_commit.keys())
        #N = get_N(args.N, N_chunks)
        #if N is not None:
            #commits_chunks = np.array_split(commits_to_inpect, N_chunks)
            #target_commits_to_process = commits_chunks[N]
        #else:
            #target_commits_to_process = commits_to_inpect

        #t1 = time.time()
        # collect metrics for each changes 
        metrics = {}
        for commit in tqdm(commits_to_inpect): #target_commits_to_process):
            modifieds = modifieds_per_commit[commit]
            # for closure, we need one more
            per_modified_file_metrics = {}
            # history metrics: 
            #    the number of past changes on the file, 
            #    the number of authors who participated in the modfication of the file
            commits_w_infos_in_range = entire_commits_w_infos[entire_commits.index(commit)+1:]
            commits_in_range = [vs[0] for vs in commits_w_infos_in_range]
            target_files = list(modifieds.keys())
            
            _, num_changes_per_file = hist_inst.num_unique_changes(commit, 
                target_files,
                file_renamed = file_renamed,  
                commits_in_range = commits_in_range,
                files_and_author_per_commit = files_and_author_per_commit)

            _, _, participated_authors_per_file = hist_inst.num_developers(commit, 
                target_files, 
                file_renamed = file_renamed, 
                commits_in_range = commits_in_range,
                files_and_author_per_commit = files_and_author_per_commit)
            
            authors_per_file = {afile:set(authors) for afile, authors in participated_authors_per_file.items()}
            per_modified_file_metrics['history'] = {
                'uniq_changes':num_changes_per_file, 'developers':authors_per_file} 

            # update metrics computed for current commit
            metrics[commit] = per_modified_file_metrics

        import pickle 
        #if args.N is None:
        destfile = os.path.join(args.dest, '{}.commit_chgs.pf.pkl'.format(args.project))
        #else:
        #    destfile = os.path.join(args.dest, '{}.commit_chgs.pf.{}_{}.pkl'.format(args.project, N, N_chunks))

        with open(destfile, 'wb') as f:
            pickle.dump(metrics, f)


if __name__ == "__main__":
    main()

