package de.lucakippe.simulation;

public class Nest {
    int posX;
    int posY;
    int radius; // durchmesser

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

    

    public boolean isInsideNest(double x, double y) {
        double dx = x - posX;
        double dy = y - posY;
        return (dx * dx + dy * dy) <= (radius * radius);
    }
}
