package de.lucakippe;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import de.lucakippe.simulation.Simulation;
import processing.core.PApplet;
import java.util.concurrent.TimeUnit;

public class App {
    public static void main(String[] args) {
       
   // runBatches();
     
         
    runVis();
        
    }

    public static void runVis() {
        int foodCount = 6;
        int interval = 1500;
        boolean antiPheromones = true;

        String timestamp = String.valueOf(System.currentTimeMillis());
        long runSeed = timestamp.hashCode(); 
        System.out.println(runSeed);
        String baseDirName = timestamp + "_" + foodCount + "_" + interval + "_" + antiPheromones;

        Simulation sim = new Simulation(true, antiPheromones, foodCount, interval, baseDirName, 0, 169624657);
        
        
       Renderer visualizer = new Renderer(sim); // Pass the simulation to the renderer
       PApplet.runSketch(new String[]{"AntSimulation"}, visualizer);
    }

   public static void runBatches() {
 
        // deutlicher unterschied beobachten koennen. 
        // 6, 1500 fairness und global avg, recovery zeiten, pfad recovery zeiten

        //{6, 1500} , {3, 3000}
//,{6,1500}, {9,1500},  {6, 3000} , {6, 1000}
         

        int N = 50;
        int[][] configs = {{3, 3000}, {3, 1500}, {3, 6000}, {1, 3000}};

        boolean[] antiPheromones = {true, false};

        ExecutorService executor = Executors.newFixedThreadPool(4);

        for (int[] config : configs) {
            int foodCount = config[0];
            int interval = config[1];   
            String timestamp = String.valueOf(System.currentTimeMillis());

            // Iterate through the run indices first
            for (int run = 1; run <= N; run++) {
                // Generate ONE seed for this specific run number
                long runSeed = timestamp.hashCode() + run; 
                
                for (boolean ap : antiPheromones) {
                    final int currentRun = run;
                    final boolean currentAp = ap;
                    
                    // Separate directories to prevent file conflicts
                    String baseDirName = timestamp + "_" + foodCount + "_" + interval + "_" + ap;
                    
                    executor.submit(() -> {
                        try {
                            // Both ap=true and ap=false will now use runSeed
                            new Simulation(false, currentAp, foodCount, interval, baseDirName, currentRun, runSeed);
                        } catch (Throwable t) {
                            System.err.println("Simulation " + currentRun + " (AP=" + currentAp + ") crashed!");
                            t.printStackTrace();
                        }
                    });
                }
            }
        }

        executor.shutdown();
        try {
            executor.awaitTermination(2, TimeUnit.HOURS);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }



}
        