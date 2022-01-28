package base;

import spoon.Launcher;
import spoon.reflect.CtModel;
import spoon.reflect.code.CtInvocation;
import spoon.reflect.declaration.CtClass;
import spoon.reflect.declaration.CtMethod;
import spoon.reflect.declaration.CtType;
import spoon.reflect.visitor.filter.TypeFilter;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Scanner;

public class Search {

    private String projectPath;
    private CtModel model;
    private String methodName;
    private String className;

    public Search(String path) {
        projectPath = path;
        model = createSpoonModel();
    }

    public CtModel createSpoonModel() {
        // Creating launcher
        Launcher launcher = new Launcher();
        launcher.addInputResource(this.projectPath);
        // Escape comments
//        launcher.getEnvironment().setIgnoreDuplicateDeclarations(true);
//        launcher.getEnvironment().setAutoImports(true);
        launcher.getEnvironment().setCommentEnabled(false);
        // Creating model from project
        launcher.buildModel();
        CtModel model = launcher.getModel();
        return model;
    }

    /**
     * -INTERACTIVE- Find a particular method in the project based on a className.methodName
     * Call methodSearch to compute metrics and generate reports
     */
    public void singleMethodSearch() throws IOException {
        // ToDo Add checkers
        Scanner myObj = new Scanner(System.in);
        System.out.println("Enter method you want to analyze [format: className.methodName]");
        String fullName = myObj.nextLine();
        String[] arrayName = fullName.split("\\.");
        this.methodName = arrayName[arrayName.length - 1];
        this.className = arrayName[arrayName.length - 2];
        methodSearch();
    }

    /**
     * -INTERACTIVE- Find particular methods in the project based on a file
     * Call methodSearch to compute metrics and generate reports
     */
    public void listOfMethodsSearch() throws IOException {
        // Ask for file path
        Scanner myObj = new Scanner(System.in);
        System.out.println("Enter path to file with methods list inside");
        String path = myObj.nextLine();
        File file = new File(path);
        // Check if file exists
        if (!file.exists()) {
            System.out.println("File not found, please enter absolute path.");
            listOfMethodsSearch();
        }
        else {
            String st;
            BufferedReader br = new BufferedReader(new FileReader(file));
            while ((st = br.readLine()) != null) {
                System.out.println(st);
                this.getMethodFromFile(st);
                this.methodSearch();
            }
        }
    }

    /**
     * Find particular methods in the project based on a file
     * Call methodSearch to compute metrics and generate reports
     * @param listMethodsPath the file path
     */
    public void listOfMethodsSearch(String listMethodsPath) throws IOException {
        File file = new File(listMethodsPath);
        // Check if file exists
        if (!file.exists()) {
            System.out.println("-listMethodsPath: File not found, please enter absolute path.");
            System.exit(0);
        }
        else {
            String st;
            BufferedReader br = new BufferedReader(new FileReader(file));
            while ((st = br.readLine()) != null) {
                this.getMethodFromFile(st);
                this.methodSearch();
            }
        }
    }

    /**
     * Find a particular method in the project
     * Compute its metrics
     * Generate JSON report in ./results/projectName/
     */
    public void methodSearch() throws IOException {
        Boolean classFound = false;
        Boolean methodFound = false;
        Metric metric = new Metric();

        // For all classes
        for(CtType<?> currentClass : this.model.getAllTypes()) {
            // Match class name
            if (currentClass.getSimpleName().equals(this.className)) {
                classFound = true;
                // For all methods
                for(CtMethod currentMethod : currentClass.getMethods()) {
                    // Match method name
                    if (currentMethod.getSimpleName().equals(this.methodName)) {
                        methodFound = true;

                        metric.computeMetrics(currentMethod, currentClass);
                        metric.computeCUTMetrics(currentMethod, currentClass);
                        metric.generateReport(this.methodName, this.className.toString(), this.projectPath);
                        break;
                    }
                }
                break;
            }
        }
        // Error handlers
        if (!classFound) {
            System.out.println("No class \"" + this.className + "\" found.");
        }
        if (classFound && !methodFound) {
            System.out.println("No Method \"" + this.methodName + "\" found in class \"" + this.className + "\".");
        }
    }

    /**
     * Find all test methods in the project, not empty and starting with @Test
     * Compute their metrics
     * Generate JSON reports in ./results/projectName/
     */
    public void getAllTestMethods() throws IOException {
        // For all classes
        for(CtType<?> currentClass : this.model.getAllTypes()) {
            // For all methods
            for (CtMethod currentMethod : currentClass.getMethods()) {
                Metric metric = new Metric();
                /*
                Looking for Code Under Test, I want
                Method's body not empty
                A @test annotation
                 */
                if (currentMethod.getBody() != null && currentMethod.getAnnotations().toString().contains("@org.junit.Test")) {
                    metric.computeMetrics(currentMethod, currentClass);
                    metric.computeCUTMetrics(currentMethod, currentClass);
                    metric.generateReport(currentMethod.getSimpleName(), currentClass.getSimpleName(), this.projectPath);
                }
            }
        }
    }

