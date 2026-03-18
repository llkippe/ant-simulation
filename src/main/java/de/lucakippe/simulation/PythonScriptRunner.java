package de.lucakippe.simulation; 

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class PythonScriptRunner {
    public static void runPythonScript(String simulationId) {
        // Pfad zum Python-Interpreter und zum Skript
        String pythonInterpreter = "python3"; // oder "python3" je nach System
        String scriptPath = "build_graphs.py";


        // Argumente für das Python-Skript
        String[] scriptArgs = {simulationId};

        // ProcessBuilder erstellen
        ProcessBuilder processBuilder = new ProcessBuilder();
        processBuilder.command(pythonInterpreter, scriptPath);
        processBuilder.command().addAll(java.util.Arrays.asList(scriptArgs));

        try {
            // Prozess starten
            Process process = processBuilder.start();

            // Ausgabe des Skripts lesen (optional)
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(process.getInputStream())
            );

            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println(line);
            }

            // Auf Beendigung des Prozesses warten
            int exitCode = process.waitFor();
            System.out.println("Python-Skript beendet mit Exit-Code: " + exitCode);

        } catch (IOException | InterruptedException e) {
            e.printStackTrace();
        }
    }
}
