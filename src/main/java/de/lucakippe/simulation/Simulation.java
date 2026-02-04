
package de.lucakippe.simulation;

public class Simulation {
    public final static int WIDTH = 800;
    public final static int HEIGHT = 800;
    final static int NUM_ANTS = 300;

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
