import os
import json
import argparse
from tqdm import tqdm

def main(args = None, which = None, N_chunks = 10):
    if args is None:
        parser = argparse.ArgumentParser()
        parser.add_argument("-dest", type = str, default = "output")
        parser.add_argument("-which", type = str, default = "rename")
        parser.add_argument("-project", type = str, default = None, 
            help = "name of project. e.g., neo4j")

        args = parser.parse_args()
    
    if which is None:
        which = args.which 

    if which == 'rename':
        combined = None
        for idx in range(N_chunks):
            file_to_append = os.path.join(args.dest, 
                "{}.rename_history.{}_{}.json".format(args.project,idx, N_chunks))
            print (file_to_append)
            with open(file_to_append) as f:
                renameds = json.load(f)
            if combined is None:
                combined = renameds
            else:
                combined.update(renameds)

        destfile = os.path.join(args.dest, "{}.rename_history.json".format(args.project))
        with open(destfile, 'w') as f:
            f.write(json.dumps(combined))
    elif which == 'ccm':
        import pickle 
        combined = None
        for idx in tqdm(range(N_chunks)):
            file_to_append = os.path.join(args.dest, 
                "commit_chgs.pf.{}_{}.pkl".format(args.project, idx, N_chunks))
            with open(file_to_append, 'rb') as f:
                data = pickle.load(f)

            if combined is None:
                combined = data
            else:
                combined.update(data)

        destfile = os.path.join(args.dest, "{}.ccms.pf.wo_age.pkl".format(args.project))
        with open(destfile, 'wb') as f:
            pickle.dump(combined, f)
    else: # changes
        combined = None
        for idx in range(N_chunks):
            file_to_append = os.path.join(args.dest, 
                "{}.changes.{}_{}.json".format(args.project, idx, N_chunks))
            with open(file_to_append) as f:
                chgs = json.load(f)

            if combined is None:
                combined = chgs
            else:
                combined.update(chgs)

        destfile = os.path.join(args.dest, "{}.changes.json".format(args.project))
        with open(destfile, 'w') as f:
            f.write(json.dumps(combined))

if __name__ == "__main__":
    main()

