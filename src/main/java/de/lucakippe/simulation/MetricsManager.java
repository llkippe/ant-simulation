package de.lucakippe.simulation;

import java.io.PrintWriter;
import java.util.HashMap;
import java.util.Map;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.Files;

public class MetricsManager {
    private Path simulationDataDir;

    
    private final int WINDOW_SIZE = 200;
    private final int INTERVAL = 20;
    private Nest nest;
    Food[] foodSources;

    private PrintWriter sourceMetricsWriter;
    private HashMap<Integer, SlidingWindow> sourceThroughputWindows = new HashMap<>();
    private HashMap<Integer, Integer> lastFoodCountPerSource = new HashMap<>();
    private HashMap<Integer, Integer> sourceCreationSteps = new HashMap<>();
    private HashMap<Integer, Integer> sourceDeletionSteps = new HashMap<>();



    private PrintWriter globalMetricsWriter;
    
    private int dissappointmentsInCurrentInterval = 0;
    private SlidingWindow dissapointmentWindow = new SlidingWindow(WINDOW_SIZE);

    private SlidingWindow foodPathWindow = new SlidingWindow(WINDOW_SIZE);
    private SlidingWindow nestPathWindow = new SlidingWindow(WINDOW_SIZE);
    private Map<Integer, Double> distanceNestFoodCache = new HashMap<>();   

    private int exploitingAntsCount = 0;


    private PrintWriter settingsWriter; 



    MetricsManager(Nest nest, Food[] foodSources, int foodSpawnIntervall, int foodSourceCount, boolean antiPheromoneActive, int totalAnts) {
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
            //String uuid = java.util.UUID.randomUUID().toString();
            simulationDataDir = dataDir.resolve(timestamp + "_" + foodSourceCount + "_" + foodSpawnIntervall + "_" + antiPheromoneActive);
            Files.createDirectory(simulationDataDir);

            // Initialize writers for both metrics files
            sourceMetricsWriter = new PrintWriter(simulationDataDir.resolve("source_metrics.csv").toFile());
            sourceMetricsWriter.println("step,source_id,amount,throughput,creation_step,deletion_step");

            globalMetricsWriter = new PrintWriter(simulationDataDir.resolve("global_metrics.csv").toFile());
            globalMetricsWriter.println("step,avg_step_efficeny_to_food,avg_step_efficeny_to_nest,dissapointmentRate,exploitingAntsCount");

            settingsWriter = new PrintWriter(simulationDataDir.resolve("settings.csv").toFile());
            settingsWriter.println("FOOD_SPAWN_INTERVALL, FOOD_SOURCE_COUNT, antiPheromoneActive,totalAnts");
            settingsWriter.println(foodSpawnIntervall + "," + foodSourceCount + "," + antiPheromoneActive + "," + totalAnts);
            settingsWriter.flush();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }


    public void update(int currentStep, Nest nest) {
        // jeder step werden sliding windows die ueber steps als zeit arbeiten geupdatet.
        dissapointmentWindow.tick(dissappointmentsInCurrentInterval);
        dissappointmentsInCurrentInterval = 0;

        HashMap<Integer, Integer> currentData = nest.getFoodPerSourceMap();
        for(Integer sourceId : currentData.keySet()) {
            int currentAmount = currentData.get(sourceId);
            int lastAmount = lastFoodCountPerSource.getOrDefault(sourceId, 0);

            // Raw throughput im aktuellen Intervall
            int throughputInInterval = currentAmount - lastAmount;
            lastFoodCountPerSource.put(sourceId, currentAmount);

            // Sliding Window für diese spezifische Quelle abrufen oder neu erstellen
            SlidingWindow window = sourceThroughputWindows.computeIfAbsent(
                sourceId, k -> new SlidingWindow(WINDOW_SIZE)
            );
            window.tick(throughputInInterval);
            
        }
        


        // nur nach ablauf des intervalls daten schreiben
        if(currentStep % INTERVAL != 0) return;
        writeSourceMetrics(currentStep, nest);
        writeGlobalMetrics(currentStep);
    }

    public void reportExploitationStart() { exploitingAntsCount++; }
    public void reportExploitationEnd() { exploitingAntsCount--; }

    


    private double getCachedDistance(int foodSourceId) {
        return distanceNestFoodCache.computeIfAbsent(foodSourceId, k -> {
            for(Food food : foodSources) {
                if(food.getId() == foodSourceId) {
                    return Simulation.distWrapped(food.getPosX(), food.getPosY(), nest.posX, nest.posY) - food.getRadius() - nest.getRadius();
                    
                }
            }
            System.out.println("Didnt find " + foodSourceId);
            return -1.0;
        });
    }

    public void reportStepsToFood(int pathLength, int foodSourceId) {
        double directDist = getCachedDistance(foodSourceId);
        if (directDist > 0 && pathLength > 0) {
            foodPathWindow.addValue(directDist / (double) pathLength);
        }
    }

    public void reportStepsToNest(int pathLength, int comingFromFoodSourceId) {
        double directDist = getCachedDistance(comingFromFoodSourceId);
        if (directDist > 0 && pathLength > 0) {
            nestPathWindow.addValue(directDist / (double) pathLength);
        }
    }

    public void reportAntDissapointed() {
        dissappointmentsInCurrentInterval++;
    }


    public void writeGlobalMetrics(int currentStep) {
        // Prüfen, ob schon Daten da sind (count > 0). Wenn ja: Durchschnitt holen, sonst "NaN"
        String foodStr = (foodPathWindow.getCount() > 0) ? String.valueOf(foodPathWindow.getAverage()) : "NaN";
        String nestStr = (nestPathWindow.getCount() > 0) ? String.valueOf(nestPathWindow.getAverage()) : "NaN";

        double avgDisappointmentProStep = dissapointmentWindow.getAverage();
    
        globalMetricsWriter.println(currentStep + "," + foodStr + "," + nestStr + "," + avgDisappointmentProStep + "," + exploitingAntsCount);
        globalMetricsWriter.flush();

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
            // int lastAmount = lastFoodCountPerSource.getOrDefault(sourceId, 0);

            // // Raw throughput im aktuellen Intervall
            // int throughputInInterval = currentAmount - lastAmount;
            // lastFoodCountPerSource.put(sourceId, currentAmount);
            // Sliding Window für diese spezifische Quelle abrufen oder neu erstellen
            SlidingWindow window = sourceThroughputWindows.computeIfAbsent(
                sourceId, k -> new SlidingWindow(WINDOW_SIZE)
            );
            // Geglätteten Durchsatz holen
            double smoothedThroughput = window.getAverage();

            int creationStep = sourceCreationSteps.getOrDefault(sourceId, -1);
            int deletionStep = sourceDeletionSteps.getOrDefault(sourceId, -1);
            
            sourceMetricsWriter.println(
                currentStep + "," +
                sourceId + "," +
                currentAmount + "," +
                smoothedThroughput + "," +
                creationStep + "," +
                deletionStep
            );
        }
        
        sourceMetricsWriter.flush();
    }

    public Path getSimulationDataDir() {
        return simulationDataDir;
    }
}