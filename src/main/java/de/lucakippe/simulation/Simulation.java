
package de.lucakippe.simulation;

public class Simulation {
    public final static int WIDTH = 600;
    public final static int HEIGHT = 600;
    final static int NUM_ANTS = 1000;

    static int stepCount = 0;

    private Ants ants;
    private Nest nest;
    private Food[] foodSources;
    private Pheromones pheromones;

    
    public Simulation() {
        nest = new Nest(400, 400, 20);
        foodSources = new Food[2];
            foodSources[0] = new Food(100, 243, 10);
            foodSources[1] = new Food(300, 63, 10);
        
        pheromones = new Pheromones();
        ants = new Ants(pheromones, nest, foodSources);
    }

    public void update() {
        stepCount++;

        ants.update();
        pheromones.update();
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
}
