import os, sys 
import pandas as pd
from gp_model import GP_model
import numpy as np
import pickle

DATA_INFO = ['project', 'commit', 'coveredClass', 'coveredClassPath']
SBFL_METRICS = ['dstar', 'ochiai', 'tarantula', 'barinel']
FLACK_METRICS = ['sm_dates', 'sm_randoms', 'sm_io', 'sm_collections', 'sm_threads', 'sm_networks']
SIZE_METRICS = ['sm_lines', 'sm_doi', 'sm_cc']
CHANGE_METRICS = ['uniq_changes', 'developers', 'age']
LABEL = 'isSusFlaky'
# can be changed
METRICS = SBFL_METRICS + CHANGE_METRICS + SIZE_METRICS + FLACK_METRICS 
N_FOLDS = 10


def get_raw_data(datafile_or_dir, delimiter = ","):
    """
    """
    if os.path.isdir(datafile_or_dir):
        data_df = append_dataOfMultileProject(datafile_or_dir, delimiter = delimiter)
    else:
        data_df = pd.read_csv(datafile_or_dir, delimiter=delimiter)
    return data_df 


def divide_to_n_folds(datafile_or_dir, project, delimiter = ",", n_folds = 10, seed = 0):
    """
    """
    data_df = get_raw_data(datafile_or_dir, delimiter=delimiter)

    if project is not None:
        data_df = data_df.loc[data_df.project == project]

    faults = data_df.commit.unique()
    if n_folds > len(faults):
        n_folds = len(faults)

    np.random.seed(seed)
    np.random.shuffle(faults)

    data_folds = np.array_split(faults, n_folds)
    return data_folds 

def get_train_and_test(data_folds, test_fold_idx):
    """
    """
    if not isinstance(data_folds[test_fold_idx], list):
        test_targets = data_folds[test_fold_idx].tolist()
    else:
        test_targets = data_folds[test_fold_idx]
    #train_target = [data for idx,data_fold in enumerate(data_folds) if idx != test_fold_idx for data in data_fold]
    train_target = [data for idx,data_fold in data_folds.items() if idx != test_fold_idx for data in data_fold]
    return {'test':test_targets, 'train':train_target}


def append_dataOfMultileProject(datadir, delimiter = ","):
    """
    """
    import glob 
    projects = ['pulsar', 'ignite', 'hbase', 'alluxio', 'neo4j']
    
    data_df_for_all = None
    for project in projects:
        datafile = os.path.join(datadir, "{}.csv".format(project))
        df_per_project = pd.read_csv(datafile, delimiter = delimiter)
        if data_df_for_all is None:
            data_df_for_all = df_per_project
        else:
            data_df_for_all = data_df_for_all.append(df_per_project)
    
    return data_df_for_all


def get_data_per_fault(project, datafile_or_dir, target_faults = None, delimiter = ","):
    from sklearn.preprocessing import minmax_scale

    data_df = get_raw_data(datafile_or_dir, delimiter=delimiter)

    common_metrics = set(data_df.columns.values).intersection(set(METRICS))
    assert len(common_metrics - set(METRICS)) == 0, common_metrics - set(METRICS)
    data_df = data_df[DATA_INFO + METRICS + [LABEL]]
    if project is not None:
        data_df = data_df.loc[data_df.project == project]

    # change age to per day
    if 'age' in METRICS:
        data_df['age'] = data_df.age.apply(lambda v:v/(60*60*24)).values 
    
    data_per_fault = {}
    cands_per_fault = {}
    labels_per_fault = {}
    for commit, df in data_df.groupby('commit'):
        if target_faults is None or commit in target_faults:
            metric_arr = df[METRICS].values 
            data_per_fault[commit] = minmax_scale(metric_arr, axis = 0)
            cands_per_fault[commit] = df.coveredClass.values 
            labels_per_fault[commit] = df[LABEL].values

    return data_per_fault, cands_per_fault, labels_per_fault


def read_config(config_file):
    """
    config_file: contains args & their values
    """
    df = pd.read_csv(config_file)
    df = df.set_index('arg')
    return df


