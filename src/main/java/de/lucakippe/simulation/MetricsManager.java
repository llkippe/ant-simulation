package de.lucakippe.simulation;

import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.HashMap;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.Files;

public class MetricsManager {
    private Path simulationDataDir;

    private int interval = 100;

    private PrintWriter sourceMetricsWriter;
    private HashMap<Integer, Integer> lastFoodCountPerSource = new HashMap<>();
    private HashMap<Integer, Integer> sourceCreationSteps = new HashMap<>();
    private HashMap<Integer, Integer> sourceDeletionSteps = new HashMap<>();



    private PrintWriter globalMetricsWriter;
    private int dissappointmentsInCurrentInterval = 0;
    private ArrayList<Integer> stepsToFoodList = new ArrayList<>();
    private ArrayList<Integer> stepsToNestList = new ArrayList<>();


   

    MetricsManager() {
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
            globalMetricsWriter.println("step,avg_steps_to_food,avg_steps_to_nest");

        } catch (Exception e) {
            e.printStackTrace();
        }
    }


    public void update(int currentStep, Nest nest) {
        if(currentStep % interval != 0) return;
        writeSourceMetrics(currentStep, nest);
        writeGlobalMetrics(currentStep);
    }

    public void reportStepsToFood(int pathLength) {
        stepsToFoodList.add(pathLength);
    }
    public void reportStepsToNest(int pathLength) {
        stepsToNestList.add(pathLength);
    }
    public float calculateAverage(ArrayList<Integer> list ) {
        if(list.isEmpty()) return 0;
        int sum = 0;
        for(int i : list) sum += i;
        return (float) sum / list.size();
    }
    public void writeGlobalMetrics(int currentStep) {
        float avgStepsToFood = calculateAverage(stepsToFoodList);
        float avgStepsToNest = calculateAverage(stepsToNestList);

        globalMetricsWriter.println(currentStep + "," + avgStepsToFood +","  + avgStepsToNest);
        globalMetricsWriter.flush();

        stepsToFoodList.clear();
        stepsToNestList.clear();
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