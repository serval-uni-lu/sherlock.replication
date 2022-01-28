package base;

import java.io.IOException;

public class Main {

    public static void main(String [] args) throws IOException {
        // ----- ARGS -----
        int i = 0;
        String arg;
        String projectPath = "";
        String listMethodsPath = "";
        String listClassesPath = "";

        // Usage
        if (args.length == 0) {
            System.out.println("Usage: ./MetricExtractor.sh\n");
            System.out.println("* INTERACTIVE *");
            System.out.println("-interactive : Open an interactive menu\n");
            System.out.println("* OPTION BASED *");
            System.out.println("-projectPath : Path to the project sources. ex: -projectPath /sample/path\n");
            System.out.println("Following options all require projectPath.");
            System.out.println("-listMethodsPath : Path to a file.txt containing className.methodName per line. ex: -listMethodsPath /sample/list.txt");
            System.out.println("-listclassesPath : Path to a file.txt containing org.whatever.className per line. ex: -listclassesPath /sample/list.txt");
            System.out.println("-getAllMethods : Get Metrics for all Methods (CUT)");
            System.out.println("-getAllTestMethods : Get Metrics for all Test Methods");
            System.exit(0);
        }

        while (i < args.length && args[i].startsWith("-")) {
            arg = args[i++];
            if (arg.equals("-projectPath")) {
                if (i < args.length) {
                    projectPath = args[i++];
                } else {
                    System.err.println("-projectPath requires a path");
                    System.exit(0);
                }
            }
            else if (arg.equals("-listMethodsPath")) {
                if (i < args.length) {
                    listMethodsPath = args[i++];
                } else {
                    System.err.println("-listMethodsPath requires a path");
                    System.exit(0);
                }
            }
            else if (arg.equals("-listClassesPath")) {
                if (i < args.length) {
                    listClassesPath = args[i++];
                } else {
                    System.err.println("-listClassesPath requires a path");
                    System.exit(0);
                }
            }
            else if (arg.equals("-interactive")) {
                Menu menu = new Menu();
                System.exit(0);
            }
            else if (arg.equals("-getAllMethods")) {
                Search search = new Search(projectPath);
                System.out.println("\nAnalyzing project: " + projectPath);
                search.getAllMethods();
                System.exit(0);
            }
            else if (arg.equals("-getAllTestMethods")) {
                Search search = new Search(projectPath);
                System.out.println("\nAnalyzing project: " + projectPath);
                search.getAllTestMethods();
                System.exit(0);
            }
        }

        if (!projectPath.equals("") && !listMethodsPath.equals("")) {
            Search search = new Search(projectPath);
            System.out.println("\nAnalyzing project: " + projectPath);
            search.listOfMethodsSearch(listMethodsPath);
        }

        if (!projectPath.equals("") && !listClassesPath.equals("")) {
            Search search = new Search(projectPath);
            System.out.println("\nAnalyzing project: " + projectPath);
            search.listOfClassesSearch(listClassesPath);
        }

        System.exit(0);
    }
}
