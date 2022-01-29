import os
import numpy as np
import pandas as pd 
from main_learn2rank import get_data_folds
import voting
from tqdm import tqdm
from scipy.stats import rankdata
import glob

def vote_for_top_n(result_dfs_from_multi_mdls, with_weight = False, vote_type = 'rank', **kwargs):
    """
    result_dfs_from_multi_mdls:
        a list of result dataframes (columns: coveredClass,sp_score,sp_rank,isSusFlaky)
    with_weight:
        False -> equally 1 vote to every candidate (within top_n)
        True -> 1/rank vote 
    """
    assert vote_type in ['rank', 'susp'], vote_type

    aggregated_votes = None
    for result_df in result_dfs_from_multi_mdls:
        # voted_cands (dict): key = coveredClass, value: the number of votes
        if vote_type == 'rank':
            voted_cands = voting.vote_on_top_n(result_df, kwargs['top_n'], 
                elemnt_column = 'coveredClass', rank_column = 'sp_rank', with_weight = with_weight)
        else:
            voted_cands = voting.vote_on_above_susp(result_df, kwargs['sp_threshold'], 
                elemnt_column = 'coveredClass', susp_score_column = 'sp_score', with_weight = with_weight)
        # aggregate
        if aggregated_votes is None:
            aggregated_votes = voted_cands
        else:
            for cand, n_vote in voted_cands.items():
                try:
                    aggregated_votes[cand] += n_vote
                except Exception:
                    aggregated_votes[cand] = n_vote
    
    # ranking
    voted_cands = list(aggregated_votes.keys())
    votes_per_cand = [-np.array(aggregated_votes[cand]) for cand in voted_cands]
    cand_ranks = rankdata(votes_per_cand, method = 'max')
    ranks_from_voting = {cand:rank for cand,rank in zip(voted_cands, cand_ranks)}
    return aggregated_votes, ranks_from_voting


def get_approx_rank_of_flaky_classes(result_dfs_from_multi_mdls, method = 'mean'):
    """
    (per flaky commit)
    return either the average or the median of ranks from individual models.
    """
    ranks_from_mdl = []
    for result_df in result_dfs_from_multi_mdls:
        indices_to_flaky = np.where(result_df.isSusFlaky.values == 1)[0]
        ranks = result_df.sp_rank[indices_to_flaky].values
        ranks_from_mdl.append(np.min(ranks)) # among multiple flaky classes, pick the best
    
    return eval("np.{}(ranks_from_mdl)".format(method))


def get_final_rank(flaky_classes, ranks_from_voting, approx_rank):
    """
    if flaky_class has failed to receive any vote, return approx_rank
    """
    computed_ranks = {}
    cnt_v = 0; cnt_approx = 0
    from_v = []; from_approx = []
    for idx, flaky_class in enumerate(flaky_classes):
        try:
            computed_rank = ranks_from_voting[flaky_class]
            cnt_v += 1
            from_v.append(idx)
        except Exception: # none voted 
            computed_rank = approx_rank
            cnt_approx += 1
            from_approx.append(idx)

        computed_ranks[flaky_class] = computed_rank
    best_rank = np.min(list(computed_ranks.values()))
    indices = np.where(np.array(list(computed_ranks.values())) == best_rank)[0]
    is_in = int(len(np.setdiff1d(np.array(from_v), indices)) > 0)
    return computed_ranks, is_in

def get_files(result_dir, commit):
    """
    """
    ret = []
    for m in ['sbfl_chg', 'sbfl_size']: #, 'sbfl_flaky']:
        result_file_pat = os.path.join(result_dir, "{}/{}.[0-9]*.test.result.csv".format(m, commit))
        ret.extend(list(glob.glob(result_file_pat)))
    return ret

