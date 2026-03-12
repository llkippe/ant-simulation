package de.lucakippe;
import de.lucakippe.simulation.Simulation;
import processing.core.PApplet;


public class App 
{
    public static void main(String[] args) {
        Simulation sim = new Simulation(true);
        
        Renderer visualizer = new Renderer(sim); // Pass the simulation to the renderer
        PApplet.runSketch(new String[]{"AntSimulation"}, visualizer);
    }
}
        