
package de.lucakippe.simulation;


public class Simulation {
    public final static int WIDTH = 600;
    public final static int HEIGHT = 600;
    final static int NUM_ANTS = 2500;
    final static double PERCENT_SCOUT_ANTS = 0.1; 


    private int maxStepCount;
    public int stepCount = 0;
    private boolean isRendered;

    private Ants ants;
    private Nest nest;


    private static final int MIN_DIST_TO_NEST = 200;
    private static final int MIN_DIST_BETWEEN_FOODSOURCES = 150;
    private static int foodSourceSize = 13;
    public int foodSourceCount;
    public int foodSpawnIntervall;
    private Food[] foodSources;

    MetricsManager metricsManager;
    

    private Pheromones pheromones;

    
    public Simulation(boolean isRendered, boolean antiPheromoneActive, int simFoodSources, int newFoodSpawnIntervall) {
        foodSourceCount = simFoodSources;
        foodSpawnIntervall = newFoodSpawnIntervall;
        maxStepCount = newFoodSpawnIntervall * 8;
        
        
        nest = new Nest(300, 300, 35);
        foodSources = new Food[foodSourceCount];
        metricsManager = new MetricsManager(nest, foodSources, foodSpawnIntervall, foodSourceCount, antiPheromoneActive, NUM_ANTS);
        for (int i = 0; i < foodSources.length; i++) {
            foodSources[i] = createRandomFoodSource();
        }
        
        
        pheromones = new Pheromones();
        ants = new Ants(pheromones, nest, foodSources,metricsManager, antiPheromoneActive);


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

        if(stepCount % foodSpawnIntervall == 0) {
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


            Food newFood = new Food(posX, posY, foodSourceSize, stepCount); 
            metricsManager.reportSourceCreated(newFood.getId(), stepCount);
            return newFood;
        }

        // fallback if map is crowded
        return new Food(
            (int)(Math.random() * WIDTH),
            (int)(Math.random() * HEIGHT),
            foodSourceSize,
            stepCount
        );
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
