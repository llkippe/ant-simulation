package de.lucakippe.simulation;


public class Ants {
    private Pheromones pheromones;
    

    private double[] posX;
    private double[] posY;
    private double[] directions; // from 0 to 2PI
    private AntState[] states;
    private double speed = 1.0;
    private double wanderStrength = 0.5; // in radians (random value between -wanderStrength/2 and +wanderStrength/2)
    private double steeringStrength = 0.1; // in radians;

    private double maxPheromoneDepositAmount = 1.0;
    private double[] currentPheromoneDepositAmount;
    private double pheremonDepositDecayRate = 0.01;
    

    public Ants(Pheromones pheromones) {
        this.pheromones = pheromones;

        this.posX = new double[Simulation.NUM_ANTS];
        this.posY = new double[Simulation.NUM_ANTS];
        this.directions = new double[Simulation.NUM_ANTS];
        this.states = new AntState[Simulation.NUM_ANTS];
        this.currentPheromoneDepositAmount = new double[Simulation.NUM_ANTS];

        for(int i = 0; i < Simulation.NUM_ANTS; i++) {
            posX[i] = 300;
            posY[i] = 300;
            directions[i] = Math.random() * 2 * Math.PI;
            states[i] = AntState.SEARCHING_FOR_FOOD;
            currentPheromoneDepositAmount[i] = maxPheromoneDepositAmount;
        }
    }


    public void update() {
        for(int i = 0; i < Simulation.NUM_ANTS; i++) {
            steerAnt(i);
            moveAnt(i);
            checkForFood(i);
            depositPhreomone(i);
        }
    
       
    }

    private void checkForFood(int i) {
        // simple radius check
        if (states[i] == AntState.SEARCHING_FOR_FOOD &&
            Math.abs(posX[i] - 200) <= 10 && Math.abs(posY[i] - 200) <= 10) {
            states[i] = AntState.RETURNING_HOME;
            directions[i] += Math.PI; // turn around
            currentPheromoneDepositAmount[i] = maxPheromoneDepositAmount;

            
        } else if (states[i] == AntState.RETURNING_HOME &&
            Math.abs(posX[i] - 300) <= 10 && Math.abs(posY[i] - 300) <= 10) {    
            directions[i] += Math.PI; // turn around
            states[i] = AntState.SEARCHING_FOR_FOOD;
            currentPheromoneDepositAmount[i] = maxPheromoneDepositAmount;
        }
}


    private void depositPhreomone(int i) {
        int x = (int) posX[i];
        int y = (int) posY[i];
        
        if (states[i] == AntState.SEARCHING_FOR_FOOD) {
            pheromones.depositToHomePheromone(x, y, currentPheromoneDepositAmount[i]);
        } else if (states[i] == AntState.RETURNING_HOME) {
            // deposit food pheromone
           pheromones.depositToFoodPheromone(x, y, currentPheromoneDepositAmount[i]);
        }

        currentPheromoneDepositAmount[i] *= (1 - pheremonDepositDecayRate);
        
    }


    private void steerAnt(int index) {
        double sensorDistance = 20.0;
        double sensorOffsetAngle = Math.PI / 6;
        
        // get strength of pheremones in straight direction
        PheromoneType type = (states[index] == AntState.SEARCHING_FOR_FOOD) ? PheromoneType.TO_FOOD : PheromoneType.TO_HOME;

        double centerSensor = getPheremoneIntensityAt(index, 0, sensorDistance, type);
        double leftSensor = getPheremoneIntensityAt(index, -sensorOffsetAngle, sensorDistance, type);
        double rightSensor = getPheremoneIntensityAt(index, sensorOffsetAngle, sensorDistance, type);

        double steeringDirection = 0;

        if(leftSensor > centerSensor && leftSensor > rightSensor) {
            // Turn left
            steeringDirection -= steeringStrength;
        } else if(rightSensor > centerSensor && rightSensor > leftSensor) {
            // Turn right
            steeringDirection += steeringStrength;
        }
        // if center is strongest go straigt
        
        
        // always do random walk
        double randomWiggle = (Math.random() - 0.5) * wanderStrength;

        directions[index] += randomWiggle + steeringDirection;
    }

    private double getPheremoneIntensityAt(int index, double sensorAngleOffset, double sensorDistance, PheromoneType type) {
        

        double sensorAngle = directions[index] + sensorAngleOffset;
        int sensorX = (int) (posX[index] + Math.cos(sensorAngle) * sensorDistance);
        int sensorY = (int) (posY[index] + Math.sin(sensorAngle) * sensorDistance);

        sensorX = (sensorX + Simulation.WIDTH) % Simulation.WIDTH;
        sensorY = (sensorY + Simulation.HEIGHT) % Simulation.HEIGHT;

        if(type == PheromoneType.TO_FOOD) {
            return pheromones.getFoodPheromone(sensorX, sensorY);
        } else {
            return pheromones.getHomePheromone(sensorX, sensorY);
        }
    }

    public AntState[] getStates() {
        return states;
    }




    private void moveAnt(int index) {

        posX[index] += Math.cos(directions[index]) * speed;
        posY[index] += Math.sin(directions[index]) * speed;

        posX[index] = (posX[index] + Simulation.WIDTH) % Simulation.WIDTH;
        posY[index] = (posY[index] + Simulation.HEIGHT) % Simulation.HEIGHT;

    }



    public double[] getPosX() { return posX; }
    public double[] getPosY() { return posY; }
    public int getNumAnts() { return Simulation.NUM_ANTS; }

}
