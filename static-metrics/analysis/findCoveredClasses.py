
import process 
import pandas as pd
import sys
import os
from pprint import pprint
pd.options.display.max_colwidth = 100

# Adapt with yours
absolutePath = "/Users/xx.xx/Documents/Work/projects/Sherlock/Documents/"

def get_classes(spectra_file):
    """
    return a list of files to look for 
    """
    elements_df = process.read_elements(absolutePath + spectra_file)
    paths = elements_df.path
    return paths

def get_tests(tests_file):
    """
    return a list of files to look for 
    """
    tests = process.read_tests(absolutePath + tests_file)
    return tests

def get_matrix(matrix_file):
    """
    return a list of files to look for 
    """
    matrix = process.read_coverage_matrix(absolutePath + matrix_file)
    return matrix

def main():
    """
    Main function
    """
    checkUsage()
    projectName = sys.argv[1]
    commitFolder = sys.argv[2]
    givenTest = ""
    # I can give a test to only get information about it, if not, get information about all tests
    if len(sys.argv) == 4:
        givenTest = sys.argv[3]
    coveredClasses = []

    # GZoltar output folders locations
    gzoltarOutput = {
        'pulsar': 'Pulsar-gzoltaroutput/{}/site/gzoltar/sfl/txt/{}',
        'alluxio': 'alluxio-gzoltar/{}/output-files/site-class/sfl/txt/{}',
        'hbase': 'Hbase-gzoltar/{}/site/gzoltar/sfl/txt/{}',
        'neo4j': 'neo4j-gzoltar/{}/output_files/site-class/sfl/txt/{}',
        'ignite': 'ignite-gzoltar/{}/output-files/site-class/sfl/txt/{}'
        }
    
    # GZoltar files of interest
    spectra = get_classes(gzoltarOutput[projectName].format(commitFolder, 'spectra.csv'))
    tests = get_tests(gzoltarOutput[projectName].format(commitFolder, 'tests.csv'))
    matrix = get_matrix(gzoltarOutput[projectName].format(commitFolder, 'matrix.txt'))

    if givenTest != "":
        tests = tests[tests['name'].str.contains(givenTest)]     
    
    # For each test of interest
    for index, test in tests.iterrows():
        if givenTest != "":
            print(test)
        # For 0 to size of a line in matrix (all components)
        for i in range(0, len(matrix[index])):
            element = matrix[index][i]
            # If the component is covered
            if element == '1':
                elementName = spectra[i]
                # Get className
                classPart = elementName.split("#")
                if len(classPart) > 2:
                    print("More than one method found")
                    sys.exit(1)
                location = classPart[0].split("$")[0]
                className = classPart[0].split("$")[1]
                fullClassName = location + "." + className
                # Add className to list of covered classes
                if fullClassName not in coveredClasses:
                    coveredClasses.append(fullClassName)

    # pprint(coveredClasses)
    print("\nProject:", projectName)
    print("Number of tests:", len(tests))
    print("Number of classes:", len(spectra))
    print("Number of covered classes (by all tests):", len(coveredClasses))
    
    # Saving file
    textfile = open("./file.txt", "w")
    for element in coveredClasses:
        textfile.write(element + "\n")
    textfile.close()
    print("File saved.")

def checkUsage():
    """
    Check Usage
    """
    #Check the programs' arguments
    if len(sys.argv) != 3:
        print("Usage:")
        print("python findCoveredClasses.py projectName commitFolder givenTest")

if __name__ == "__main__":
    main()
