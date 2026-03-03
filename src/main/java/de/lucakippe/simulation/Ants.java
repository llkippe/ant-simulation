package de.lucakippe.simulation;

import java.util.Random;

public class Ants {
    private Pheromones pheromones;
    

    private double[] posX;
    private double[] posY;
    private double[] directions; // from 0 to 2PI
    private AntState[] states;
    private int[] carryingFoodFromSourceId; // -1 if not carrying food, otherwise the id of the food source the food is from
    private int[] stepsSinceLastTarget;

    private double speed = 1.0;
    private double wanderStrength = 0.5; // in radians (random value between -wanderStrength/2 and +wanderStrength/2)
    private double steeringStrength = 0.08; // in radians;

    private double maxPheromoneDepositAmount = 1.5;
    private double[] currentPheromoneDepositAmount;
    private double pheremonDepositDecayRate = 0.01;

    private double sensorDistance = 15.0;
    private double sensorOffsetAngle = Math.PI / 7;
    
    private Nest nest;
    private MetricsManager metricsManager;
    private Food[] foodSources;


    public Ants(Pheromones pheromones, Nest nest, Food[] foodSources, MetricsManager metricsManager) {
        this.pheromones = pheromones;
        this.nest = nest;
        this.foodSources = foodSources;
        this.metricsManager = metricsManager;

        this.posX = new double[Simulation.NUM_ANTS];
        this.posY = new double[Simulation.NUM_ANTS];
        this.directions = new double[Simulation.NUM_ANTS];
        this.states = new AntState[Simulation.NUM_ANTS];
        this.currentPheromoneDepositAmount = new double[Simulation.NUM_ANTS];
        this.carryingFoodFromSourceId = new int[Simulation.NUM_ANTS];
        this.stepsSinceLastTarget = new int[Simulation.NUM_ANTS];

        for(int i = 0; i < Simulation.NUM_ANTS; i++) {
            posX[i] = nest.getPosX();
            posY[i] = nest.getPosY();
            directions[i] = Math.random() * 2 * Math.PI;
            states[i] = AntState.SEARCHING_FOR_FOOD;
            currentPheromoneDepositAmount[i] = maxPheromoneDepositAmount;
            carryingFoodFromSourceId[i] = -1; 
            stepsSinceLastTarget[i] = 0;
        }
    }


    public void update() {
        for(int i = 0; i < Simulation.NUM_ANTS; i++) {
            steerAnt(i);
            moveAnt(i);
            checkForFoodSources(i);
            checkForNest(i);
            depositPhreomone(i);
        }
    
       
    }

    private void checkForFoodSources(int index) {
        // simple radius check
        int foodSourceId = isOnFoodSource(posX[index], posY[index]);
        if (states[index] == AntState.SEARCHING_FOR_FOOD && foodSourceId != -1) {
            states[index] = AntState.RETURNING_HOME;
            directions[index] += Math.PI; // turn around
            currentPheromoneDepositAmount[index] = maxPheromoneDepositAmount;
            carryingFoodFromSourceId[index] = foodSourceId;
            metricsManager.reportStepsToFood(stepsSinceLastTarget[index]);
            stepsSinceLastTarget[index] = 0;
        }
    }

    private int isOnFoodSource(double posX, double posY) {
        for(int f = 0; f < foodSources.length; f++) {
            Food food = foodSources[f];
            if(food.isInsideFood(posX, posY)) {
                
                
                return food.getId();

            }
        }
        return -1;
    }

    private void checkForNest(int index) {
        if(states[index] == AntState.RETURNING_HOME && nest.isInsideNest(posX[index], posY[index])) {    
            directions[index] += Math.PI; // turn around
            states[index] = AntState.SEARCHING_FOR_FOOD;
            currentPheromoneDepositAmount[index] = maxPheromoneDepositAmount;
            nest.foodBroughtToNest(carryingFoodFromSourceId[index]);
            carryingFoodFromSourceId[index] = -1;
            metricsManager.reportStepsToNest(stepsSinceLastTarget[index]);
            stepsSinceLastTarget[index] = 0;
        }
    
    }


    private void depositPhreomone(int i) {
        int x = (int) posX[i];
        int y = (int) posY[i];
        
        if (states[i] == AntState.SEARCHING_FOR_FOOD) {
            pheromones.depositToHomePheromone(x, y, currentPheromoneDepositAmount[i]);
        } else if (states[i] == AntState.RETURNING_HOME) {
           pheromones.depositToFoodPheromone(x, y, currentPheromoneDepositAmount[i]);
        }
        
        // decay for every step away from pheremone target
        currentPheromoneDepositAmount[i] *= (1 - pheremonDepositDecayRate);
    }


