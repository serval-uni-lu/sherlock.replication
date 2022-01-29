# Genetic Programming-based & Voting-based Flakiness Identification Model Generation, and DDU computation

Traina and evaluate GP-based models, and vote for the most suspicious class

## GP model training & test 

Train flakiness identification models using GP.

### Dependencies

- DEAP 1.3.1
- scipy 1.5.4

### Usage

`./gp.sh ${dest} ${datadir} ${mode}`

**Arguments**:

- `${dest}`: a directory that will store the output GP models and their prediction results 
- `${datadir}`: a directory that contains input data files (i.e., `data`)
- `${mode}`: allow to use a different combinations of metrics. currenlty support below four modes
    - 0: only sbfl. 
    - 1: sbfl & change
    - 2: sbfl & size
    - 3: sblf & flaky

**Output**:

For mode 0/1/2/3, `best.${fold}.${iter}.mdl` and `${commit}.${fold}.test.result.csv` will be stored <br /> 
under `${dest}/gp/{sbfl|sbfl_chg|sbfl_size|sbfl_flaky}`, respectively. *fold* indicates the corresponding test fold of the model <br />
and *iter* implies that the model was generated from the *iter*th repetition of GP. *commit* denotes one of the commit the test fold contains. <br /> 
To replicate the results, simply give `data` to `$datadir`.

## Voting 

Vote for the class that is most likely to be flaky

### Usage

`./vote.sh ${dest} ${model_dir} ${top_n}`

**Arguments**:

- `${dest}`: a directory where the voting result will be saved
- `${model_dir}`: a directory that contains models participating in the voting
- `${top_n}`: the number of candidate classes an individual model will vote. e.g., `top_n=3`, each model will vote for the top 3 classes in its ranking. <br /> The experimental results reported in the paper were produced with `top_n=3`. To replicate the results, run `./vote.sh results/gp' 

**Output**:

- `${dest}/vote/voting.rank.${top_n}.weighted.csv`

Currently, all the results, both GP and voting, are stored under `results` directory as `outputs.zip`. 


## DDU

To compute a DDU score for a project, simly run <br />

`python3 ddu.py -dst ${dest} -project ${project}`

This will produce a `ddu.csv` file under `${dest}`. `${project}` can be one of *pulsar, hbase, neo4j, ignite, alluxio*. 

