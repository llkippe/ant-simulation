package de.lucakippe.simulation;

import java.util.Random;

public class Ants {
    private Pheromones pheromones;
    private boolean antiPheromoneActive;

    private double[] posX;
    private double[] posY;
    private double[] directions; // from 0 to 2PI
    private AntState[] states;
    private int[] carryingFoodFromSourceId; // -1 if not carrying food, otherwise the id of the food source the food is from
    private int[] stepsSinceLastTarget;
    private boolean[] isScout;

    private boolean[] isFollowingStrongPath;
    private final double STRONG_PATH_THRESHOLD = 3.5;
    private final int CONFUSED_STEP_INTERVAL = 55;
    private final double PERCENTAGE_TRIGGER_END_OF_TRAIL = 0.15;
    private final int[] stepsSinceLeavingStrongPath;


    private double speed = 1.0;
    private double wanderStrength = 0.3; // in radians (random value between -wanderStrength/2 and +wanderStrength/2)
    private double steeringStrength = 0.4; // in radians;

    private double maxPheromoneDepositAmount = 0.8;
    private double maxPheromoneDepositAmountScoutOnFood = 5.5;
    private double[] currentPheromoneDepositAmount;
    private double pheremonDepositDecayRate = 0.008;
    private double foodDepletedWeight = 2; // based on research anti is double as strong

    private double sensorDistance = 25.0;
    private double sensorOffsetAngle = Math.PI / 5; // 36 grad
    
    private Nest nest;
    private MetricsManager metricsManager;
    private Food[] foodSources;

    private Random random;


    public Ants(Pheromones pheromones, Nest nest, Food[] foodSources, MetricsManager metricsManager, boolean antiPheromoneActive, long seed) {
        this.random = new Random(seed);

        this.pheromones = pheromones;
        this.nest = nest;
        this.foodSources = foodSources;
        this.metricsManager = metricsManager;
        this.antiPheromoneActive = antiPheromoneActive;

        this.posX = new double[Simulation.NUM_ANTS];
        this.posY = new double[Simulation.NUM_ANTS];
        this.directions = new double[Simulation.NUM_ANTS];
        this.states = new AntState[Simulation.NUM_ANTS];
        this.currentPheromoneDepositAmount = new double[Simulation.NUM_ANTS];
        this.carryingFoodFromSourceId = new int[Simulation.NUM_ANTS];
        this.stepsSinceLastTarget = new int[Simulation.NUM_ANTS];
        this.isScout = new boolean[Simulation.NUM_ANTS];
        this.isFollowingStrongPath = new boolean[Simulation.NUM_ANTS];
        this.stepsSinceLeavingStrongPath = new int[Simulation.NUM_ANTS];

        for(int i = 0; i < Simulation.NUM_ANTS; i++) {
            double angle = random.nextDouble() * 2 * Math.PI;
// Wurzel ziehen für gleichmäßige Verteilung
double r = nest.getRadius() * Math.sqrt(random.nextDouble()); 

posX[i] = nest.getPosX() + r * Math.cos(angle);
posY[i] = nest.getPosY() + r * Math.sin(angle);
            directions[i] = this.random.nextDouble() * 2 * Math.PI;
            
            states[i] = AntState.SEARCHING_FOR_FOOD;
            currentPheromoneDepositAmount[i] = maxPheromoneDepositAmount;
            carryingFoodFromSourceId[i] = -1; 
            stepsSinceLastTarget[i] = 0;
            if(i < Simulation.NUM_ANTS * Simulation.PERCENT_SCOUT_ANTS) isScout[i] = true;
            else isScout[i] = false;
            isFollowingStrongPath[i] = false;
            this.stepsSinceLeavingStrongPath[i] = 0;
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
            if(isScout[index]) currentPheromoneDepositAmount[index] = maxPheromoneDepositAmountScoutOnFood;
            carryingFoodFromSourceId[index] = foodSourceId;
            metricsManager.reportStepsToFood(stepsSinceLastTarget[index], foodSourceId); 
            stepsSinceLastTarget[index] = 0;

            if (!isFollowingStrongPath[index]) {
            metricsManager.reportExploitationStart();
            }

            isFollowingStrongPath[index] = false;
            stepsSinceLeavingStrongPath[index] = 0;
        }
    }

    private int isOnFoodSource(double posX, double posY) {
        for(int f = 0; f < foodSources.length; f++) {
            Food food = foodSources[f];
            if(food.isInsideFood(posX, posY)) return food.getId(); 
        }
        return -1;
    }

