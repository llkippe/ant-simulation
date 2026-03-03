package de.lucakippe.simulation;




public class Pheromones {
    private double[] homeGrid;
    private double[] foodGrid;

    final static double DIFFUSION_RATE = 0.03;

    final static double LINEAR_THRESHHOLD = 0.01;
    final static double LINEAR_DROPOFF = 0.0001;
    final static double EVAPORATION_RATE = 0.01;

   

    public Pheromones() {
        homeGrid = new double[Simulation.WIDTH * Simulation.HEIGHT];
        foodGrid = new double[Simulation.WIDTH * Simulation.HEIGHT];
    }

    void update() {
        evaporate();
        diffuse();
    }

    public void evaporate() {
    for (int i = 0; i < homeGrid.length; i++) {
        // Nur rechnen, wenn überhaupt Pheromon da ist
        if (homeGrid[i] > 0) {
            if (homeGrid[i] > LINEAR_THRESHHOLD) {
                homeGrid[i] *= (1 - EVAPORATION_RATE);
            } else {
                homeGrid[i] -= LINEAR_DROPOFF;
            }
            if (homeGrid[i] < 0) homeGrid[i] = 0; // Sicherstellen, dass es nicht negativ wird
        }

        if (foodGrid[i] > 0) {
            if (foodGrid[i] > LINEAR_THRESHHOLD) {
                foodGrid[i] *= (1 - EVAPORATION_RATE);
            } else {
                foodGrid[i] -= LINEAR_DROPOFF;
            }
            if (foodGrid[i] < 0) foodGrid[i] = 0;
        }
    }
}

    public void diffuse() {
        // 1. Create temporary arrays to store the results
        double[] newHomeGrid = new double[homeGrid.length];
        double[] newFoodGrid = new double[foodGrid.length];

        int W = Simulation.WIDTH;
        int H = Simulation.HEIGHT;

        for (int i = 0; i < homeGrid.length; i++) {
            int x = i % W;
            int y = i / W;

            double sumHome = 0;
            double sumFood = 0;

            // 2. Sample the 3x3 neighborhood (including the center)
            for (int offsetX = -1; offsetX <= 1; offsetX++) {
                for (int offsetY = -1; offsetY <= 1; offsetY++) {

                    // 3. The "Wrap-around" logic
                    int neighborX = (x + offsetX + W) % W;
                    int neighborY = (y + offsetY + H) % H;
                    int neighborIndex = neighborY * W + neighborX;

                    sumHome += homeGrid[neighborIndex];
                    sumFood += foodGrid[neighborIndex];
                }
            }

            // 4. Calculate the average and apply the rate
            double avgHome = sumHome / 9.0;
            double avgFood = sumFood / 9.0;

            // Linear interpolation between current value and neighbor average
            newHomeGrid[i] = homeGrid[i] + (avgHome - homeGrid[i]) * DIFFUSION_RATE;
            newFoodGrid[i] = foodGrid[i] + (avgFood - foodGrid[i]) * DIFFUSION_RATE;
        }

        // 5. Swap the grids
        homeGrid = newHomeGrid;
        foodGrid = newFoodGrid;
    }   

   

   

    public void depositToHomePheromone(int x, int y, double amount) {
        homeGrid[index(x, y)] += amount;
    }
    public void depositToFoodPheromone(int x, int y, double amount) {
        foodGrid[index(x, y)] += amount;
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

    
}
