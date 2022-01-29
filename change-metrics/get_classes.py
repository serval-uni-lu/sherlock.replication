import os
from process import read_tests
from tqdm import tqdm 
import numpy as np
import utils

def get_list_of_executed_classes(covg_matrix_file, testlst_file, spectra_file):
    """
    coverage_matrix -> |T| X |E|
    """
    from process import read_coverage_matrix, read_elements

    coverage_matrix = read_coverage_matrix(covg_matrix_file)
    tests = read_tests(testlst_file).name.values
    elements = read_elements(spectra_file).path.values
    N_tests, N_elements = coverage_matrix.shape
    
    assert N_tests == len(tests), "{} vs {}".format(N_tests, len(tests))
    assert N_elements == len(elements), "{} vs {}".format(N_elements, len(elements))

    # the elemnent can be in other granularity rather than in class
    covg_per_class = {}
    for i in range(N_elements):
        class_of_element = elements[i].split("#")[0]
        try:
            covg_per_class[class_of_element] += coverage_matrix[:,i]
        except Exception:
            covg_per_class[class_of_element] = coverage_matrix[:,i]
        
    classes_under_test = list(covg_per_class.keys())
    covg_matrix_per_class = np.array([
        covg_per_class[_class] > 0 for _class in classes_under_test], dtype = np.int32).T # N_Test X N_Class
    
    # covered (class) or cover (test) at least once
    indices_to_exec_classes = np.where(np.sum(covg_matrix_per_class, axis = 0) > 0)[0]
    indices_to_exec_tests = np.where(np.sum(covg_matrix_per_class, axis = 1) > 0)[0]

    # since, they may have 
    executed_classes = list(set(np.array(classes_under_test, dtype = object)[indices_to_exec_classes]))
    executed_tests = list(set(tests[indices_to_exec_tests]))
    
    # logging
    #print ("Out of {} classes, {} are executed".format(len(set(classes_under_test)), len(executed_classes)))
    #print ("Out of {} tests, {} are executed".format(len(set(tests)), len(executed_tests)))
    return executed_classes, executed_tests


def main(args = None, **kwargs):
    import argparse
    
    if args is None:
        parser = argparse.ArgumentParser()
        parser.add_argument("-project", "--project_name", type = str, default = None,
            help = "e.g., pulsar")
        parser.add_argument("-project_id", "--full_project_name", type = str, default = None,
            help = "e.g., apache/pulsar")
        parser.add_argument("-target", "--target_data_file", type = str, default = "targets/data.tsv",
            help = "the tsv file of the spreadsheet")
        parser.add_argument("-sbfl", "--sbfl_result_dir", type = str, default = "../projects/pulsar",
            help = "a directory that contains gzoltar results of all commits of a target project")
        parser.add_argument("-repo", type = str, default = "benchmarks/pulsar",
            help = "a github repository of a proejct")

        args = parser.parse_args()

    if 'project_name' in kwargs.keys():
        project_name = kwargs['project_name']
    else:
        project_name = args.project_name

    if 'project_id' in kwargs.keys():
        full_project_name = kwargs['project_id']
    else:
        full_project_name = args.full_project_name

    if 'repo' in kwargs.keys():
        repo = kwargs['repo']
    else:
        repo = args.repo

    if 'sbfl' in kwargs.keys():
        sbfl_result_dir = kwargs['sbfl']
    else:
        sbfl_result_dir = args.sbfl_result_dir

    # to get a full commit-id 
    commits_in_rev = utils.get_commit_infos_and_order(repo, only_ordered_commit = True)
    commits_to_inspect = utils.get_commits_to_inspect(args.target_data_file, full_project_name, commits_in_rev)
    
    executed_classes_and_tests = {project_name: {}}
    for commit_to_inspect in tqdm(commits_to_inspect):
        #print ("commit: {}".format(commit_to_inspect))
        matched_dir = utils.get_matching_dir(os.path.join(sbfl_result_dir, commit_to_inspect))
        if matched_dir is None:
            msg = "dir doesn't exist", project_name, os.path.join(sbfl_result_dir, commit_to_inspect)
            assert False, msg

        spectra_file = utils.find_file(matched_dir, "spectra.csv")
        dir_to_look = os.path.dirname(spectra_file)
        testlst_file = utils.find_file(dir_to_look, "tests.csv")
        coverage_matrix_file = utils.find_file(dir_to_look, "matrix.txt")
        executed_classes, executed_tests = get_list_of_executed_classes(coverage_matrix_file, testlst_file, spectra_file)
        executed_classes_and_tests[project_name][commit_to_inspect] = {'Class':executed_classes, 'Test':executed_tests}

    os.makedirs("targets", exist_ok=True)
    destfile = os.path.join("targets/test_and_class_info_{}.pkl".format(project_name))
    with open(destfile, 'wb') as f:
        import pickle
        pickle.dump(executed_classes_and_tests, f)


if __name__ == "__main__":
    main()