    /**
     * Find all methods in the project, not empty and not starting with @Test
     * Compute their metrics
     * Generate JSON reports in ./results/projectName/
     */
    public void getAllMethods() throws IOException {
        // For all classes
        for(CtType<?> currentClass : this.model.getAllTypes()) {
            // For all methods
            for (CtMethod currentMethod : currentClass.getMethods()) {
                Metric metric = new Metric();
                /*
                Looking for Code Under Test, I want
                Method's body not empty
                No @test annotation
                No ClassName starting or ending with "Test"
                 */
                if (currentMethod.getBody() != null && !currentMethod.getAnnotations().toString().contains("@org.junit.Test") && !currentClass.getSimpleName().startsWith("Test") && !currentClass.getSimpleName().endsWith("Test")) {
                    metric.computeMetrics(currentMethod, currentClass);
                    metric.computeCUTMetrics(currentMethod, currentClass);
                    metric.generateReport(currentMethod.getSimpleName(), currentClass.getSimpleName(), this.projectPath);
                }
            }
        }
    }

    /**
     * Helper, Extract Method Name and Class Name from File path
     * Save them in Search attributes
     */
    public void getMethodFromFile(String fullName) {
        // ToDo Add checkers
        String[] arrayName = fullName.split("\\.");
        this.methodName = arrayName[arrayName.length - 1];
        this.className = arrayName[arrayName.length - 2];
    }

    /**
     * -INTERACTIVE- Find particular classes in the project based on a file
     * Call classSearch to compute metrics and generate reports
     */
    public void listOfClassesSearch() throws IOException {
        // Ask for file path
        Scanner myObj = new Scanner(System.in);
        System.out.println("Enter path to file with classes list inside");
        String path = myObj.nextLine();
        File file = new File(path);
        // Check if file exists
        if (!file.exists()) {
            System.out.println("File not found, please enter absolute path.");
            listOfClassesSearch();
        }
        else {
            String st;
            BufferedReader br = new BufferedReader(new FileReader(file));
            while ((st = br.readLine()) != null) {
                System.out.println(st);
                this.getClassFromFile(st);
                this.classSearch();
            }
        }
    }

    /**
     * Find particular classes in the project based on a file
     * Call classSearch to compute metrics and generate reports
     * @param listClassesPath the file path
     */
    public void listOfClassesSearch(String listClassesPath) throws IOException {
        File file = new File(listClassesPath);
        // Check if file exists
        if (!file.exists()) {
            System.out.println("-listClassesPath: File not found, please enter absolute path.");
            System.exit(0);
        }
        else {
            BufferedReader reader = new BufferedReader(new FileReader(file));
            String line = reader.readLine();
            while (line != null) {
                System.out.println(line);
                this.getClassFromFile(line);
                this.classSearch();
                line = reader.readLine();
            }
        }
    }

    /**
     * Find all methods in the project, not empty and not starting with @Test
     * Compute their metrics
     * Generate JSON reports in ./results/projectName/
     */
    public void getAllClasses() throws IOException {
        // For all classes
        for (CtClass<?> currentClass : this.model.getElements(new TypeFilter<CtClass>(CtClass.class))) {
            Metric metric = new Metric();
            System.out.println(currentClass.getQualifiedName().toString());
            if (currentClass.getPosition().getFile() == null) continue;
            metric.computeMetrics(currentClass);
            metric.generateReport(currentClass.getSimpleName(), this.projectPath);
        }
    }

    /**
     * Helper, Extract Method Name and Class Name from File path
     * Save them in Search attributes
     */
    public void getClassFromFile(String fullName) {
        // ToDo Add checkers
        this.className = fullName;
    }

    /**
     * -INTERACTIVE- Find a particular class in the project based on a className
     * Call classSearch to compute metrics and generate reports
     */
    public void singleClassSearch() throws IOException {
        // ToDo Add checkers
        Scanner myObj = new Scanner(System.in);
        System.out.println("Enter class you want to analyze [format: org.whatever.className]");
        this.className = myObj.nextLine();
        classSearch();
    }

    public void singleClassSearch(String className) throws IOException {
        this.className = className;
        classSearch();
    }

    /**
     * Find a particular class in the project
     * Compute its metrics
     * Generate JSON report in ./results/projectName/
     */
    public void classSearch() throws IOException {
        Boolean classFound = false;
        Metric metric = new Metric();

        // For all classes
        for (CtClass<?> currentClass : this.model.getElements(new TypeFilter<CtClass>(CtClass.class))) {
            // Match class name
            if (currentClass.getQualifiedName().toString().equals(this.className)) {
                classFound = true;
                metric.computeMetrics(currentClass);
                metric.generateReport(this.className.toString(), this.projectPath);
                break;
            }
        }
        // Error handlers
        if (!classFound) {
            System.out.println("No class \"" + this.className + "\" found.");
        }
    }

}
