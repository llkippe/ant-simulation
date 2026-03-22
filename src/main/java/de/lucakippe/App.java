package de.lucakippe;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import de.lucakippe.simulation.Simulation;
import processing.core.PApplet;
import java.util.concurrent.TimeUnit;

public class App {
    public static void main(String[] args) {
        // Definition der Batch-Größe
        int N = 2; 

        // Deine gewünschten Konfigurationen: {FoodSources, SpawnInterval}
        // (4 Quellen / 2000 Intervall überschneidet sich in deinen Gruppen, 
        //  daher schreiben wir es hier nur einmal auf, um Redundanz zu sparen)
        int[][] configs = {
           // {2, 4000},
            {2, 1000},

            //{2, 2000}, {4, 2000}, {8, 2000}, // Gruppe 1 (Quellen im Fokus)
            //{4, 1000}, {4, 4000}             // Gruppe 2 (Intervalle im Fokus)
        };

        boolean[] antiPheromones = {true, false};

        ExecutorService executor = Executors.newFixedThreadPool(4);

        for (int[] config : configs) {
            for (boolean ap : antiPheromones) {
                int foodCount = config[0];
                int interval = config[1];

                // Generiere DEN SELBEN Timestamp für den gesamten Batch
                String timestamp = String.valueOf(System.currentTimeMillis());
                String baseDirName = timestamp + "_" + foodCount + "_" + interval + "_" + ap;
            
                for (int run = 1; run <= N; run++) {
                    final int currentRun = run;
                    executor.submit(() -> {
                    try {
                        new Simulation(false, ap, foodCount, interval, baseDirName, currentRun);
                    } catch (Throwable t) { // Catch Throwable, not just Exception
                        System.err.println("Simulation " + currentRun + " crashed!");
                        t.printStackTrace();
                    }
                });
                }
            }
        }

                executor.shutdown();
        try {
            // Wait for all tasks to finish (timeout after 1 hour)
            executor.awaitTermination(1, TimeUnit.HOURS);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        
       // runVis();
        
    }

    public static void runVis() {
        int foodCount = 8;
        int interval = 1000;
        boolean antiPheromones = true;

        String timestamp = String.valueOf(System.currentTimeMillis());
        String baseDirName = timestamp + "_" + foodCount + "_" + interval + "_" + antiPheromones;

        Simulation sim = new Simulation(true, antiPheromones, foodCount, interval, baseDirName, 0);
        
        
       Renderer visualizer = new Renderer(sim); // Pass the simulation to the renderer
       PApplet.runSketch(new String[]{"AntSimulation"}, visualizer);
    }



}
        