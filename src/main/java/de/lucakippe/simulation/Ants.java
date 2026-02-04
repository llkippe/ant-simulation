package de.lucakippe.simulation;


enum Direction {
    UP,
    UP_RIGHT,
    RIGHT,
    DOWN_RIGHT,
    DOWN,
    DOWN_LEFT,
    LEFT,
    UP_LEFT,
}



public class Ants {
    private Pheromones pheromones;
    

    private int[] posX;
    private int[] posY;
    private Direction[] directions;
    private AntState[] states;

    public Ants(Pheromones pheromones) {
        this.pheromones = pheromones;

        this.posX = new int[Simulation.NUM_ANTS];
        this.posY = new int[Simulation.NUM_ANTS];
        this.directions = new Direction[Simulation.NUM_ANTS];
        this.states = new AntState[Simulation.NUM_ANTS];

        for(int i = 0; i < Simulation.NUM_ANTS; i++) {
            posX[i] = 300;
            posY[i] = 300;
            directions[i] = randomDirection();
            states[i] = AntState.SEARCHING_FOR_FOOD;
        }
    }


    public void update() {
        move();
        checkForFood();
        depositPhreomones();
       
    }

    private void checkForFood() {
    for(int i = 0; i < Simulation.NUM_ANTS; i++) {
        // simple radius check
        if (states[i] == AntState.SEARCHING_FOR_FOOD &&
            Math.abs(posX[i] - 200) <= 10 && Math.abs(posY[i] - 200) <= 10) {
            System.out.println( i + "Found FOOD");
            states[i] = AntState.RETURNING_HOME;
            turn(i, 4);
             System.out.println(i + states[i].toString());
        } else if (states[i] == AntState.RETURNING_HOME &&
            Math.abs(posX[i] - 300) <= 10 && Math.abs(posY[i] - 300) <= 10) {
                System.out.println("Got Home");
                turn(i, 4);
            states[i] = AntState.SEARCHING_FOR_FOOD;
        }
    }
}


    private void depositPhreomones() {
        for(int i = 0; i < Simulation.NUM_ANTS; i++) {
            int x = posX[i];
            int y = posY[i];
            

            if (states[i] == AntState.SEARCHING_FOR_FOOD) {
                pheromones.depositToHomePheromone(x, y, 1.5);
            } else if (states[i] == AntState.RETURNING_HOME) {
                // deposit food pheromone
               pheromones.depositToFoodPheromone(x, y, 1.5);
            }
        }
    }

    private void move() {
        for(int i = 0; i < Simulation.NUM_ANTS; i++) {
            moveAnt(i);

            chooseNewDirection(i);
        }
    }

    private void chooseNewDirection(int index) {
        // final double homePheromoneSensingStrength = 10.0;
        // final double foodPheromoneSensingStrength = 10.0;
        
        final double baseStraightStrength = 10;
        final double baseSideStrength = 1;

        // get strength of pheremones in straight direction
        PheromoneType type = (states[index] == AntState.SEARCHING_FOR_FOOD) ? PheromoneType.TO_FOOD : PheromoneType.TO_HOME;


        double inFrontPheromone = getPheromoneAtDirection(posX[index], posY[index], directions[index], type);
        double leftPheromone = getPheromoneAtDirection(posX[index], posY[index], Direction.values()[((directions[index].ordinal() + 7) % 8)], type);
        double rightPheromone = getPheromoneAtDirection(posX[index], posY[index], Direction.values()[((directions[index].ordinal() + 9) % 8)], type);

        double total = inFrontPheromone + leftPheromone + rightPheromone;
        if(total > 0) {
            double r = Math.random() * total;
            if (r < inFrontPheromone) {
            }else if (r < inFrontPheromone + leftPheromone) {
                // turn left
                turn(index, -1);
            } else {
                // turn right
                turn(index, 1);
            }
            return;
        }
        
        double r = Math.random() * baseStraightStrength + 2 * baseSideStrength;
        if (r < baseStraightStrength) {
            // go straight
        } else if (r < baseStraightStrength + baseSideStrength) {
            // turn left
            turn(index, -1);
        } else {
            // turn right
            turn(index, 1);
        }
    }

    private double getPheromoneAtDirection(int x, int y, Direction d, PheromoneType type) {
    int targetX = x;
    int targetY = y;

    switch(d) {
        case UP: targetY = y - 1; break;
        case UP_RIGHT: targetX = x + 1; targetY = y - 1; break;
        case RIGHT: targetX = x + 1; break;
        case DOWN_RIGHT: targetX = x + 1; targetY = y + 1; break;
        case DOWN: targetY = y + 1; break;
        case DOWN_LEFT: targetX = x - 1; targetY = y + 1; break;
        case LEFT: targetX = x - 1; break;
        case UP_LEFT: targetX = x - 1; targetY = y - 1; break;
    }

    targetX = (targetX + Simulation.WIDTH) % Simulation.WIDTH;
    targetY = (targetY + Simulation.HEIGHT) % Simulation.HEIGHT;

    // choose pheromone grid
    if (type == PheromoneType.TO_FOOD) {
        return pheromones.getFoodPheromone(targetX, targetY);
    } else if (type == PheromoneType.TO_HOME) {
        return pheromones.getHomePheromone(targetX, targetY);
    }

    return 0;
}

public AntState[] getStates() {
    return states;
}



    private void turn(int index, int offset) {
        int currentOrdinal = directions[index].ordinal();
        int newOrdinal = (currentOrdinal + offset + 8) % 8;
        directions[index] = Direction.values()[newOrdinal];
    }

    private void moveAnt(int index) {
        switch(directions[index]) {
            case UP:
                posY[index]--;
                break;
            case UP_RIGHT:
                posX[index]++;
                posY[index]--;
                break;
            case RIGHT:
                posX[index]++;
                break;
            case DOWN_RIGHT:
                posX[index]++;
                posY[index]++;
                break;
            case DOWN:
                posY[index]++;
                break;
            case DOWN_LEFT:
                posX[index]--;
                posY[index]++;
                break;
            case LEFT:
                posX[index]--;
                break;
            case UP_LEFT:
                posX[index]--;
                posY[index]--;
                break;
        }

        posX[index] = (posX[index] + Simulation.WIDTH) % Simulation.WIDTH;
        posY[index] = (posY[index] + Simulation.HEIGHT) % Simulation.HEIGHT;
    }

    private Direction randomDirection() {
        int dir = (int) (Math.random() * 8);
        return Direction.values()[dir];
    }

    public int[] getPosX() { return posX; }
    public int[] getPosY() { return posY; }
    public int getNumAnts() { return Simulation.NUM_ANTS; }

}
