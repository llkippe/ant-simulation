package de.lucakippe.simulation;

public class Food {



    private final int id;
    private final int posX;
    private final int posY;
    private final int radius; // durchmesser

    int createdAtStep; 


    public Food(int posX, int posY, int size, int currentStepCount, int id) {
        this.posX = posX;
        this.posY = posY;
        this.id = id;

        this.radius = size;

        this.createdAtStep = currentStepCount;
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
    public int getCreatedAtStep() {
        return createdAtStep;
    }
    public int getId() {
        return id;
    }



    public boolean isInsideFood(double x, double y) {
    double dx = x - posX;
    double dy = y - posY;
    return (dx * dx + dy * dy) <= (radius * radius);
}   

}
