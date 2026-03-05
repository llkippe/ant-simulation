package de.lucakippe.simulation;

import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.Files;
import de.lucakippe.util.*;

public class MetricsManager {
    private Path simulationDataDir;


    private int interval = 100;
    private Nest nest;
    Food[] foodSources;

    private PrintWriter sourceMetricsWriter;
    private HashMap<Integer, Integer> lastFoodCountPerSource = new HashMap<>();
    private HashMap<Integer, Integer> sourceCreationSteps = new HashMap<>();
    private HashMap<Integer, Integer> sourceDeletionSteps = new HashMap<>();



    private PrintWriter globalMetricsWriter;
    private int dissappointmentsInCurrentInterval = 0;
    private ArrayList<Double> foodPathEfficiencies = new ArrayList<>();
    private ArrayList<Double> nestPathEfficiencies = new ArrayList<>();
    private Map<Integer, Double> distanceNestFoodCache = new HashMap<>();   


   

    MetricsManager(Nest nest, Food[] foodSources) {
        this.nest = nest;
        this.foodSources = foodSources;

        try {
            // Create 'data' directory if it doesn't exist
            Path dataDir = Paths.get("data");
            if (!Files.exists(dataDir)) {
                Files.createDirectory(dataDir);
            }

            // Create a unique subfolder for this simulation
            String timestamp = String.valueOf(System.currentTimeMillis());
            simulationDataDir = dataDir.resolve(timestamp);
            Files.createDirectory(simulationDataDir);

            // Initialize writers for both metrics files
            sourceMetricsWriter = new PrintWriter(simulationDataDir.resolve("source_metrics.csv").toFile());
            sourceMetricsWriter.println("step,source_id,amount,throughput,creation_step,deletion_step");

            globalMetricsWriter = new PrintWriter(simulationDataDir.resolve("global_metrics.csv").toFile());
            globalMetricsWriter.println("step,avg_step_efficeny_to_food,avg_step_efficeny_to_nest,dissapointmentRate");

        } catch (Exception e) {
            e.printStackTrace();
        }
    }


    public void update(int currentStep, Nest nest) {
        if(currentStep % interval != 0) return;
        writeSourceMetrics(currentStep, nest);
        writeGlobalMetrics(currentStep);
    }


    private double getCachedDistance(int foodSourceId) {
        return distanceNestFoodCache.computeIfAbsent(foodSourceId, k -> {
            for(Food food : foodSources) {
                if(food.getId() == foodSourceId) {
                    return Util.dist(food.getPosX(), food.getPosY(), nest.posX, nest.posY); 
                    
                }
            }
            System.out.println("Didnt find " + foodSourceId);
            return -1.0;
        });
    }

    public void reportStepsToFood(int pathLength, int foodSourceId) {
        double directDist = getCachedDistance(foodSourceId);
        if (directDist > 0 && pathLength > 0) {
            foodPathEfficiencies.add(directDist / (double) pathLength);
        }
    }

    public void reportStepsToNest(int pathLength, int comingFromFoodSourceId) {
        double directDist = getCachedDistance(comingFromFoodSourceId);
        if (directDist > 0 && pathLength > 0) {
            nestPathEfficiencies.add(directDist / (double) pathLength);
        }
    }

    public Double calculateAverage(ArrayList<Double> list ) {
        if(list.isEmpty()) return 0.0;
        double sum = 0.0;
        for(double i : list) sum += i;
        return (Double) sum / list.size();
    }

    public void reportAntDissapointed() {
        dissappointmentsInCurrentInterval++;
    }


    public void writeGlobalMetrics(int currentStep) {
    double avgFoodEfficiency = calculateAverage(foodPathEfficiencies);
    double avgNestEfficiency = calculateAverage(nestPathEfficiencies);
    

    // CSV Header suggestion: Step, FoodEfficiency, NestEfficiency, DisappointmentRate
    globalMetricsWriter.println(currentStep + "," + avgFoodEfficiency + "," + avgNestEfficiency + "," + dissappointmentsInCurrentInterval);
    globalMetricsWriter.flush();

    // Resetting for the next interval
    foodPathEfficiencies.clear();
    nestPathEfficiencies.clear();
    dissappointmentsInCurrentInterval = 0;
}

    


    public void reportSourceCreated(int sourceId, int currentStep) {
        sourceCreationSteps.put(sourceId, currentStep);
    }

    public void reportSourceDeleted(int sourceId, int currentStep) {
        sourceDeletionSteps.put(sourceId, currentStep);
    }

    public void writeSourceMetrics(int currentStep, Nest nest) {
        HashMap<Integer, Integer> currentData = nest.getFoodPerSourceMap();
        
        for(Integer sourceId : currentData.keySet()) {
            int currentAmount = currentData.get(sourceId);
            int lastAmount = lastFoodCountPerSource.getOrDefault(sourceId, 0);
            int throughput = currentAmount - lastAmount;
            lastFoodCountPerSource.put(sourceId, currentAmount);

            int creationStep = sourceCreationSteps.getOrDefault(sourceId, -1);
            int deletionStep = sourceDeletionSteps.getOrDefault(sourceId, -1);
            
            sourceMetricsWriter.println(
                currentStep + "," +
                sourceId + "," +
                currentAmount + "," +
                throughput + "," +
                creationStep + "," +
                deletionStep
            );
        }
        
        sourceMetricsWriter.flush();
    }
}