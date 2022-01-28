from pydoc import classname
import sys
import os
import json
import pandas as pd
from pprint import pprint

def main():
    # Checks
    checkUsage()

    path = sys.argv[1]
    results = []
    project = path.split("/")[-1]
    # Need to change those 2 manually
    commit = "3ce9a3833e4c1bff8d6f185bc7f02f4e61d2af21"
    isSusFlaky = str(0)

    # Parsing Spoon results folder
    for jsonFile in os.listdir(path):
        # print(jsonFile)
        jsonPath = os.path.join(path, jsonFile)
        with open(jsonPath, 'r') as json_file:
            resultFile = json.load(json_file)
            results.append(resultFile)

    f = open("temp.txt", "w")
    for result in results:
        className = result["ClassName"]
        filePath = result["FilePath"]
        # If needed, remove first part of absolute path
        # .split("/Users/xx.xx/Documents/Work/projects/Sherlock-perso/projects/")[-1]
        last_char_index = className.rfind(".")
        className = className[:last_char_index] + "$" + className[last_char_index+1:]

        sm_dates = result["NumberOfDates"]
        sm_randoms = result["NumberOfRandoms"]
        sm_io = result["NumberOfIO"]
        sm_collections = result["NumberOfCollections"]
        sm_threads = result["NumberOfThreads"]
        sm_networks = result["NumberOfNetworks"]
        sm_lines = result["NumberOfLines"]
        sm_doi = result["DepthOfInheritance"]
        sm_cc = result["CyclomaticComplexity"]

        row = {
            "className": className,
            "filePath": filePath,
            "sm_dates": str(sm_dates),
            "sm_randoms": str(sm_randoms),
            "sm_io": str(sm_io),
            "sm_collections": str(sm_collections),
            "sm_threads": str(sm_threads),
            "sm_networks": str(sm_networks),
            "sm_lines": str(sm_lines),
            "sm_doi": str(sm_doi),
            "sm_cc": str(sm_cc)
            }
        tocsv = ",".join([project, commit, row["className"], row["filePath"], isSusFlaky, row["sm_dates"], row["sm_randoms"], row["sm_io"], row["sm_collections"], row["sm_threads"], row["sm_networks"], row["sm_lines"], row["sm_doi"], row["sm_cc"]]) + "\n"
        f.write(tocsv)
    f.close()

def checkUsage():
    #Check the programs' arguments
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        print("Usage: python3 analyseResults.py [path/to/resultsFolder]")
        sys.exit(1)

if __name__ == "__main__":
    main()