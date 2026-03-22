package de.lucakippe;

import de.lucakippe.simulation.Simulation;
import de.lucakippe.simulation.AntState;
import de.lucakippe.simulation.Food;
import de.lucakippe.simulation.Nest;
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
        noSmooth(); 
    }

    @Override
    public void setup() {
        frameRate(120);
        
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
            float depleted = (float) sim.getPheromones().getFoodDepletedPheromone(x, y);

            int r = (int) Math.min(255, food * 255); 
            //if(food > 0) r = 255;
            int b = (int) Math.min(255, home * 255);
            //if (home > 0) b = 255;
            int g = (int) Math.min(255, depleted * 255);

            pheromoneMap.pixels[i] = (255 << 24) | (r << 16) | (g << 8) | b;
        }
        pheromoneMap.updatePixels();

        
        image(pheromoneMap, 0, 0, width, height);
        
        // DRAW ANTS

        var antsData = sim.getAnts();
        double[] xs = antsData.getPosX();
        double[] ys = antsData.getPosY();
        boolean[] isScout = antsData.getIsScout();
        AntState[] states = antsData.getStates();
        

        strokeWeight(3 * scaleX); // Scale ant size slightly too
        for (int i = 0; i < antsData.getNumAnts(); i++) {
            if (states[i] == AntState.SEARCHING_FOR_FOOD) {
                if(isScout[i]) stroke(55, 55, 255, 200);
                else stroke(50, 50, 255, 100); // White searching

            } else if(states[i] == AntState.DISAPPOINTED_RETURNING_HOME){
                if(isScout[i]) stroke(55,255,55, 200);
               else stroke(55,255,50, 100);// Green returning
            } else { // returning home
                if(isScout[i]) stroke(255,55,55, 200);
                else stroke(255,50,50, 100);// Green returning
            }
            // Multiply sim position by scale factor to place on screen
            point((float)xs[i] * scaleX, (float)ys[i] * scaleY);
        }


        // 3. Draw Home and Food markers
      
        drawNest();
        drawFoodSources();

        surface.setTitle("Steps In: " + sim.getStepCount()  + "   FPS: " + (int)frameRate);
    }

    private void drawFoodSources() {
        noStroke();
        fill(255, 0, 0, 150);
        Food[] foodSources = sim.getFoodSources();
        for(int i = 0; i < foodSources.length; i++) {
            var food = foodSources[i];
            circle(food.getPosX() * scaleX, food.getPosY() * scaleY, food.getRadius() * 2 * scaleX);
 fill(255, 0, 0, 20);
           circle(food.getPosX() * scaleX, food.getPosY() * scaleY, Simulation.MIN_DIST_BETWEEN_FOODSOURCES * 2 * scaleX);
        }
    }

    private void drawNest() {
        noStroke();
        fill(0, 0, 255, 150);
        Nest nest = sim.getNest();
        circle(nest.getPosX() * scaleX, nest.getPosY() * scaleY, nest.getRadius() * 2 * scaleX);
        fill(0, 0, 255, 20);
          circle(nest.getPosX() * scaleX, nest.getPosY() * scaleY, Simulation.MIN_DIST_TO_NEST * 2 * scaleX);
    }

    


}