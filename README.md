# Sherlock replication package
This repository contains the necessary scripts and source code to build the Sherloc-Gzoltar mven plugin, the scripts used to run the experiment for each projects and the results presented in _Identifying non-Deterministic Software Components_
## Requirements
### Data extraction
- `unzip`

### Run
- Java version : `8 Update 2xx` with `JAVA_HOME` environment variable set and pointing to the JDK
- Apache MAven verison : 3.6.3
- Gzoltar sherlock version maven plugin version 1.7.3-SHERLOCk on local maven repository (i.e. installation procedure described bellow)

### Gzoltar-sherlock plugin instalation

To be able to specify flaky tests during gzoltar report generation we have modified the existing code to allow the specification of such failing tests. The code is provided as a maven project in th `sherlock-gzoltar-plugin` folder.
To install the plugin please use the following command at the root of the `sherlock-gzoltar-plugin` directory.

``mvn clean install -DskipTests``

Some error about javadoc command might be shown but the overall build of the plugin eventual succeed.


## Structure




