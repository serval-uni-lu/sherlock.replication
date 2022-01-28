#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import json
import csv
from pprint import pprint
import subprocess
import shlex
import csv  

fixKeywords = ["fix", "repair", "solve", "correct", "patch", "prevent"]

def main():
    """
    Main function
    """
    checkUsage()
    resultsPath = sys.argv[1]

    countProjects = 0
    countCommits = 0
    countCommitsFix = 0
    countCommitsFixCode = 0
    countCommitsFixTestAndCode = 0

    projectsOfInterest = {}
    csvData = []

    patchedFilesExtensions = {}

    for root, dirs, files in os.walk(resultsPath):
        for name in files:

            # Skip non-commit files
            if name == "sourcegraphsearch.json":
                countProjects += 1
                continue
            else:
                sgData = loadJson(os.path.join(root, "sourcegraphsearch.json"))
                projectName = sgData["Query"].split("repo:")[-1][:-1]
            
            countCommits += 1
            data = loadJson(os.path.join(root, name))

            # Skip Errors
            if "message" in data:
                # print(os.path.join(root, name))
                # print(data["message"])
                continue

            sha = data["sha"]
            stats = data["stats"]
            changedfiles = data["files"]
            commitMessage = data["commit"]["message"]
            htmlUrl = data["html_url"]
            commitDate = data["commit"]["committer"]["date"]

            numberOfChangedFiles = len(changedfiles)
            touchTest = False
            touchCode = False

            for file in changedfiles:
                if "patch" in file:
                    filename = file["filename"]
                    extension = filename.split(".")[-1]
                    if extension not in patchedFilesExtensions:
                        patchedFilesExtensions[extension] = 1
                    else:
                        patchedFilesExtensions[extension] += 1


            if any(x in commitMessage.lower() for x in fixKeywords):
                countCommitsFix += 1
                # print(sha)
                countchanges = 0
                for file in changedfiles:
                    filename = file["filename"]
                    fileAdditions = file["additions"]
                    fileDeletions = file["deletions"]
                    fileChanges = file["changes"]
                    countchanges += fileChanges

                    # Check for files when patch is available
                    if "patch" in file:
                        isPyFile = filename.endswith(".py")
                        isTest = "test" in filename.lower()
                        filePatch = file["patch"]
                        fileStatus = file["status"]

                        # Only check py files
                        # if not isPyFile:
                        #     continue
                        if "test" in filePatch.lower() or isTest:
                            touchTest = True
                        else:
                            touchCode = True
                        

                # Find commits fixing test and code
                if touchCode and not touchTest:

                    # print("commitMessage", commitMessage)
                    # print("Number of changedfiles", len(changedfiles))
                    # print("Additions", stats["additions"])
                    # print("Deletions", stats["deletions"])
                    # print("htmlUrl", htmlUrl)
                    countCommitsFixCode += 1
                    # if "apache/ignite" in projectName:
                    #     print("Code & !Test", projectName, commitDate, sha)
                    # Limit number of changed files
                    # if countchanges <= 10:
                        # print(projectName, htmlUrl, numberOfChangedFiles)

                    comment = getInterestingLinesFromMessage("flaky", commitMessage)
                    row = [projectName, htmlUrl, sha, comment]
                    csvData.append(row)
                    # Add to dictionary
                    # If different from Android frameworks_base
                    if "frameworks_base" not in projectName:
                        if projectName not in projectsOfInterest:
                            projectsOfInterest[projectName] = 1
                        else:
                            projectsOfInterest[projectName] += 1
                
                if touchTest and touchCode:
                    countCommitsFixTestAndCode += 1
                    # print("Code & Test", projectName, commitDate, sha)

                    if "frameworks_base" not in projectName:
                        if projectName not in projectsOfInterest:
                            projectsOfInterest[projectName] = 1
                        else:
                            projectsOfInterest[projectName] += 1
    
    # Print projects with at least 5 commits
    for project, numberOfCommits in projectsOfInterest.items():
        if numberOfCommits >= 5:
            print(project, numberOfCommits)

    # Print general info
    print("\ncountProjects", countProjects)
    print("Number of commits with 'flaky' in message", countCommits)
    print("Number of commits with 'flaky' and mentions about fix in message", countCommitsFix)
    print("Number of commits with 'flaky' and fix apparently modifying code only", countCommitsFixCode)
    print("Number of commits with 'flaky' and fix apparently modifying test and code", countCommitsFixTestAndCode)
    # pprint(sorted(patchedFilesExtensions.items(), key=lambda x: x[1], reverse=False))

    # Save interesting findings to file       
    # csvData = sorted(csvData, key=lambda x:x[0])
    # writeToCsv(csvData)

def getInterestingLinesFromMessage(keyword, message):
    # Split by lines
    message = message.replace("\r", "\n")
    message = message.split("\n")

    comment = ""
    for line in message:
        if keyword in line.lower():
            comment += line + ","
    comment = comment.rstrip(',')
    return comment

def writeToCsv(data):
    with open('file.csv', 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerows(data)
    return

def loadJson(jsonPath):
    with open(jsonPath) as report:
        data = json.load(report)
    return data

def checkUsage():
    """
    Check Usage
    """
    #Check the programs' arguments
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        print("Usage:")
        print("python commitAnalysis.py /path/to/results")
        sys.exit(1)

if __name__ == "__main__":
    main()