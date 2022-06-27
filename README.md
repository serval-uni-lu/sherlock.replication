# What Made This Test Flake? Pinpointing Classes Responsible for Test Flakiness: Replication package

This repository contains the necessary resources for replication. It includes:
- The projects and commits used in our study;
- The necessary scripts and source code to build the Gzoltar maven plugin;
- The scripts used to run experiments;
- And the results. 

## Requirements
### Data extraction
- `unzip`

### Run
- Java version : `8 Update 2xx` with `JAVA_HOME` environment variable set and pointing to the JDK
- Apache Maven verison : 3.6.3
- Gzoltar version maven plugin version 1.7.3-SHERLOCk on local maven repository (i.e. installation procedure described bellow)

### Gzoltar plugin installation

To be able to specify flaky tests during gzoltar report generation we have modified the existing code to allow the specification of such failing tests. The code is provided as a maven project in th `gzoltar-plugin` folder.
To install the plugin please use the following command at the root of the `gzoltar-plugin` directory.

``mvn clean install -DskipTests``

Some error about javadoc command might be shown but the overall build of the plugin eventually succeeds.

### Projects repository
- Alluxio : `git@github.com:Alluxio/alluxio.git`
- Hbase : `git@github.com:apache/hbase.git`
- Ignite : `git@github.com:apache/ignite.git`
- Neo4j : `git@github.com:neo4j/neo4j.git`
- Pulsar : `git@github.com:apache/pulsar.git`

## Structure
- `projects/{project}` : contains the commit used for the experiments and he experimental results.
- `projects/{project}/{commit.id}/` : contains the SBFL reports after running the tests on `{commit.id}`. For some projects the modified `pom.xml` is present.
- `gzoltar-plugin` : contains the _maven_ gzoltar project modified to suits our experiments.
- `data-collection` : contains scripts used for searching projects and flaky fixing commits.
- `static-metrics` : contains scripts used to compute and analyse static metrics.
- `change-metrics` : contains scirpts used to compute change metrics and combine all static, change, and sbfl metrics.
- `model-generation` : contains scripts to train GP-based models, perform the model voting, and compute DDU scores. 

## Run experiments
The experiments subject consist of 5 projects from which we analyse between 3 and 14 commits.

Each experiments (i.e. a commit of a project ) starts by checking out the parent commit (i.e. prior the patch).
 With `{project}` the analyzed project, `{project.fix.commitId}` the commit id containing the flakyTest patch.
```
mkdir {project} 
cd {project}
git clone {project.git.url} {project.base}
mkdir {project.fix.commitId}
cp -r {project.base} {project.fix.commitId}
cd {project.fix.commitId};
git checkout {project.fix.commitId};
git checkout HEAD^;
```
Then the Plugin in should be put into the build definition script `pom.xml` of the target commit.

```xml
<plugins>
...
<plugin>
  <groupId>com.gzoltar</groupId>
  <artifactId>com.gzoltar.maven</artifactId>
  <version>1.7.3-SHERLOCK</version>
  <executions>
    <execution>
      <id>pre-unit-test</id>
      <goals>
        <goal>prepare-agent</goal>
      </goals>
    </execution>
  </executions>
</plugin>
...
</plugins>
```

Please not that if surefire is used, a fork count of at least `3` must be used `<forkCount>3</forkCount>` also the plugin listner should be put into the surefire listener configuration :

```xml
<property>
  <name>listener</name>
    <value>com.gzoltar.internal.core.listeners.JUnitListener</value>
    OR
    <value>com.gzoltar.internal.core.listeners.TestNGListener</value>
</property>
```

A file containing the flakytest owning class and test name must also be present at the root of the project e.g.

```
touch flaky.txt
echo FlakyTestClass#flakyTest > flaky.txt
```

Then the build can be run using the appropriate command
```
mvn clean install {maven opts} ... -fn  -Dgzoltar.flakyTestList=$PWD/flaky.txt
```
After the test execution, the report containing the different results can me obtain with 

```
mvn gzoltar:fl-report -Dgzoltar.granularity=class -fn -U -Dgzoltar.outputDirectory=$PWD/site-class
```

The coefficients of the instrumented class are available under `site-class/sfl/txt/*.csv`
