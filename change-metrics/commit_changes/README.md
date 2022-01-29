# Commit Chang Information  

Collect commit change information required to generate change metrics. <br /> More specificially, we collect the past change information of each file modified by a commit. <br /> Before running `./run.sh`, a git repository of a target project should be already cloned. <br />
For instance, to collect the change information of the project *pulsar*, its git repository should be already cloned at `${repo}`. 

### Collected Information 

For each file modified by a commit,

- Number of prior changes made on the file 
- A list of unique developers who made changs on the file 

### Dependencies

- GitPython 3.1.24 
- git version 2.32.0


### Usage 

`./run.sh ${repo} ${projec} ${dest}` 

#### Arguments
- `${repo}`: a git repository of a project that we target to collect commit change information. (e.g., `../benchmarks`)
- `${project}`: a project name. This value will be used to identify a result file 
- `${dest}`: a directory where the output file of `run.sh` will be stored

Running the command above will generate

- `${project}.changes.json"`
- `${project}.files.author.json`
- `${project}.rename_history.json`
- `${project}.commit_chgs.pf.pkl`

under `${dest}`. Among these files, we only `${project}.rename_history.json` and `${project}.commit_chgs.pf.pkl` <br /> for the following steps to generat change metrics used in our study. 

Currently, these commit change information files used in our study are stored under `results` as `${project}.zip`. <br /> To use this already-computed data, unzip them in `results`.  