    private void checkForNest(int index) {
        if((states[index] == AntState.RETURNING_HOME || states[index] == AntState.DISAPPOINTED_RETURNING_HOME) && nest.isInsideNest(posX[index], posY[index])) {    
            
            if(states[index] == AntState.RETURNING_HOME) {
                metricsManager.reportStepsToNest(stepsSinceLastTarget[index], carryingFoodFromSourceId[index]);
                nest.foodBroughtToNest(carryingFoodFromSourceId[index]);
                metricsManager.reportExploitationEnd(); // when dissapointed it already counts as exploring from this moment on
            }

            //directions[index] += Math.PI; // turn around
            // Teleport to center and pick a random unbiased direction to treat nest as coordiantion hub, unbiased sampling of env
            double angle = random.nextDouble() * 2 * Math.PI;
// Wurzel ziehen für gleichmäßige Verteilung
double r = nest.getRadius() * Math.sqrt(random.nextDouble()); 

posX[index] = nest.getPosX() + r * Math.cos(angle);
posY[index] = nest.getPosY() + r * Math.sin(angle);
            directions[index] = this.random.nextDouble() * 2 * Math.PI;



            states[index] = AntState.SEARCHING_FOR_FOOD;
            currentPheromoneDepositAmount[index] = maxPheromoneDepositAmount;
            stepsSinceLastTarget[index] = 0;
            carryingFoodFromSourceId[index] = -1;

   


            isFollowingStrongPath[index] = false;
            stepsSinceLeavingStrongPath[index] = 0;
        }
    }


    private void depositPhreomone(int i) {
        int x = (int) posX[i];
        int y = (int) posY[i];
        
        if (states[i] == AntState.SEARCHING_FOR_FOOD) {
            pheromones.depositToHomePheromone(x, y, currentPheromoneDepositAmount[i]);
        } else if (states[i] == AntState.RETURNING_HOME) {
           pheromones.depositToFoodPheromone(x, y, currentPheromoneDepositAmount[i]);
        } else if (states[i] == AntState.DISAPPOINTED_RETURNING_HOME && antiPheromoneActive) {
            pheromones.depostFoodDepletedPheromone(x, y, currentPheromoneDepositAmount[i]);
        }
        
        // decay for every step away from pheremone target
        currentPheromoneDepositAmount[i] *= (1 - pheremonDepositDecayRate);
    }

    


    private void steerAnt(int index) {
        double[] leftPos = getSensorPosition(index, -sensorOffsetAngle, sensorDistance);
        double[] centerPos = getSensorPosition(index, 0, sensorDistance);
        double[] rightPos = getSensorPosition(index, sensorOffsetAngle, sensorDistance);

        double leftI = getAverageIntensity3x3(leftPos[0], leftPos[1], states[index], isScout[index]);
        double centerI = getAverageIntensity3x3(centerPos[0], centerPos[1], states[index],isScout[index]);
        double rightI = getAverageIntensity3x3(rightPos[0], rightPos[1], states[index],isScout[index]);

        double total = leftI + centerI + rightI;
        detectDisappointment(index, total);

        double steeringDirection = 0;

        if (total > 0) {
            steeringDirection = ((rightI - leftI) / total) * steeringStrength;
            // less steering when target ahead
            if (centerI > leftI && centerI > rightI) {
                steeringDirection *= 0.2; 
            }
        }

        double randomWiggle = (random.nextDouble() - 0.5) * wanderStrength;
        directions[index] += steeringDirection + randomWiggle;
    }

    private void detectDisappointment(int index, double currentPheromoneIntensity) {
        if (states[index] == AntState.SEARCHING_FOR_FOOD && isScout[index] == false) {
            
            
            // ameise ist aktuell aufm starken pfad 
            if(currentPheromoneIntensity >= STRONG_PATH_THRESHOLD) {
                if(!isFollowingStrongPath[index]){
                    isFollowingStrongPath[index] = true;
                    metricsManager.reportExploitationStart();
                }
                stepsSinceLeavingStrongPath[index] = 0; 
            }

            // die ameise war auf starken pfad 
            else if(isFollowingStrongPath[index] && currentPheromoneIntensity < STRONG_PATH_THRESHOLD * (1 - PERCENTAGE_TRIGGER_END_OF_TRAIL)) {
                stepsSinceLeavingStrongPath[index]++;

                // am ende des such intervals nach ende vom trail
                if(stepsSinceLeavingStrongPath[index] > CONFUSED_STEP_INTERVAL) {
                    if(antiPheromoneActive) {
                        states[index] = AntState.DISAPPOINTED_RETURNING_HOME;
                        directions[index] += Math.PI; // turn around
                        currentPheromoneDepositAmount[index] = maxPheromoneDepositAmount * 3;
                    }
                    isFollowingStrongPath[index] = false;
                    stepsSinceLeavingStrongPath[index] = 0;
                    metricsManager.reportAntDissapointed();
                    metricsManager.reportExploitationEnd();
                }
            }
        }
    }

