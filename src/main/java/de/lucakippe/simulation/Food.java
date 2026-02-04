package de.lucakippe.simulation;

public class Food {
    int posX;
    int posY;
    int radius; // durchmesser

    int createdAtStep; 


    public Food(int posX, int posY, int size) {
        this.posX = posX;
        this.posY = posY;
        this.radius = size;

        this.createdAtStep = Simulation.stepCount;
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

    public boolean isInsideFood(double x, double y) {
    double dx = x - posX;
    double dy = y - posY;
    return (dx * dx + dy * dy) <= (radius * radius);
}   

}
