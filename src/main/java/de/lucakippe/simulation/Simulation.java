
package de.lucakippe.simulation;

public class Simulation {
    final static int WIDTH = 400;
    final static int HEIGHT = 400;
    final static int NUM_ANTS = 500;

    private int stepCount = 0;

    private Ants ants;
    private Pheromones pheromones;

    
    public Simulation() {
        
        pheromones = new Pheromones();
        ants = new Ants(pheromones);
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
}
