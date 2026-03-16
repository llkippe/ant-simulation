package de.lucakippe;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import de.lucakippe.simulation.Simulation;
import processing.core.PApplet;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class App {
    public static void main(String[] args) {
        int[] foodCount = {2, 4, 8};
        int[] foodSpawnInterval = {1000, 2000, 4000};

        ExecutorService executor = Executors.newFixedThreadPool(4);
        for (int i = 0; i < foodCount.length; i++) {
            for (int j = 0; j < foodSpawnInterval.length; j++) {
                final int foodIndex = i;
                final int spawnIndex = j;

                executor.submit(() -> {
                    Simulation sim = new Simulation(false,true, foodCount[foodIndex], foodSpawnInterval[spawnIndex]);
                    
                });
                executor.submit(() -> {
                    Simulation sim = new Simulation(false, false,foodCount[foodIndex], foodSpawnInterval[spawnIndex]);
                    
                });
            }
        }

        executor.shutdown();
        try {
            // Wait for all tasks to finish (timeout after 1 hour)
            executor.awaitTermination(1, TimeUnit.HOURS);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    
    //    Simulation sim = new Simulation(true, true, 2, 1500);
        
    //    Renderer visualizer = new Renderer(sim); // Pass the simulation to the renderer
    //    PApplet.runSketch(new String[]{"AntSimulation"}, visualizer);
    }
}
        