    // extrem boost to go to nest or food source
    private double getAverageIntensity3x3(double x, double y, AntState state, boolean isScout) {
        double sum = 0;
        double count = 0;
        double TARGET_BOOST = 1000.0; // Ein extrem hoher Wert für das Ziel

        for (int ox = -1; ox <= 1; ox++) {
            for (int oy = -1; oy <= 1; oy++) {
                if(Simulation.bordersActive && Simulation.outsideOfBorder(x + ox, y + oy)) {
                    continue;
                }

                count++;
                int sx = (int) (x + ox + Simulation.WIDTH) % Simulation.WIDTH;
                int sy = (int) (y + oy + Simulation.HEIGHT) % Simulation.HEIGHT;

                if (state == AntState.SEARCHING_FOR_FOOD) {
                    if (isOnFoodSource(sx, sy) != -1) sum += TARGET_BOOST;
                    else if(!isScout) {
                        double foodIntensity = pheromones.getFoodPheromone(sx, sy);
                        double depletedIntensity = pheromones.getFoodDepletedPheromone(sx, sy);

                        sum += Math.max(0, foodIntensity - (depletedIntensity * foodDepletedWeight)); 
                    }           
                } else { // RETURNING_HOME OR RETURNING_HOME_DISSAPOINTED
                    if (nest.isInsideNest(sx, sy)) sum += TARGET_BOOST;
                    else sum += pheromones.getHomePheromone(sx, sy);
                }
            }
        }
        return sum / count;
    }

   

    public double[] getSensorPosition(int index, double sensorAngleOffset, double sensorDistance) {
        double sensorAngle = directions[index] + sensorAngleOffset;
        double sensorX = (posX[index] + Math.cos(sensorAngle) * sensorDistance);
        double sensorY = (posY[index] + Math.sin(sensorAngle) * sensorDistance);

        if(Simulation.bordersActive) {
            // If borders are active and the sensor is outside, return the edge position
            if (Simulation.outsideOfBorder(sensorX, sensorY)) {
                sensorX = Math.max(0, Math.min(Simulation.WIDTH - 1, sensorX));
                sensorY = Math.max(0, Math.min(Simulation.HEIGHT - 1, sensorY));
                return new double[] { sensorX, sensorY };
            }
        }else {
            sensorX = (sensorX + Simulation.WIDTH) % Simulation.WIDTH;
            sensorY = (sensorY + Simulation.HEIGHT) % Simulation.HEIGHT;
        }

   

        return new double[] { sensorX, sensorY };
    }

    public AntState[] getStates() {
        return states;
    }




    private void moveAnt(int index) {
        double nextX = posX[index] + Math.cos(directions[index]) * speed;
            double nextY = posY[index] + Math.sin(directions[index]) * speed;

        // BEGRENZTE WELT: Reflektierende Wände (Bouncing-Logik)
        if(Simulation.bordersActive) {
            // Prüfung der horizontalen Grenzen (Linke/Rechte Wand)
            if (nextX < 0 || nextX >= Simulation.WIDTH) {
                // Reflektiere den Winkel an der vertikalen Achse (PI - Winkel)
                directions[index] = Math.PI - directions[index]; 
                // Clamp die Position, um ein "Feststecken" außerhalb zu verhindern
                nextX = Math.max(0, Math.min(Simulation.WIDTH - 1, nextX));
            }

            // Prüfung der vertikalen Grenzen (Obere/Untere Wand)
            if (nextY < 0 || nextY >= Simulation.HEIGHT) {
                // Reflektiere den Winkel an der horizontalen Achse (-Winkel)
                directions[index] = -directions[index]; 
                nextY = Math.max(0, Math.min(Simulation.HEIGHT - 1, nextY));
            }

            posX[index] = nextX;
            posY[index] = nextY;
        } else { // UNBEGRENZTE WELT. 

            posX[index] = (nextX + Simulation.WIDTH) % Simulation.WIDTH;
            posY[index] = (nextY + Simulation.HEIGHT) % Simulation.HEIGHT;
        }
        stepsSinceLastTarget[index]++;

    }




    public double[] getPosX() { return posX; }
    public double[] getPosY() { return posY; }
    public boolean[] getIsScout() { return isScout; }
    public int getNumAnts() { return Simulation.NUM_ANTS; }

}
