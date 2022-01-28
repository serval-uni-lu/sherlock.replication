#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import json
import csv
from pprint import pprint
import subprocess
import shlex

# Get args
csvPath = sys.argv[1]
resultsPath = sys.argv[2]

def main():
    """
    Main function
    """
    checkUsage()
    
    projects = csvReader(csvPath)
    main = []

    for element in projects:
        # if element["category"] == "NOD":
        main.append(element["URL"])

    unique = set(main)

    for project in unique:
        projectName = project.lstrip("https://github.com/")
        # print(projectName)
        searchSourceGraph(projectName)
    

def searchSourceGraph(projectName):
    """
    Take a project name
    Print query 
    """
    # Avoid slashes in repo name
    repoName = projectName.replace("/","_")
    dirPath = os.path.join(resultsPath, repoName)
    # If folder doesn't exist we create it
    if not os.path.isdir(dirPath):
        os.mkdir(dirPath)
    # If file doesn't exist or folder is empty, we make the query
    if not os.path.isfile(os.path.join(dirPath, "sourcegraphsearch.json")) or not os.listdir(dirPath):
        queryCommit = "src search -json 'flaky count:all timeout:59s type:commit repo:" + projectName + "$' | tee " + dirPath + "/sourcegraphsearch.json"
        # Add sleep for API "too many requests"
        sleepCommand = "sleep 3"
        print(queryCommit)
        print(sleepCommand)
    return

def csvReader(csvPath):
    """
    Read csv file from input arg
    Return list of projects
    """
    projects = []
    with open(csvPath) as csvFile:
        csvReader = csv.reader(csvFile, delimiter=',')
        lineCount = 0
        for row in csvReader:
            if lineCount == 0:
                lineCount += 1
            else:
                lineCount += 1
                project = assembleProject(row)
                projects.append(project)
    return projects

def assembleProject(row):
    """
    Take a row form csv file
    Return project object
    """
    url = row[0]
    sha = row[1]
    testName = row[3]
    category = row[4]
    project = {
        "URL": url,
        "SHA": sha,
        "testName": testName,
        "category": category,
    }
    return project

def sortBy(projectList, feature, n):
    """
    Take projectList, sorting feature, first n to return
    Return projectList sorted accordingly
    """
    return sorted(projectList, key=lambda x: x[feature], reverse=True)[:n]

def checkUsage():
    """
    Check Usage
    """
    #Check the programs' arguments
    if len(sys.argv) != 3 or not os.path.isfile(sys.argv[1]) or not os.path.isdir(sys.argv[2]):
        print("Usage:")
        print("python searchiDFlakies.py /path/to/iDFlakies-flakytests-list.csv /path/to/resultsFolder")
        sys.exit(1)

if __name__ == "__main__":
    main()