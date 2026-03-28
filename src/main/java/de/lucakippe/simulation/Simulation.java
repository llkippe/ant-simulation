
package de.lucakippe.simulation;

import java.util.Random;

public class Simulation {
    public final static int WIDTH = 800;
    public final static int HEIGHT = 800;
    final static int NUM_ANTS = 1300;
    final static double PERCENT_SCOUT_ANTS = 0.1; 
    final static boolean bordersActive = true;


    private int maxStepCount;
    public int stepCount = 0;

    private Ants ants;
    private Nest nest;


    public static final int MIN_DIST_TO_NEST = 200;
    public static final int MIN_DIST_BETWEEN_FOODSOURCES = 150;
    private static int foodSourceSize = 15;
    private static int nestSize = 45;
    public int foodSourceCount;
    public int foodSpawnIntervall;
    private Food[] foodSources;
    private int nextFoodSourceId;

    MetricsManager metricsManager;
    

    private Pheromones pheromones;

    Random random;

    
    public Simulation(boolean isRendered, boolean antiPheromoneActive, int simFoodSources, int newFoodSpawnIntervall, String baseDirName, int runIndex, long seed) {
        this.random = new Random(seed);



        foodSourceCount = simFoodSources;
        foodSpawnIntervall = newFoodSpawnIntervall;
        
        // Ein Basis-Faktor, wie viele "Events" wir mindestens sehen wollen
        int minEvents = 8; 
        // Wir nehmen entweder (Anzahl Quellen * 1.5) oder mindestens 6
        int eventCount = Math.max(minEvents, (int)(simFoodSources * 1.5));
        maxStepCount = newFoodSpawnIntervall * eventCount;

        nextFoodSourceId = 0;
        
        
        
        nest = new Nest(WIDTH / 2, HEIGHT / 2, nestSize);
        foodSources = new Food[foodSourceCount];
        metricsManager = new MetricsManager(nest, foodSources, foodSpawnIntervall, foodSourceCount, antiPheromoneActive, NUM_ANTS, baseDirName, runIndex, seed);
      
        
        for (int i = 0; i < foodSources.length; i++) {
            foodSources[i] = createRandomFoodSource();
        }
        
        
        pheromones = new Pheromones();
        ants = new Ants(pheromones, nest, foodSources,metricsManager, antiPheromoneActive, seed);


        if(!isRendered ) {
            while(stepCount < maxStepCount) {
                update();
            }
            PythonScriptRunner.runPythonScript(metricsManager.getSimulationDataDir().toString());
            System.out.println("Simulation Finished");    
        }
        // simulation finished
        
        return;
    }


    public void update() {
        stepCount++;

        ants.update();
        pheromones.update(stepCount);

        if(stepCount % foodSpawnIntervall == 0) {
            replaceOldestFoodSource();
        }

        metricsManager.update(stepCount, nest);
    }

    public void replaceOldestFoodSource() {
        if (foodSources.length == 0) return;

        // 1. Berechne das Alter jeder Quelle und die Gesamtsumme des Alters
        double[] ages = new double[foodSources.length];
        double totalAge = 0;

        for (int i = 0; i < foodSources.length; i++) {
            // Alter = Aktueller Schritt minus Geburts-Schritt
            ages[i] = (double) (stepCount - foodSources[i].getCreatedAtStep());
            totalAge += ages[i];
        }

        // 2. Würfeln (Roulette Wheel with random seed implementation)
        double roll = random.nextDouble() * totalAge;
        double cumulativeAge = 0;
        int indexToDelete = 0;

        for (int i = 0; i < foodSources.length; i++) {
            cumulativeAge += ages[i];
            if (roll <= cumulativeAge) {
                indexToDelete = i;
                break;
            }
        }

        // 3. Löschen und Ersetzen
        metricsManager.reportSourceDeleted(foodSources[indexToDelete].getId(), stepCount);
        foodSources[indexToDelete] = createRandomFoodSource();
        
    }



    private Food createRandomFoodSource() {
        int maxTries = 1000;

        for (int t = 0; t < maxTries; t++) {

            int posX = random.nextInt(WIDTH);
            int posY = random.nextInt(HEIGHT);

            
            // check nest distance
            if (distWrapped(posX, posY, nest.posX, nest.posY)
                    < MIN_DIST_TO_NEST) {
                continue;
            }

            // check other food sources
            boolean tooClose = false;

            for (Food f : foodSources) {
                if (f == null) continue;

                if (distWrapped(posX, posY, f.getPosX(), f.getPosY())
                        < MIN_DIST_BETWEEN_FOODSOURCES) {
                    tooClose = true;
                    break;
                }
            }

            if (tooClose) continue;


            Food newFood = new Food(posX, posY, foodSourceSize, stepCount, nextFoodSourceId); 
            nextFoodSourceId++;
            metricsManager.reportSourceCreated(newFood.getId(), stepCount);
            return newFood;
        }


        // determenistic fallback if map is crowded
        Food newFood =  new Food(
            nest.getPosX() - MIN_DIST_TO_NEST,
            nest.getPosY() - MIN_DIST_TO_NEST ,
            foodSourceSize,
            stepCount,
            nextFoodSourceId
        );

        System.out.println("WARNING. No Food spot found");

        nextFoodSourceId++;
        return newFood;
    }

    public static double distWrapped(int x1, int y1, int x2, int y2) {
        int dx = Math.abs(x1 - x2);
        int dy = Math.abs(y1 - y2);

        // Calculate the wrap-around distances
        int wrappedDx = WIDTH - dx;
        int wrappedDy = HEIGHT - dy;

        // Use the minimum of the direct and wrap-around distances
        dx = Math.min(dx, wrappedDx);
        dy = Math.min(dy, wrappedDy);

        return Math.sqrt(dx * dx + dy * dy);
    }

    public static boolean outsideOfBorder(double x, double y) {
        if(y < 0 || y >= HEIGHT || x < 0 || x >= WIDTH) return true;
        return false;
    }

    public Ants getAnts() {
        return ants;
    }   

    public Pheromones getPheromones() {
        return pheromones;
    }

    public Nest getNest() {
        return nest;
    }

    public Food[] getFoodSources() {
        return foodSources;
    }

    public int getStepCount() {
        return stepCount;
    }


}
