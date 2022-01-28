# Sherlock replication package
This repository contains the necessary scripts and source code to build the Sherloc-Gzoltar mven plugin, the scripts used to run the experiment for each projects and the results presented in _Identifying non-Deterministic Software Components_
## Requirements
### Data extraction
- `unzip`

### Run
- Java version : `8 Update 2xx` with `JAVA_HOME` environment variable set and pointing to the JDK
- Apache Maven verison : 3.6.3
- Gzoltar sherlock version maven plugin version 1.7.3-SHERLOCk on local maven repository (i.e. installation procedure described bellow)

### Gzoltar-sherlock plugin instalation

To be able to specify flaky tests during gzoltar report generation we have modified the existing code to allow the specification of such failing tests. The code is provided as a maven project in th `sherlock-gzoltar-plugin` folder.
To install the plugin please use the following command at the root of the `sherlock-gzoltar-plugin` directory.

``mvn clean install -DskipTests``

Some error about javadoc command might be shown but the overall build of the plugin eventually succeeds.

### Projects repository
- Alluxio : `git@github.com:Alluxio/alluxio.git`
- Hbase : `git@github.com:apache/hbase.git`
- Ignite : `git@github.com:apache/ignite.git`
- Neo4j : `git@github.com:neo4j/neo4j.git`
- Pulsar : `git@github.com:apache/pulsar.git`
## Structure


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

```
<property>
        <name>listener</name>
        <value>com.gzoltar.internal.core.listeners.JUnitListener</value>
        OR
        <value>com.gzoltar.internal.core.listeners.TestNGListener</value>
</property>
```