    private void steerAnt(int index) {
        
        
        double[] centerSensorPos = getSensorPosition(index, 0, sensorDistance);
        double[] leftSensorPos = getSensorPosition(index, -sensorOffsetAngle, sensorDistance);
        double[] rightSensorPos = getSensorPosition(index, sensorOffsetAngle, sensorDistance);

        double centerSensorPheromoneIntesity;
        double leftSensorPheromoneIntesity;
        double rightSensorPheromoneIntesity;
        
        // check for food or nest
        if(states[index] == AntState.SEARCHING_FOR_FOOD) {
            boolean centerSensorOnFood = isOnFoodSource(centerSensorPos[0], centerSensorPos[1]) == -1 ? false : true;
            boolean leftSensorOnFood = isOnFoodSource(leftSensorPos[0], leftSensorPos[1]) == -1 ? false : true;
            boolean rightSensorOnFood = isOnFoodSource(rightSensorPos[0], rightSensorPos[1] ) == -1 ? false : true;
            
            if(centerSensorOnFood || leftSensorOnFood || rightSensorOnFood) {
                // steer towards food
                if(leftSensorOnFood && !rightSensorOnFood) {
                    directions[index] -= steeringStrength;
                } else if(rightSensorOnFood && !leftSensorOnFood) {
                    directions[index] += steeringStrength;
                }
                // if both or center just go straight
                return;
            }

            centerSensorPheromoneIntesity = pheromones.getFoodPheromone((int) centerSensorPos[0], (int) centerSensorPos[1]);
            leftSensorPheromoneIntesity = pheromones.getFoodPheromone((int) leftSensorPos[0], (int) leftSensorPos[1]);
            rightSensorPheromoneIntesity = pheromones.getFoodPheromone((int) rightSensorPos[0], (int) rightSensorPos[1]);

        }else { // RETURNING_HOME 
            boolean centerSensorOnNest = nest.isInsideNest(centerSensorPos[0], centerSensorPos[1]);
            boolean leftSensorOnNest = nest.isInsideNest(leftSensorPos[0], leftSensorPos[1]);
            boolean rightSensorOnNest = nest.isInsideNest(rightSensorPos[0], rightSensorPos[1]);
            
            if(centerSensorOnNest || leftSensorOnNest || rightSensorOnNest) {
                // steer towards nest
                if(leftSensorOnNest && !rightSensorOnNest) {
                    directions[index] -= steeringStrength;
                } else if(rightSensorOnNest && !leftSensorOnNest) {
                    directions[index] += steeringStrength;
                }
                // if both or center just go straight
                return;
            }

            centerSensorPheromoneIntesity = pheromones.getHomePheromone((int) centerSensorPos[0], (int) centerSensorPos[1]);
            leftSensorPheromoneIntesity = pheromones.getHomePheromone((int) leftSensorPos[0], (int) leftSensorPos[1]);
            rightSensorPheromoneIntesity = pheromones.getHomePheromone((int) rightSensorPos[0], (int) rightSensorPos[1]);
        }

    
        double steeringDirection = 0;

        if(leftSensorPheromoneIntesity > centerSensorPheromoneIntesity && leftSensorPheromoneIntesity > rightSensorPheromoneIntesity) {
            steeringDirection -= steeringStrength;
        } else if(rightSensorPheromoneIntesity > centerSensorPheromoneIntesity && rightSensorPheromoneIntesity > leftSensorPheromoneIntesity) {
            steeringDirection += steeringStrength;
        }
        // if center is strongest go straigt
        
        
        // always do random walk
        double randomWiggle = (Math.random() - 0.5) * wanderStrength;

        directions[index] += randomWiggle + steeringDirection;
    }



    public double[] getSensorPosition(int index, double sensorAngleOffset, double sensorDistance) {
        double sensorAngle = directions[index] + sensorAngleOffset;
        double sensorX = (posX[index] + Math.cos(sensorAngle) * sensorDistance);
        double sensorY = (posY[index] + Math.sin(sensorAngle) * sensorDistance);

        sensorX = (sensorX + Simulation.WIDTH) % Simulation.WIDTH;
        sensorY = (sensorY + Simulation.HEIGHT) % Simulation.HEIGHT;

        return new double[] { sensorX, sensorY };
    }

    public AntState[] getStates() {
        return states;
    }




    private void moveAnt(int index) {

        posX[index] += Math.cos(directions[index]) * speed;
        posY[index] += Math.sin(directions[index]) * speed;

        posX[index] = (posX[index] + Simulation.WIDTH) % Simulation.WIDTH;
        posY[index] = (posY[index] + Simulation.HEIGHT) % Simulation.HEIGHT;

        stepsSinceLastTarget[index]++;

    }



    public double[] getPosX() { return posX; }
    public double[] getPosY() { return posY; }
    public int getNumAnts() { return Simulation.NUM_ANTS; }

}
