
package de.lucakippe.simulation;

import de.lucakippe.util.Util;

public class Simulation {
    public final static int WIDTH = 600;
    public final static int HEIGHT = 600;
    final static int NUM_ANTS = 2500;
    final static double PERCENT_SCOUT_ANTS = 0.15; 


    private int maxStepCount = 10000;
    static int stepCount = 0;
    private boolean isRendered;

    private Ants ants;
    private Nest nest;


    private static final int MIN_DIST_TO_NEST = 200;
    private static final int MIN_DIST_BETWEEN_FOODSOURCES = 150;
    private int foodSourceSize = 13;
    private int simulatniousFoodSources = 3;
    private int newFoodSpawnIntervall = 2000;
    private Food[] foodSources;

    MetricsManager metricsManager;
    

    private Pheromones pheromones;

    
    public Simulation(boolean isRendered) {
        
        
        nest = new Nest(300, 300, 20);
        foodSources = new Food[simulatniousFoodSources];
        metricsManager = new MetricsManager(nest, foodSources);
        for (int i = 0; i < foodSources.length; i++) {
            foodSources[i] = createRandomFoodSource();
        }
        
        
        pheromones = new Pheromones();
        ants = new Ants(pheromones, nest, foodSources,metricsManager);


        this.isRendered = isRendered;
        if(!isRendered ) {
            update();
        }

    }

    public void update() {
        stepCount++;
        if(stepCount >= maxStepCount) {
            System.out.println("Simulation Finished");
            return;
        }


        ants.update();
        pheromones.update();

        if(stepCount % newFoodSpawnIntervall == 0) {
            replaceOldestFoodSource();
        }

        metricsManager.update(stepCount, nest);


        if(!isRendered) {
            update();
        }
    }

    public void replaceOldestFoodSource() {
        int oldestIndex = 0;
        // find the oldest food source
        for (int i = 1; i < foodSources.length; i++) {
            if (foodSources[i].getCreatedAtStep()
                < foodSources[oldestIndex].getCreatedAtStep()) {
                oldestIndex = i;
            }
        }
        
        metricsManager.reportSourceDeleted(foodSources[oldestIndex].getId(), stepCount);

        foodSources[oldestIndex] = createRandomFoodSource();
    }



    private Food createRandomFoodSource() {
        int maxTries = 50;

        for (int t = 0; t < maxTries; t++) {

            int posX = (int) (Math.random() * WIDTH);
            int posY = (int) (Math.random() * HEIGHT);

            

            // check nest distance
            if (Util.dist(posX, posY, nest.posX, nest.posY)
                    < MIN_DIST_TO_NEST) {
                continue;
            }

            // check other food sources
            boolean tooClose = false;

            for (Food f : foodSources) {
                if (f == null) continue;

                if (Util.dist(posX, posY, f.getPosX(), f.getPosY())
                        < MIN_DIST_BETWEEN_FOODSOURCES) {
                    tooClose = true;
                    break;
                }
            }

            if (tooClose) continue;


            Food newFood = new Food(posX, posY, foodSourceSize); 
            metricsManager.reportSourceCreated(newFood.getId(), stepCount);
            return newFood;
        }

        // fallback if map is crowded
        return new Food(
            (int)(Math.random() * WIDTH),
            (int)(Math.random() * HEIGHT),
            foodSourceSize
        );
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
