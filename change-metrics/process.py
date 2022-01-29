"""
read and process SBFL results from gzoltar
"""
import numpy as np
import pandas as pd

def read_coverage_matrix(file):
    """
    matrix.txt: 
        the coverage matrix where rows represent tests and columns the components (1ij = component j covered by test i , 0ij = not covered)
    """
    covgs = []
    with open(file) as f:
        for line in f.readlines():
            line = line.strip()
            if bool(line):
                covg = [v for v in line.split(" ") if v.isdigit()]
                covgs.append(covg)
    
    covg_arr = np.float32(np.array(covgs))
    return covg_arr 

def read_susps(file):
    """
    {dstar,barine,ochiail,tarantula}.ranking.csv:
        contains each component scores ranked according to the scores
    """
    # columns: name, suspiciousness_value
    #   name: file_id, lno
    #       e.g., org.apache.hadoop.hbase.master.procedure$ServerCrashException:38
    #   suspiciousness_value -> are these values normalised?
    susps = pd.read_csv(file, sep = ";")
    return susps

def read_elements(file):
    """
    spectra.csv:
        a list of all components (i.e. lines,classes or methods) identified of all instrumented classes
    """
    elements_df = pd.read_csv(file, sep = ":").reset_index()
    elements_df = elements_df.rename(columns={'index':'path', 'name':'lno'})
    return elements_df

def read_statistics(file):
    """
    statistics.csv:
        a set of metrics extracted (i.e. matrix density, component ambiguity score, and entropy) for each formulas
    """
    return pd.read_csv(file)


def read_tests(file):
    """
    tests.csv:
        list of all test cases identified
    
    headers: name,outcome,runtime,stacktrace
    e.g., org.apache.hadoop.hbase.coprocessor.TestCoprocessorMetrics#testRegionObserverMultiCoprocessor,PASS,2306421475, 
    (no execution trace here ...)
    """
    test_infos = {}
    with open(file) as f:
        headers = [line.strip() for line in f.readline().split(",")]
        test_infos = {header:[] for header in headers}
        for line in f.readlines():
            line = line.strip()
            if bool(line):
                ts = line.split(",")
                #test_infos[headers[-1]].append(ts[-1])
                #test_infos[headers[-2]].append(ts[-2])
                #test_infos[headers[-3]].append(ts[-3])
                #test_name = ",".join(ts[:-3])
                #test_infos[headers[-4]].append(test_name)
                test_name = ts[0]
                test_infos[headers[0]].append(ts[0])
                test_infos[headers[1]].append(ts[1])
                test_infos[headers[2]].append(ts[2])
                test_infos[headers[3]].append(",".join(ts[3:]))

    
    return pd.DataFrame(test_infos)
  

def get_parent_commit(target_commit, commits_in_rev, unix_time_stamps = None):
    """
    .... thinking again ... it might be possible that this commit may not be pushed into the master(main) branch ...
    => then, retrieve the most recent one
    """
    if target_commit in commits_in_rev:
        idx = commits_in_rev.index(target_commit)
        if idx == len(commits_in_rev) - 1: # the first commit
            print ("This ({}) is the first commit, so, there is no parent commit for this".format(target_commit))
            import sys; sys.exit()
        return commits_in_rev[idx-1]
    else: # compare the time stamps
        assert unix_time_stamps is not None
        print ('not yet')
    


