import collect_commit_changes_info
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("-dest", type = str,
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
#parser.add_argument("-N", type = int, default = None,
#    help = "run on Nth chunks of commits. Here, the entire commits is divide into five chunks. \
#            if None, then all commits are processed together")

args = parser.parse_args()

#N_chunks = 10
# collect changes 
collect_commit_changes_info.main(args, mode = 0)#, N_chunks = N_chunks)
print ("target commits & changes collected!")
#if args.N is not None:
    #import aggregate
    #print ("aggregation start") 
    #aggregate.main(args, which = 'change', N_chunks = N_chunks)    

# collect authors 
collect_commit_changes_info.main(args, mode = 1)
print ("commit authors collected!")

# collect file renaming
collect_commit_changes_info.main(args, mode = 2)
print ("file renaming collected!")
#if args.N is not None:
    #import aggregate
    #print ("aggregation start") 
    #aggregate.main(args, which = 'rename', N_chunks = N_chunks)   

# collect change metrics for each commit
changes_file = os.path.join(args.dest, "{}.changes.json".format(args.project))
files_and_authors_file = os.path.join(args.dest, "{}.files.author.json".format(args.project))
rename_hist_file = os.path.join(args.dest, "{}.rename_history.json".format(args.project))
collect_commit_changes_info.main(
    args, mode = 3, 
    changes_file = changes_file,
    files_and_authors_file = files_and_authors_file,
    rename_hist_file = rename_hist_file)

print ("change metrics per commit collected!")
#if args.N is not None:
    #import aggregate
    #print ("aggregation start") 
    #aggregate.main(args, which = 'ccm', N_chunks = N_chunks)    