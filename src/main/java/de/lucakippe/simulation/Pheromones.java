package de.lucakippe.simulation;




public class Pheromones {
    private double[] homeGrid;
    private double[] foodGrid;
    private double[] foodDepletedGrid;

  

    final static double LINEAR_THRESHHOLD = 0.05;
    final static double LINEAR_DROPOFF = 0.0001;
    final static double EVAPORATION_RATE = 0.004;
    //final static double FOOD_DEPLETED_EVAPORTAION_RATE = 0.004; // half of original evaporation rate

    final static double DIFFUSION_RATE = 0.04;
    final static double FOOD_DEPLETED_DIFFUSION_RATE = 0.25;
    final static int diffuseSteps = 3; // Diffusion happens every 3 steps, to save computation time



    final static double MAX_PHEROMONE_STRENGTH = 13.0;

   

    public Pheromones() {
        homeGrid = new double[Simulation.WIDTH * Simulation.HEIGHT];
        foodGrid = new double[Simulation.WIDTH * Simulation.HEIGHT];
        foodDepletedGrid = new double[Simulation.WIDTH * Simulation.HEIGHT];
    }

    void update(int stepCount) {
        evaporate();
        if(stepCount % diffuseSteps == 0) {
            diffuse();
        }
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
                foodDepletedGrid[i] *= (1 - EVAPORATION_RATE);
            } else {
                foodDepletedGrid[i] -= LINEAR_DROPOFF;
            }
            if (foodDepletedGrid[i] < 0) foodDepletedGrid[i] = 0;
        }
    }
}

    public void diffuse() {
        double[] newHome = new double[homeGrid.length];
        double[] newFood = new double[foodGrid.length];
        double[] newFoodDepleted = new double[foodDepletedGrid.length];

        int W = Simulation.WIDTH;
        int H = Simulation.HEIGHT;

        // --- PART 1: THE INNER CORE (The Speed Demon) ---
        // We skip the first/last rows and columns (y=1 to H-2, x=1 to W-2)
        // No "if" checks, no modulo math, pure raw calculation.
        // Inside your diffuse() method, for the "Inner Core":
        int[] offsets = {
            -W - 1, -W, -W + 1, // Top neighbors
            -1,      0,      1, // Middle neighbors
             W - 1,  W,  W + 1  // Bottom neighbors
        };

        for (int y = 1; y < H - 1; y++) {
            for (int x = 1; x < W - 1; x++) {
                int i = y * W + x;

                double sH = 0, sF = 0, sD = 0;
            
                // This loop is now just simple addition. Extremely fast.
                for (int offset : offsets) {
                    int nIdx = i + offset;
                    sH += homeGrid[nIdx];
                    sF += foodGrid[nIdx];
                    sD += foodDepletedGrid[nIdx];
                }
            
                newHome[i] = homeGrid[i] + (sH / 9.0 - homeGrid[i]) * DIFFUSION_RATE * diffuseSteps;
                newFood[i] = foodGrid[i] + (sF / 9.0 - foodGrid[i]) * DIFFUSION_RATE * diffuseSteps;
                newFoodDepleted[i] = foodDepletedGrid[i] + (sD / 9.0 - foodDepletedGrid[i]) * FOOD_DEPLETED_DIFFUSION_RATE * diffuseSteps;
            }
        }

        // --- PART 2: THE BOUNDARIES (The "Safe" Slow Path) ---
        // Only run the wrap-around/border logic for the outermost pixels
        handleEdges(newHome, newFood, newFoodDepleted, W, H);

        homeGrid = newHome;
        foodGrid = newFood;
        foodDepletedGrid = newFoodDepleted;
    }

   private void handleEdges(double[] nextHome, double[] nextFood, double[] nextDepleted, int W, int H) {
    // 1. Process Top and Bottom rows
    for (int x = 0; x < W; x++) {
        updateSingleCell(x, 0, nextHome, nextFood, nextDepleted, W, H);     // Top row
        updateSingleCell(x, H - 1, nextHome, nextFood, nextDepleted, W, H); // Bottom row
    }

    // 2. Process Left and Right columns (skipping corners already handled above)
    for (int y = 1; y < H - 1; y++) {
        updateSingleCell(0, y, nextHome, nextFood, nextDepleted, W, H);     // Left column
        updateSingleCell(W - 1, y, nextHome, nextFood, nextDepleted, W, H); // Right column
    }
}

// Helper to perform the complex logic (with borders and wrap-around) on a single pixel
private void updateSingleCell(int x, int y, double[] nextHome, double[] nextFood, double[] nextDepleted, int W, int H) {
    int i = y * W + x;
    double sumHome = 0, sumFood = 0, sumDepleted = 0;
    int samples = 0;

    for (int oy = -1; oy <= 1; oy++) {
        for (int ox = -1; ox <= 1; ox++) {
            int nx = x + ox;
            int ny = y + oy;

            // If borders are active and we are outside, skip this neighbor
            if (Simulation.bordersActive && Simulation.outsideOfBorder(nx, ny)) {
                continue; 
            }

            // Wrap-around logic for neighbors
            int neighborX = (nx + W) % W;
            int neighborY = (ny + H) % H;
            int nIdx = neighborY * W + neighborX;

            sumHome += homeGrid[nIdx];
            sumFood += foodGrid[nIdx];
            sumDepleted += foodDepletedGrid[nIdx];
            samples++;
        }
    }

    // Use the actual number of samples collected (to handle border cut-offs correctly)
    double div = (samples > 0) ? (double)samples : 1.0;
    
    nextHome[i] = homeGrid[i] + (sumHome / div - homeGrid[i]) * DIFFUSION_RATE * diffuseSteps;
    nextFood[i] = foodGrid[i] + (sumFood / div - foodGrid[i]) * DIFFUSION_RATE * diffuseSteps;
    nextDepleted[i] = foodDepletedGrid[i] + (sumDepleted / div - foodDepletedGrid[i]) * FOOD_DEPLETED_DIFFUSION_RATE * diffuseSteps;
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
