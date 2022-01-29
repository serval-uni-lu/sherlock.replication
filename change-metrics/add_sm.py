"""
Add static metrics to chg & sbfl metrics, and 
generate the final metric data file for the model learning
"""
import pandas as pd
pd.options.mode.chained_assignment = None 
import numpy as np
import os 

SM_METRICS = ['sm_dates', 'sm_randoms', 'sm_io', 'sm_collections', 'sm_threads',
       'sm_networks', 'sm_lines', 'sm_doi', 'sm_cc']
COLUMNS = ['project', 'commit', 'coveredClass', 'outerClass', 'coveredClassPath'] \
         + ['dstar', 'ochiai', 'tarantula', 'barinel'] + SM_METRICS \
         + ['uniq_changes', 'developers', 'age'] + ['isSusFlaky']  

def get_outer_class(class_id):
    outer_class = '$'.join(class_id.split('$')[:2])
    return outer_class

def combine(sm_file, sbfl_chg_m_file):
    sm_df = pd.read_csv(sm_file)
    sbfl_chg_df = pd.read_csv(sbfl_chg_m_file)
    commits = set(list(sm_df.commit.values))
    final_df = None
    for commit in commits:
        sm_df_pcommit = sm_df.loc[sm_df.commit == commit]
        sbfl_chg_df_pcommit = sbfl_chg_df.loc[sbfl_chg_df.commit == commit]
        sbfl_chg_df_pcommit['outerClass'] = sbfl_chg_df_pcommit.coveredClass.apply(get_outer_class).values
        
        num = len(sbfl_chg_df_pcommit)
        matching_sm_metrics = []
        for i in range(num):
            curr_outer_class = sbfl_chg_df_pcommit.iloc[i].outerClass
            matching_sms = sm_df_pcommit.loc[sm_df_pcommit.coveredClass == curr_outer_class][SM_METRICS]
            if len(matching_sms) == 0: # no match
                matching_sm_metrics.append([0] * len(SM_METRICS)) # assuming, we cannot compute anything at all
            else:
                assert len(matching_sms) == 1, matching_sms
                matching_sm_metrics.append(matching_sms.values[0])
        
        matching_sm_metrics = np.array(matching_sm_metrics)
        if len(matching_sm_metrics) == 0: # for pulsar 
            continue
        else:
            for i,sm_metric_name in enumerate(SM_METRICS):
                sbfl_chg_df_pcommit[sm_metric_name] = matching_sm_metrics[:,i]

        if final_df is None:
            final_df = sbfl_chg_df_pcommit
        else:
            final_df = final_df.append(sbfl_chg_df_pcommit)
        
    final_df = final_df[COLUMNS] # columns reordering
    return final_df


def main(dest, cm_sbfl_file, sm_file, project_name):
    os.makedirs(dest, exist_ok=True)
    combined_df = combine(sm_file, cm_sbfl_file)
    combined_df.to_csv(os.path.join(dest, "{}.csv".format(project_name)), index = False)


if __name__ == "__main__":
    import argparse
   
    parser = argparse.ArgumentParser()
    parser.add_argument("-dst", "--dest", type = str, default = "results")
    parser.add_argument("-cm_sbfl", "--cm_sbfl_file", type = str, default = "results")
    parser.add_argument("-sm", "--sm_file", type = str, default = "../static-metrics/analysis/results/")
    parser.add_argument("-project", "--project_name", type = str, default = None, help = "e.g., pulsar")
    
    args = parser.parse_args()
    
    main(args.dest, args.cm_sbfl_file, args.sm_file, args.project_name)