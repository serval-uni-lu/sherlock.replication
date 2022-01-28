## Static Metrics Analysis

`findCoveredClasses.py`

Takes Gzoltar results folder and find covered classes
Creates a file.txt listing classes to get static metrics from

`analyseResults.py`

Parse the Spoon result folder
Creates a temp.txt containing static metrics for all covered classes (susFlaky and nonSusFlaky)

`results` contains results with all covered classes (by all tests), and complexity-related metrics as well