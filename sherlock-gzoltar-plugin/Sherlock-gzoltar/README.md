## Readme for using gzoltar with the flakytest list inputs

This forked version allows to provide a list of tests that are marked as flaky and thus count them as failed in the Junit run.

### Command sequence:
#### To use the gzoltar built in test runner 
- Clean and compile tests : `mvn clean test-compile` (e.g. `-pl $submodule` to specify the module)
- Record tests with gzoltar : `mvn -P sherlock gzoltar:list-test-methods`
- Run the tests and compute gzoltar execution file : `mvn -P sherlock -Dgzoltar.offline=false -Dgzoltar.collectCoverage=true -Dgzlotar.flakyTestList=${listPath} gzoltar:run-test-methods`
- Generate reports and rankings : `mvn gzoltar:fl-report`

#### associated maven `pom.xml` config
`Profile`
```xml
<profile>
    <id>sherlock</id>
    <activation>
      <property>
        <name>sherlock</name>
      </property>
    </activation>
    <build>
      <plugins>
        <plugin>
          <groupId>com.gzoltar</groupId>
          <artifactId>com.gzoltar.maven</artifactId>
          <version>1.7.3-SHERLOCK</version>
          <dependencies>
            <dependency>
              <groupId>junit</groupId>
              <artifactId>junit</artifactId>
              <version>4.12</version>
            </dependency>
          </dependencies>
          <executions>
            <execution>
              <id>run-test-methods</id>
              <goals>
                <goal>run-test-methods</goal>
              </goals>
            </execution>
          </executions>
        </plugin>
      </plugins>
    </build>
</profile>
```

`plugin`
```xml
<plugin>
                <groupId>com.gzoltar</groupId>
                <artifactId>com.gzoltar.maven</artifactId>
                <version>1.7.3-SHERLOCK</version>
                <executions>
                  <execution>
                    <id>fl-report</id>
                    <goals>
                      <goal>fl-report</goal>
                    </goals>
                    <configuration>
                      <granularity>line</granularity>
                      <inclPublicMethods>true</inclPublicMethods>
                      <inclStaticConstructors>true</inclStaticConstructors>
                      <inclDeprecatedMethods>true</inclDeprecatedMethods>
                      <flFamilies>
                        <flFamily>
                          <name>sfL</name>
                          <formulas>
                            <formula>barinel</formula>
                            <formula>dstar</formula>
                            <formula>ochiai</formula>
                            <formula>tarantula</formula>
                            <!--<formula>...</formula>-->
                          </formulas>
                          <metrics>
                            <metric>rho</metric>
                            <metric>ambiguity</metric>
                            <metric>entropy</metric>
                            <!--<metric>...</metric>-->
                          </metrics>
                          <formatters>
                            <format implementation="com.gzoltar.report.fl.config.ConfigTxtReportFormatter" />
                            <format implementation="com.gzoltar.report.fl.config.ConfigHTMLReportFormatter">
                              <htmlViews>
                                <htmlView>sunburst</htmlView>
                                <htmlView>vertical_partition</htmlView>
                                <!--<htmlView>...</htmlView>-->
                              </htmlViews>
                            </format>
                          </formatters>
                        </flFamily>
                      </flFamilies>
                    </configuration>
                  </execution>
                </executions>
            </plugin>
```

#### To use surefire test runner 
- Clean and compile tests : `mvn clean test-compile` (e.g. `-pl $submodule` to specify the module)
- Run test and compile gzoltar execution file : `mvn -Dgzoltar.flakyTestList=${listPath} -pl ${submodule} test`
- Generate report : `mvn -pl ${submodule} gzoltar:fl-report`

#### associated maven `pom.xml` config

```xml
 <plugin>
   <groupId>com.gzoltar</groupId>
   <artifactId>com.gzoltar.maven</artifactId>
   <version>1.7.3-SHERLOCK</version>
   <dependencies>
     <dependency>
       <groupId>junit</groupId>
       <artifactId>junit</artifactId>
       <version>4.12</version>
     </dependency>
   </dependencies>
   <executions>
     <execution>
       <id>pre-unit-test</id>
       <goals>
         <goal>prepare-agent</goal>
       </goals>
     </execution>
   </executions>
 </plugin>

```
The gzoltar listener should also be added to the surefire plugin :

```xml
<configuration>
       <properties>
              <property>
                     <name>listener</>
                     <value>com.gzoltar.internal.core.listeners.JUnitListener</value>
              </property>
       </properties>
</configuration>
```

### FAQ

#### Getting `ClassNotFoundException` on the Gzoltar `JunitListener`.
It might happened that on multiple-module maven project the `com.gzoltar.core` classpath library is over-written by surefire `argLine` parameter.
To avoid this issue you should add `@{argLine}` to the `<argLine>` property in the surefire plugin.

