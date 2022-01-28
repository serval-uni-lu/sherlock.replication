/**
 * Copyright (C) 2020 GZoltar contributors.
 * 
 * This file is part of GZoltar.
 * 
 * GZoltar is free software: you can redistribute it and/or modify it under the terms of the GNU
 * Lesser General Public License as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 * 
 * GZoltar is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
 * the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
 * General Public License for more details.
 * 
 * You should have received a copy of the GNU Lesser General Public License along with GZoltar. If
 * not, see <https://www.gnu.org/licenses/>.
 */
package com.gzoltar.cli.commands;

import java.io.*;
import java.net.URL;
import java.util.HashSet;
import java.util.Properties;
import java.util.Set;

import org.kohsuke.args4j.Option;
import com.gzoltar.cli.Command;
import com.gzoltar.core.test.TestMethod;
import com.gzoltar.core.test.TestRunner;
import com.gzoltar.core.test.TestTask;
import com.gzoltar.core.test.junit.JUnitTestTask;
import com.gzoltar.core.test.testng.TestNGTestTask;
import com.gzoltar.core.util.ClassType;
import io.github.classgraph.ClassGraph;


/**
 * The <code>runTestMethods</code> command.
 */
public class RunTestMethods extends Command {




  @Option(name = "--testMethods", usage = "file with list of test methods to run",
      metaVar = "<path>", required = true)
  private File testMethods = null;

  @Option(name = "--collectCoverage", usage = "collect coverage of each test method",
      metaVar = "<boolean>", required = false)
  private Boolean collectCoverage = false;

  @Option(name = "--offline",
      usage = "inform GZoltar that classes have been instrumented using offline instrumentation",
      metaVar = "<boolean>", required = false)
  private Boolean offline = false;

  @Option(name = "--initTestClass", usage = "initialize test class with thread classloader",
      metaVar = "<boolean>", required = false)
  private Boolean initTestClass = false;

  //SHERLOCK-ADDITION add option to specify flaky test list file
  @Option(name="--flakyTests", usage="file with list of flaky test",metaVar = "<path>",required = false)
  private File flakyTestFile=null;


  @Override
  public String description() {
    return "Run test methods in isolation.";
  }



  /**
   * {@inheritDoc}
   */
  @Override
  public String name() {
    return "runTestMethods";
  }

  @Override
  public int execute(final PrintStream out, final PrintStream err) throws Exception {
    out.println("* " + this.description());

    Properties backupProperties = (Properties) System.getProperties().clone();

    if (!this.testMethods.exists() || !this.testMethods.canRead()) {
      throw new RuntimeException(this.testMethods + " does not exist or cannot be read");
    }

    //SHERLOCK-ADDITION Read the file and construct list of flaky tests
    boolean runWithFlaky = (flakyTestFile != null );
    Set<String> flakyTestSet = new HashSet<>();
    if(runWithFlaky){
      if ((!this.flakyTestFile.exists() || !this.flakyTestFile.canRead())){
        throw new RuntimeException(this.flakyTestFile + " does not exist or cannot be read");
      }
      flakyTestSet = constructFlakyTestList(flakyTestFile);
    }


    final URL[] classpathURLs = new ClassGraph().getClasspathURLs().toArray(new URL[0]);

    try (BufferedReader br = new BufferedReader(new FileReader(this.testMethods))) {
      String line;
      while ((line = br.readLine()) != null) {
        String[] split = line.split(",");

        TestMethod testMethod = new TestMethod(ClassType.valueOf(split[0]), split[1]);
        TestTask testTask = null;

        //SHERLOCK-ADDITION
        System.out.printf("[SHERLOCK] test name = %s %n",testMethod.getLongName());

        switch (testMethod.getClassType()) {
          case JUNIT:
            //SHERLOCK-ADDITION add boolean parameter to JUnitTestTask : isFlaky
            if(runWithFlaky) {
              //SHERLOCK-ADDITION check within flakyTestsList set if testMethod is marked as flaky
              boolean isTestFlaky = flakyTestSet.contains(testMethod.getLongName());
              testTask = new JUnitTestTask(classpathURLs, this.offline, this.collectCoverage,
                      this.initTestClass, testMethod,isTestFlaky);
            }else{
              testTask = new JUnitTestTask(classpathURLs, this.offline, this.collectCoverage,
                      this.initTestClass, testMethod);
            }
            break;
          case TESTNG:
            testTask = new TestNGTestTask(classpathURLs, this.offline, this.collectCoverage,
                this.initTestClass, testMethod);
            break;
          default:
            throw new RuntimeException(testMethod.getLongName() + " is not supported");
        }
        assert testTask != null;

        TestRunner.run(testTask);
        testTask = null;

        // restore system properties
        System.setProperties((Properties) backupProperties.clone());
      }
    }

    out.println("* Done!");

    return 0;
  }
  //SHERLOCK-ADDITION Create set containing flakyTests
  private Set<String> constructFlakyTestList(File flakyTestFile) {
    Set<String> flakyTestSet = new HashSet<>();
    try (BufferedReader br = new BufferedReader(new FileReader(flakyTestFile))) {
      String line;
      while ((line = br.readLine()) != null){
        flakyTestSet.add(line);
      }
    } catch (IOException e) {
      e.printStackTrace();
    }
    return flakyTestSet;
  }
}
