package de.lucakippe;

import de.lucakippe.simulation.Simulation;
import de.lucakippe.simulation.AntState;
import processing.core.PApplet;

public class Renderer extends PApplet {
    private Simulation sim;

    public Renderer(Simulation sim) {
        this.sim = sim;
    }

    @Override
    public void settings() {
        size(400, 400);
    }

    @Override
    public void setup() {
        frameRate(60);
        background(0);
    }

    @Override
    public void draw() {
        // Update simulation
        sim.update();

        // 1. Draw Pheromones directly to the pixel buffer (Much faster)
        loadPixels();
        
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int i = x + y * width;
                
                // Get strengths
                float foodStrength = (float) sim.getPheromones().getFoodPheromone(x, y);
                float homeStrength = (float) sim.getPheromones().getHomePheromone(x, y);
                
                

                // Calculate colors based on strength
                // Multiply strength by a factor (e.g. 100) to make faint trails visible
                int r = (int) Math.min(255, foodStrength * 100); 
                int b = (int) Math.min(255, homeStrength * 50);
                
                // Set pixel color: (Alpha << 24) | (R << 16) | (G << 8) | B
                // If there is no pheromone, leave it (or fade it slightly)
                if (r > 0 || b > 0) {
                     pixels[i] = color(r, 0, b);
                } else {
                     pixels[i] = color(0, 0, 0); // Black background
                }
            }
        }
        updatePixels();

        // 2. Draw Ants (White dots)
        stroke(255);
        strokeWeight(2);
        
        var antsData = sim.getAnts();
        int[] xs = antsData.getPosX();
        int[] ys = antsData.getPosY();
        AntState[] states = antsData.getStates();
    
for (int i = 0; i < antsData.getNumAnts(); i++) {
    if (states[i] == AntState.SEARCHING_FOR_FOOD) {
 

        fill(255);
    } else {
        fill(0, 255, 0);
    }
    point(xs[i], ys[i]);
}


        // 3. Draw Home and Food markers
        noStroke();
        fill(0, 0, 255, 100); // Blue Home
        circle(300, 300, 20);

        fill(255, 0, 0, 100); // Red Food
        circle(200, 200, 20);
        
        // Debug: Print frame rate to ensure it's running smoothly
        surface.setTitle("FPS: " + frameRate);
    }
}