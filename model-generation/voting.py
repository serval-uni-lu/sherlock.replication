"""
voting between SBFL
"""
import numpy as np 


def vote_on_top_n(ranks_df, top_n, elemnt_column = 'name', rank_column = 'rank', with_weight = False):
    """
    cast votes to the top_n elements
    """
    indices_to_voted = ranks_df.loc[ranks_df[rank_column] <= top_n].index.values
    voted_cands = ranks_df[elemnt_column][indices_to_voted].values
    ranks_of_voted = ranks_df[rank_column][indices_to_voted].values
    number_of_votes = [1] * len(indices_to_voted) if not with_weight else 1/ranks_of_voted
    cands = {cand:number_of_votes[i] for i,cand in enumerate(voted_cands)}

    if len(indices_to_voted) < top_n:
        next_best_rank = np.min(ranks_df.loc[ranks_df[rank_column] > top_n][rank_column].values)
        cand_indices_to_add_voted = ranks_df.loc[ranks_df[rank_column] == next_best_rank].index.values 
        add_voted_cands = ranks_df[elemnt_column][cand_indices_to_add_voted].values
        
        n_add_cand = len(add_voted_cands)
        number_of_votes = [1/n_add_cand] * n_add_cand if not with_weight else [1/(next_best_rank * n_add_cand)]*n_add_cand
        cands.update({cand:number_of_votes[i] for i,cand in enumerate(add_voted_cands)})
    #return {cand:[indices_to_voted[i], number_of_votes[i]] for i,cand in enumerate(voted_cands)}
    #return {cand:number_of_votes[i] for i,cand in enumerate(voted_cands)}
    return cands 

def vote_on_above_susp(susps_df, susp_threshold, 
    elemnt_column = 'name', susp_score_column = 'suspiciousness_value', with_weight = False):
    """
    cast votes to the top_n elements
    ranks -> dataframe of name & rank
    """
    indices_to_voted = susps_df.loc[susps_df[susp_score_column] > susp_threshold].index.values
    voted_cands = susps_df[elemnt_column][indices_to_voted].values
    susps_of_voted = susps_df[susp_score_column][indices_to_voted].values
    # normalise between 0 to 1
    all_susps = susps_df[susp_score_column].values
    min_susp = np.min(all_susps); max_susp = np.max(all_susps)
    normed_susps_of_voted = (susps_of_voted - min_susp)/(max_susp - min_susp)

    number_of_votes = [1] * len(indices_to_voted) if not with_weight else normed_susps_of_voted
    #return {cand:[indices_to_voted[i], number_of_votes[i]] for i,cand in enumerate(voted_cands)}
    return {cand:number_of_votes[i] for i,cand in enumerate(voted_cands)}
