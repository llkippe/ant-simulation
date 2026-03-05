package de.lucakippe.simulation;

import java.util.HashMap;

public class Nest {
    int posX;
    int posY;
    int radius; // durchmesser


    private HashMap<Integer, Integer> foodCountPerSource = new HashMap<>();
    

    public Nest(int posX, int posY, int size) {
        this.posX = posX;
        this.posY = posY;
        this.radius = size;
    }

    public int getPosX() {
        return posX;
    }
    public int getPosY() {
        return posY;
    }
    public int getRadius() {
        return radius;    
    }


    public void foodBroughtToNest(int foodSourceId) {
        if(foodSourceId == -1) System.out.println("huch");
        foodCountPerSource.put(foodSourceId, foodCountPerSource.getOrDefault(foodSourceId, 0) + 1);
    }

    public HashMap<Integer, Integer> getFoodPerSourceMap() {
        return new HashMap<>(foodCountPerSource);
    }
    

    public boolean isInsideNest(double x, double y) {
        double dx = x - posX;
        double dy = y - posY;
        return (dx * dx + dy * dy) <= (radius * radius);
    }
}
