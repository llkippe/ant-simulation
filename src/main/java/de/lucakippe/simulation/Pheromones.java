package de.lucakippe.simulation;




public class Pheromones {
    private double[] homeGrid;
    private double[] foodGrid;
    private double[] foodDepletedGrid;

  

    final static double LINEAR_THRESHHOLD = 0.05;
    final static double LINEAR_DROPOFF = 0.0001;
    final static double EVAPORATION_RATE = 0.005;
    final static double FOOD_DEPLETED_EVAPORTAION_RATE = 0.0025; // half of original evaporation rate

    final static double DIFFUSION_RATE = 0.04;
    final static double FOOD_DEPLETED_DIFFUSION_RATE = 0.25;

    final static double MAX_PHEROMONE_STRENGTH = 13.0;

   

    public Pheromones() {
        homeGrid = new double[Simulation.WIDTH * Simulation.HEIGHT];
        foodGrid = new double[Simulation.WIDTH * Simulation.HEIGHT];
        foodDepletedGrid = new double[Simulation.WIDTH * Simulation.HEIGHT];
    }

    void update() {
        evaporate();
        diffuse();
    }

    public void evaporate() {
    for (int i = 0; i < homeGrid.length; i++) {
        if (homeGrid[i] > 0) {

            if(homeGrid[i] > MAX_PHEROMONE_STRENGTH) homeGrid[i] = MAX_PHEROMONE_STRENGTH;

            if (homeGrid[i] > LINEAR_THRESHHOLD) {
                homeGrid[i] *= (1 - EVAPORATION_RATE);
            } else {
                homeGrid[i] -= LINEAR_DROPOFF;
            }
            if (homeGrid[i] < 0) homeGrid[i] = 0; // Sicherstellen, dass es nicht negativ wird
        }

        if (foodGrid[i] > 0) {
            if(foodGrid[i] > MAX_PHEROMONE_STRENGTH) foodGrid[i] = MAX_PHEROMONE_STRENGTH;

            if (foodGrid[i] > LINEAR_THRESHHOLD) {
                foodGrid[i] *= (1 - EVAPORATION_RATE);
            } else {
                foodGrid[i] -= LINEAR_DROPOFF;
            }
            if (foodGrid[i] < 0) foodGrid[i] = 0;
        }

        if(foodDepletedGrid[i] > 0) {
            if(foodDepletedGrid[i] > MAX_PHEROMONE_STRENGTH) foodDepletedGrid[i] = MAX_PHEROMONE_STRENGTH;

            if (foodDepletedGrid[i] > LINEAR_THRESHHOLD) {
                foodDepletedGrid[i] *= (1 - FOOD_DEPLETED_EVAPORTAION_RATE);
            } else {
                foodDepletedGrid[i] -= LINEAR_DROPOFF;
            }
            if (foodDepletedGrid[i] < 0) foodDepletedGrid[i] = 0;
        }
    }
}

    public void diffuse() {
        // 1. Create temporary arrays to store the results
        double[] newHomeGrid = new double[homeGrid.length];
        double[] newFoodGrid = new double[foodGrid.length];
        double[] newFoodDepletedGrid = new double[foodDepletedGrid.length];

        int W = Simulation.WIDTH;
        int H = Simulation.HEIGHT;

        for (int i = 0; i < homeGrid.length; i++) {
            int x = i % W;
            int y = i / W;

            double sumHome = 0;
            double sumFood = 0;
            double sumFoodDepleted = 0;

            // 2. Sample the 3x3 neighborhood (including the center)
            for (int offsetX = -1; offsetX <= 1; offsetX++) {
                for (int offsetY = -1; offsetY <= 1; offsetY++) {

                    // 3. The "Wrap-around" logic
                    int neighborX = (x + offsetX + W) % W;
                    int neighborY = (y + offsetY + H) % H;
                    int neighborIndex = neighborY * W + neighborX;

                    sumHome += homeGrid[neighborIndex];
                    sumFood += foodGrid[neighborIndex];
                    sumFoodDepleted += foodDepletedGrid[neighborIndex];
                }
            }

            // 4. Calculate the average and apply the rate
            double avgHome = sumHome / 9.0;
            double avgFood = sumFood / 9.0;
            double avgFoodDepleted = sumFoodDepleted / 9.0;

            // Linear interpolation between current value and neighbor average
            newHomeGrid[i] = homeGrid[i] + (avgHome - homeGrid[i]) * DIFFUSION_RATE;
            newFoodGrid[i] = foodGrid[i] + (avgFood - foodGrid[i]) * DIFFUSION_RATE;
            newFoodDepletedGrid[i] = foodDepletedGrid[i] + (avgFoodDepleted - foodDepletedGrid[i]) * FOOD_DEPLETED_DIFFUSION_RATE;
        }

        // 5. Swap the grids
        homeGrid = newHomeGrid;
        foodGrid = newFoodGrid;
        foodDepletedGrid = newFoodDepletedGrid;
    }   

   

   

    public void depositToHomePheromone(int x, int y, double amount) {
        homeGrid[index(x, y)] += amount;
    }
    public void depositToFoodPheromone(int x, int y, double amount) {
        foodGrid[index(x, y)] += amount;
    }
    public void depostFoodDepletedPheromone(int x, int y, double amount) {
        foodDepletedGrid[index(x, y)] += amount;
    }



   private int index(int x, int y) {
        return y * Simulation.WIDTH + x;
    }

    public double getHomePheromone(int x, int y) {
        return homeGrid[index(x, y)];
    }

    public double getFoodPheromone(int x, int y) {
        return foodGrid[index(x, y)];
    }

    public double getFoodDepletedPheromone(int x, int y) {
        return foodDepletedGrid[index(x, y)];
    }

    
}
