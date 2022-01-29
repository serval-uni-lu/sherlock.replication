"""
DDU: Diversity Density Uniquness 
"""
import numpy as np
import sys, os
sys.path.insert(0, "../change-metrics")
import utils, process 
from tqdm import tqdm
import time

def gen_coverage_matrix_secure(covg_matrix_file, testlst_file, spectra_file):
    """
    coverage_matrix -> |T| X |E|
    """
    coverage_matrix = process.read_coverage_matrix(covg_matrix_file)
    tests = process.read_tests(testlst_file).name.values
    elements = process.read_elements(spectra_file).path.values
    N_tests, N_elements = coverage_matrix.shape
    assert N_tests == len(tests), "{} vs {}".format(N_tests, len(tests))
    assert N_elements == len(elements), "{} vs {}".format(N_elements, len(elements))
    
    # the elemnent can be in other granularity rather than in class
    uniq_tests = np.unique(tests)
    covg_per_class = {}
    if len(tests) == len(uniq_tests):
        # the elemnent can be in other granularity rather than in class
        for i in range(N_elements):
            class_of_element = elements[i].split("#")[0]
            try:
                covg_per_class[class_of_element] += coverage_matrix[:,i]
            except Exception:
                covg_per_class[class_of_element] = coverage_matrix[:,i]
    else:### hahahahahah
        indices_to_each_uniq_test = {uniq_test:[] for uniq_test in uniq_tests}
        for test_idx, test in enumerate(tests):
            indices_to_each_uniq_test[test].append(test_idx)

        for i in range(N_elements):
            class_of_element = elements[i].split("#")[0]
            try:
                _ = covg_per_class[class_of_element]
            except Exception:
                covg_per_class[class_of_element] = np.zeros(len(uniq_tests))

            for j, test in enumerate(uniq_tests):
                indices_to_test = indices_to_each_uniq_test[test]
                # add all the coverage from ..
                covg_per_class[class_of_element][j] += np.sum(coverage_matrix[indices_to_test, i]) 

    classes = list(covg_per_class.keys())
    covg_matrix_per_class = np.array([covg_per_class[_class] > 0 for _class in classes], dtype = np.int32).T
    return covg_matrix_per_class


def diversity(coverage_matrix):
    """
    tests cover diverse combinations of components (classes)
    """
    N_tests = coverage_matrix.shape[0]
    get_equals = lambda v: np.sum(np.all(coverage_matrix == v, axis = 1))
    uniq_groups = np.unique(coverage_matrix, axis = 0)
    equal_ns = np.int32(list(map(get_equals, uniq_groups)))

    if len(coverage_matrix) == 1:
        gini = np.finfo(float).eps
    else:
        gini = 1. - np.sum(equal_ns * (equal_ns - 1))/(N_tests * (N_tests - 1)) # 0. ~ 1.

    return gini


def uniqueness(coverage_matrix):
    """
    ensure program components (classes) are distinguishable by covered tests
    coverage_matrix: N_tests X N_classes
    """
    # a group of unique coverage (i.e., unique columns)
    num_uniq_groups = np.unique(coverage_matrix, axis = 1).shape[1]
    N_elements = coverage_matrix.shape[1]
    uniqv = num_uniq_groups / N_elements
    return uniqv


def density(coverage_matrix):
    """
    ensure program elemnets to be frequently involved in tests
    """
    N_tests, N_elements = coverage_matrix.shape
    num_cells = N_tests * N_elements
    num_covered = np.sum(coverage_matrix)
    bfr_normalised =  num_covered/num_cells
    aft_normalised = 1. - np.abs(1 - 2 * bfr_normalised) # between 0. ~ 1.

    return aft_normalised


def compute_ddu(coverage_matrix_file, testlst_file, spectra_file):
    """
    generate coverage matrix & compute DDU metrics
    """
    covg_matrix_per_class = gen_coverage_matrix_secure(coverage_matrix_file, testlst_file, spectra_file)

    u = uniqueness(covg_matrix_per_class)
    div = diversity(covg_matrix_per_class)
    dens = density(covg_matrix_per_class)
    ddu = u * div * dens 
    return  ddu, u, div, dens


def main():
    import argparse
    import pandas as pd 
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-dst", "--dest", type = str)
    parser.add_argument("-project", "--project_name", type = str, default = None,
        help = "e.g., apache/pulsar")
    args = parser.parse_args()
    
    target_data_file = "../change-metrics/targets/data.tsv"
    sbfl_dir = "../projects"
    sbfl_result_dirs = {
        'apache/hbase':os.path.join(sbfl_dir, 'hbase'), 
        'apache/ignite':os.path.join(sbfl_dir, 'ignite'), 
        'apache/pulsar':os.path.join(sbfl_dir, 'pulsar'), 
        'Alluxio/alluxio':os.path.join(sbfl_dir, 'alluxio'),
        'neo4j/neo4j':os.path.join(sbfl_dir, 'neo4j')}

    root_repo = "../change-metrics/benchmarks"
    repos = {'apache/hbase':os.path.join(root_repo,'hbase'), 
        'apache/ignite':os.path.join(root_repo,'ignite'),
        'apache/pulsar':os.path.join(root_repo,'pulsar'),
        'Alluxio/alluxio':os.path.join(root_repo,'alluxio'),
        'neo4j/neo4j':os.path.join(root_repo,'neo4j')}

    project_full_names = {'hbase':'apache/hbase', 'ignite':'apache/ignite', 
        'pulsar':'apache/pulsar', 'alluxio':'Alluxio/alluxio', 'neo4j':'neo4j/neo4j'}
    
    # incomplete
    if args.project_name is None:   
        project_names = ['hbase', 'ignite', 'pulsar','alluxio', 'neo4j']
    else:
        project_names = [args.project_name]

    ddus = {'project':[], 'commit':[], 'ddu':[], 'uniqueness':[], 'density':[], 'diversity':[]}
    cnt = 0
    for project_name in tqdm(project_names):
        project_id = project_full_names[project_name]
        print ("Processing: {}".format(project_name))
        # this one is to get the full commit-id 
        commits_in_rev = utils.get_commit_infos_and_order(repos[project_id], only_ordered_commit = True)
        commits_to_inspect = utils.get_commits_to_inspect(target_data_file, project_id, commits_in_rev)
        for commit_to_inspect in tqdm(commits_to_inspect):
            matched_dir = utils.get_matching_dir(sbfl_result_dirs[project_id].format(commit_to_inspect))
            
            if matched_dir is None:
                print ("dir doesn't exist", project_id, sbfl_result_dirs[project_id].format(commit_to_inspect))
                cnt += 1
                continue

            spectra_file = utils.find_file(matched_dir, "spectra.csv")
            dir_to_look = os.path.dirname(spectra_file)
            testlst_file = utils.find_file(dir_to_look, "tests.csv")
            coverage_matrix_file = utils.find_file(dir_to_look, "matrix.txt")

            #compute_ddu(coverage_matrix_file, testlst_file, spectra_file)
            ddu, u, div, dens = compute_ddu(coverage_matrix_file, testlst_file, spectra_file)
            #continue 
            ddus['project'].append(project_id)
            ddus['commit'].append(commit_to_inspect)
            ddus['ddu'].append(ddu)
            ddus['uniqueness'].append(u)
            ddus['density'].append(dens)
            ddus['diversity'].append(div)

    ddus_df = pd.DataFrame(ddus)
    #print (ddus_df)

    os.makedirs(args.dest, exist_ok=True)
    ddu_file = os.path.join(args.dest, "ddu.csv")
    ddus_df.to_csv(ddu_file, index = False)


if __name__ == "__main__":
    main()