def train(project, mdl_algo, train_targets, datafile, config_file, dest, mdl_key, random_state = None):
    """
    project -> short_project_id
    """
    configs = None if config_file is None else read_config(config_file)

    if mdl_algo == 'gp':
        data_per_fault, cands_per_fault, labels_per_fault = get_data_per_fault(
            project, datafile, target_faults = train_targets, delimiter = ",")

        mdl_inst = GP_model(
		    METRICS,
		    maxTreeDepth = int(configs.value['maxTreeDepth']),
		    minTreeDepth = int(configs.value['minTreeDepth']), 
		    initMaxTreeDepth = int(configs.value['initMaxTreeDepth']), 
		    cxpb = configs.value['cxpb'], 
		    mutpb = configs.value['mutpb'], 
		    random_state = int(configs.value['random_state']) if random_state is None else random_state,
		    num_pop = int(configs.value['num_pop']),
		    ngen = int(configs.value['ngen']))
        
        best_model, logs = mdl_inst.run(data_per_fault, cands_per_fault, labels_per_fault, 
            gen_full = False, num_best = 1, tie_breaker = 'max')
        with open(os.path.join(dest, "{}.mdl".format(mdl_key)), 'w') as f:
            f.write(str(best_model) + "\n")

        with open(os.path.join(dest, "{}.log".format(mdl_key)), 'wb') as f:
            pickle.dump(logs, f)

        return best_model
    else:
        print ("{} not supported yet".format(mdl_algo))
        sys.exit()


def evaluate(project, mdl_algo, mdl, mdl_file, test_targets, datafile, dest, eval_k, saving = True):
    """
    """
    if mdl_algo == 'gp':
        if mdl is None and os.path.exists(mdl_file):
            with open(mdl_file) as f:
                outs = [line.strip() for line in f.readlines()]
                assert len(outs) == 1, mdl_file 
                mdl = outs[0]

        data_per_fault, cands_per_fault, labels_per_fault = get_data_per_fault(
            project, datafile, target_faults = test_targets, delimiter = ",", per_fault = True)

        if saving:
            os.makedirs(dest, exist_ok = True)
            for commit, data in data_per_fault.items():
                sps, ranks = GP_model.predict(mdl, METRICS, data, tie_breaker = 'max')
                cands = cands_per_fault[commit]
                labels = labels_per_fault[commit]

                pred_df = pd.DataFrame({'coveredClass':cands, 'sp_score':sps, 'sp_rank':ranks, 'isSusFlaky':labels})
                destfile = os.path.join(dest, "{}.{}.result.csv".format(commit, eval_k))
                pred_df.to_csv(destfile, index = False)
        
        # overall evaluation. fitness: avg rank of flaky classes
        fitness, _, _ = GP_model.evaluate_model(mdl, METRICS, data_per_fault, labels_per_fault, 
		    cands_per_fault = cands_per_fault, tie_breaker = 'max')
    else:
        print ("{} not supported yet".format(mdl_algo))
        sys.exit()
        return fitness


def read_mdl(mdl_algo, mdl_file):
    """
    """
    if mdl_algo == 'gp':
        with open(mdl_file) as f:
            outs = [line.strip() for line in f.readlines() if bool(line.strip())]
            assert len(outs) == 1, mdl_file 
        mdl = outs[0]
    else:
        print ("{} not supported yet".format(mdl_algo))
    return mdl


def select_mdl(project, mdl_algo, mdl_dir, datafile_or_dir, iter_num, data_folds):
    """
    """
    selected_mdls = {'fold':[], 'which':[], 'iter':[], 'mdlPath':[], 'fitness':[]}
    num_folds = len(data_folds)
    for fold_idx in range(num_folds):
        test_and_train_targets = get_train_and_test(data_folds, fold_idx)
        test_targets = test_and_train_targets['test']
        data_per_fault, _, labels_per_fault = get_data_per_fault(
            project, datafile_or_dir, target_faults = test_targets, delimiter = ",", per_fault = True)

        mdls_with_fitness = []
        for iter_idx in range(iter_num):
            mdl_file = os.path.join(mdl_dir, "best.{}.{}.mdl".format(fold_idx, iter_idx))
            mdl = read_mdl(mdl_algo, mdl_file)
            fitness, _, _ = GP_model.static_eval_func(
			    mdl, METRICS, data_per_fault, labels_per_fault, tie_breaker = 'max')

            mdls_with_fitness.append([iter_idx, mdl_file, fitness])
        
        sorted_mdls_with_fitness = sorted(mdls_with_fitness, key = lambda v:v[-1])
        # select the best
        best_mdl = sorted_mdls_with_fitness[0]
        selected_mdls['fold'].append(fold_idx)
        selected_mdls['which'].append('best')
        selected_mdls['iter'].append(best_mdl[0])
        selected_mdls['mdlPath'].append(best_mdl[1])
        selected_mdls['fitness'].append(best_mdl[2])

        # select the median 
        med_mdl = sorted_mdls_with_fitness[int(iter_num/2)]
        selected_mdls['fold'].append(fold_idx)
        selected_mdls['which'].append('med')
        selected_mdls['iter'].append(med_mdl[0])
        selected_mdls['mdlPath'].append(med_mdl[1])
        selected_mdls['fitness'].append(med_mdl[2])

    selected_mdls = pd.DataFrame(selected_mdls)
    return selected_mdls

