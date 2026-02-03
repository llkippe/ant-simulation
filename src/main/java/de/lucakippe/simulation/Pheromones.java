package de.lucakippe.simulation;

public enum PheromoneType {
    TO_FOOD,
    TO_HOME
}


public class Pheromones {
    private double[] homeGrid;
    private double[] foodGrid;

   

    public Pheromones() {
        homeGrid = new double[Simulation.WIDTH * Simulation.HEIGHT];
        foodGrid = new double[Simulation.WIDTH * Simulation.HEIGHT];
    }

    void update() {
        evaporate(0.01); // Evaporate 1% each update
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

   

    public void depositToHomePheromone(int x, int y, double amount) {
        homeGrid[index(x, y)] += amount;
    }
    public void depositToFoodPheromone(int x, int y, double amount) {
        foodGrid[index(x, y)] += amount;
    }



  

    public void evaporate(double evaporationRate) {
        for (int i = 0; i < homeGrid.length; i++) {
            homeGrid[i] *= (1 - evaporationRate);
            foodGrid[i] *= (1 - evaporationRate);
        }
    }
}
