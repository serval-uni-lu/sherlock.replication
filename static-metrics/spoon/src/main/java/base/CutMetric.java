package base;


import spoon.reflect.declaration.CtMethod;
import spoon.reflect.declaration.CtType;

public class CutMetric {
    // Arguments declaration
    private int nbLines;
    private int nbCyclo;
    private int nbAsyncWaits;
    private int nbThreads;
    private int nbDates;
    private int nbRandoms;
    private int nbFiles;
    private int depthOfInheritance;
    private String methodBody;
    private String className;
    private String methodName;

    public CutMetric(Metric metric) {
        this.nbLines = metric.getNbLines();
        this.nbCyclo = metric.getNbCyclo();
        this.nbAsyncWaits = metric.getNbAsyncWaits();
        this.nbThreads = metric.getNbThreads();
        this.nbDates = metric.getNbDates();
        this.nbRandoms = metric.getNbRandoms();
        this.nbFiles = metric.getNbFiles();
        this.depthOfInheritance = metric.getDepthOfInheritance();
        this.methodBody = metric.getMethodBody();
        this.methodName = metric.getMethodName();
        this.className = metric.getClassName();
    }

    public int getNbLines() {
        return nbLines;
    }

    public int getNbCyclo() {
        return nbCyclo;
    }

    public int getNbAsyncWaits() {
        return nbAsyncWaits;
    }

    public int getNbThreads() {
        return nbThreads;
    }

    public int getNbDates() {
        return nbDates;
    }

    public int getNbRandoms() {
        return nbRandoms;
    }

    public int getNbFiles() {
        return nbFiles;
    }

    public int getDepthOfInheritance() {
        return depthOfInheritance;
    }

    public String getMethodBody() {
        return methodBody;
    }

    public String getClassName() {
        return className;
    }

    public String getMethodName() {
        return methodName;
    }
}
