package de.lucakippe;

import de.lucakippe.simulation.Simulation;
import de.lucakippe.simulation.AntState;
import processing.core.PApplet;
import processing.core.PImage;

public class Renderer extends PApplet {
    private Simulation sim;
    private PImage pheromoneMap;
    private float scaleX, scaleY;

    public Renderer(Simulation sim) {
        this.sim = sim;
    }

    @Override
    public void settings() {
        size(800, 800, P2D);
    }

    @Override
    public void setup() {
        frameRate(60);
        
        pheromoneMap = createImage(Simulation.WIDTH, Simulation.HEIGHT, RGB);
        
        scaleX = (float) width / Simulation.WIDTH;
        scaleY = (float) height / Simulation.HEIGHT;
    }

    @Override
    public void draw() {
        sim.update();

        // DRAW PHEROMONES

        pheromoneMap.loadPixels();  
        for (int i = 0; i < pheromoneMap.pixels.length; i++) {
            int x = i % Simulation.WIDTH;
            int y = i / Simulation.WIDTH;

            float food = (float) sim.getPheromones().getFoodPheromone(x, y);
            float home = (float) sim.getPheromones().getHomePheromone(x, y);

            int r = (int) Math.min(255, food * 120); 
            int b = (int) Math.min(255, home * 60);

            pheromoneMap.pixels[i] = (255 << 24) | (r << 16) | (0 << 8) | b;
        }
        pheromoneMap.updatePixels();

        noSmooth(); 
        image(pheromoneMap, 0, 0, width, height);
        
        // DRAW ANTS

        var antsData = sim.getAnts();
        double[] xs = antsData.getPosX();
        double[] ys = antsData.getPosY();
        AntState[] states = antsData.getStates();

        strokeWeight(2 * scaleX); // Scale ant size slightly too
        for (int i = 0; i < antsData.getNumAnts(); i++) {
            if (states[i] == AntState.SEARCHING_FOR_FOOD) {
                stroke(255); // White searching
            } else {
                stroke(0, 255, 0); // Green returning
            }
            // Multiply sim position by scale factor to place on screen
            point((float)xs[i] * scaleX, (float)ys[i] * scaleY);
        }


        // 3. Draw Home and Food markers
        drawMarkers();

        surface.setTitle("FPS: " + (int)frameRate);
    }
private void drawMarkers() {
        noStroke();
        fill(0, 0, 255, 150);
        circle(300 * scaleX, 300 * scaleY, 20 * scaleX);

        fill(255, 0, 0, 150);
        circle(200 * scaleX, 200 * scaleY, 20 * scaleX);
    }
}