def vote(commits_to_inspect, result_dir, 
    vote_type, is_weighted, top_n, sp_threshold):
    """
    """
    is_voted_cnt =0; rs_for_voted = []
    final_ranks_pcommit = {}
    for commit in tqdm(commits_to_inspect):
        result_dfs_from_multi_mdls = []
        for result_file in get_files(result_dir, commit):
            df = pd.read_csv(result_file)
            # scale to be within 0 ~ 1
            from sklearn.preprocessing import minmax_scale
            df['sp_score'] = minmax_scale(df.sp_score.values, axis = 0)
            result_dfs_from_multi_mdls.append(df)

        if vote_type == 'rank': ## 
            if top_n < 0 or top_n > len(result_dfs_from_multi_mdls[0]):
                top_n = len(result_dfs_from_multi_mdls[0])
                is_weighted = True

            _, ranks_from_voting = vote_for_top_n(
                result_dfs_from_multi_mdls, with_weight = is_weighted, vote_type = 'rank', top_n  = top_n)
        else:
            _, ranks_from_voting = vote_for_top_n(
                result_dfs_from_multi_mdls, with_weight = is_weighted, vote_type = 'susp', sp_threshold  = sp_threshold)

        approx_rank = get_approx_rank_of_flaky_classes(result_dfs_from_multi_mdls, method = 'median')
        indices_to_flaky = np.where(result_dfs_from_multi_mdls[0].isSusFlaky.values == 1)[0]
        flaky_classes = result_dfs_from_multi_mdls[0].coveredClass[indices_to_flaky].values
        final_ranks_of_flaky_classes, is_voted = get_final_rank(flaky_classes, ranks_from_voting, approx_rank)
        is_voted_cnt += is_voted
        final_ranks_pcommit[commit] = np.min(list(final_ranks_of_flaky_classes.values()))
        if bool(is_voted):
            rs_for_voted.append(final_ranks_pcommit[commit])
        
    #for n in [1,3,5,10]:
    #    print ("acc@{}: {}".format(n, np.sum(np.array(rs_for_voted) <= n)))
    return final_ranks_pcommit


def main():
    import argparse
    import csv

    parser = argparse.ArgumentParser()
    parser.add_argument('-dst', '--dest', type = str)
    parser.add_argument('-result', '--result_dir', type = str, 
        help = "a metric data file that contains metrics and labels per class")
    parser.add_argument("-p", "--project", type = str, default = None, help = "e.g., hbase")
    parser.add_argument("-key", type = str, default = "best")
    parser.add_argument("-fold", "--fold_info_file", type = str, default = None,
        help = "contain information of data folds")
    parser.add_argument("-vote", "--vote_type", default = 'rank', 
        help = "either rank or susp")
    parser.add_argument("-weighted", action = "store_true")
    parser.add_argument("-top_n", type = int, default = 10)
    parser.add_argument("-threshold", "--sp_threshold", type = float, default = 0.7)
    
    args = parser.parse_args()

    data_folds = get_data_folds(args.fold_info_file)
    commits_to_inspect = [commit for data_fold in data_folds.values() for commit in data_fold]
    is_weighted = args.weighted
    top_n = args.top_n 
    sp_threshold = args.sp_threshold

    final_ranks_pcommit = vote(commits_to_inspect, args.result_dir, args.vote_type, is_weighted, top_n, sp_threshold)

    dest = os.path.join(args.dest, 'vote')
    os.makedirs(dest, exist_ok=True)
    top_n = args.top_n if args.top_n > 0 else "all"
    k = "{}.{}".format(args.vote_type, top_n if args.vote_type == 'rank' else args.sp_threshold)
    k += ".weighted" if args.weighted else ".not_weighted"

    destfile = os.path.join(dest, "voting.{}.csv".format(k))
    print ("saved in {}".format(destfile))

    with open(destfile, 'w') as f:
        csvWriter = csv.writer(f, delimiter = ",")
        results_to_record = list(final_ranks_pcommit.items())
        csvWriter.writerow(['commit', 'sp_rank'])
        csvWriter.writerows(results_to_record)


if __name__ == "__main__":
    main()