def get_data_folds(fold_info_file):
    """
    """
    data_folds_df = pd.read_csv(fold_info_file, delimiter='\t')
    data_folds = {int(test_fold_idx):commits.split(",") for test_fold_idx,commits in data_folds_df.values}
    return data_folds 


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-dst', '--dest', type = str)
    parser.add_argument('-data', '--datafile_or_dir', type = str, 
        help = "a metric data file that contains metrics and labels per class")
    parser.add_argument("-algo", '--mdl_algo', type = str, default = 'gp', 
        help = "learn to rank algorithm")  
    parser.add_argument("-config", "--config_file", type = str)
    # this argument will be not used as we do not train a model within project
    parser.add_argument("-p", "--project", type = str, default = None, help = "e.g., hbase")
    parser.add_argument("-key", type = str, default = "best") # model key
    parser.add_argument("-fold", "--fold_info_file", type = str, default = "results/data_folds.tsv",
        help = "contains information of for each fold of ten-fold cross-val")
    parser.add_argument("-train", action = 'store_true')
    parser.add_argument("-test", action = 'store_true')
    parser.add_argument("-start", type = int, default = 0)
    parser.add_argument("-end", type = int, default = -1)
    parser.add_argument("-mode", type = int, default = 0)

    args = parser.parse_args()

    dest = os.path.join(args.dest, args.mdl_algo)
    os.makedirs(dest, exist_ok=True)
    assert args.train or args.test, "at least, either train or test should be given"

    if args.mode == 0:
        # only sbfl
        METRICS = SBFL_METRICS
        dest = os.path.join(dest, 'sbfl')
        os.makedirs(dest, exist_ok=True)
    elif args.mode == 1:
        # sbfl & change
        METRICS = SBFL_METRICS + CHANGE_METRICS
        dest = os.path.join(dest, 'sbfl_chg')
        os.makedirs(dest, exist_ok=True)
    elif args.mode == 2:
        # sbfl & size
        METRICS = SBFL_METRICS + SIZE_METRICS 
        dest = os.path.join(dest, 'sbfl_size')
        os.makedirs(dest, exist_ok=True)
    elif args.mode == 3:
        # sblf & flaky
        METRICS = SBFL_METRICS + FLACK_METRICS 
        dest = os.path.join(dest, 'sbfl_flaky')
        os.makedirs(dest, exist_ok=True)
    else:
        print ("{} not supported".format(args.mode))
        sys.exit()

    data_folds = get_data_folds(args.fold_info_file)
    start = args.start
    end = 30 if args.end < 0 else args.end
    for test_fold_idx in range(len(data_folds)):
        print ("\n====================================================================================")
        print ("================================== In fold {} =======================================".format(test_fold_idx))
        print ("====================================================================================\n")
        test_and_train_targets = get_train_and_test(data_folds, test_fold_idx)
        test_targets = test_and_train_targets['test']
        train_targets = test_and_train_targets['train']
        #print ("Number of test: {} and train: {}".format(len(test_targets), len(train_targets)))

        for iter_idx in range(start, end):
            if args.train:
                best_mdl = train(args.project, args.mdl_algo, train_targets, args.datafile_or_dir, args.config_file, 
                    dest, "{}.{}.{}".format(args.key, test_fold_idx, iter_idx), random_state = iter_idx)
            else:
                best_mdl = None 

            if args.test:
                mdl_file = os.path.join(dest, "{}.mdl".format("{}.{}.{}".format(args.key, test_fold_idx, iter_idx)))
                _ = evaluate(args.project, args.mdl_algo, best_mdl, mdl_file, test_targets, args.datafile_or_dir, dest, '{}.test'.format(iter_idx))
                print ("\n=====================================TRAIN===========================================\n")
                _ = evaluate(args.project, args.mdl_algo, best_mdl, mdl_file, train_targets, args.datafile_or_dir, dest, '{}.train'.format(iter_idx))


if __name__ == "__main__":
    main()