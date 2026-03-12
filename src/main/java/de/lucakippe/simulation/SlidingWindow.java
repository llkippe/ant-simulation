package de.lucakippe.simulation;

public class SlidingWindow {
    private final double[] buffer;
    private int head = 0;
    private int count = 0;
    private double runningSum = 0;

    public SlidingWindow(int bufferSize) {
        this.buffer = new double[bufferSize];
    }

    // fuer Ameisen-Basierte Metrik (pfadeffizienz)
    public void addValue(double value) {
        // entferne aeltesten wert von summe
        runningSum -= buffer[head];
        // fuege neuen wert hinzu
        buffer[head] = value;
        runningSum += value;

        // circular buffer logik -> head auf aeltesten eintrag
        head = (head +1) % buffer.length;
        if(count < buffer.length) count++;
    }

    // fuer Step-basierte Metriken (throuput, )
    public void tick(double valueInThisStep) {
        addValue(valueInThisStep);
    }
    public double getAverage() {
        if (count == 0) return 0.0;
        return runningSum / count;
    }

    public double getSum() {
        return runningSum;
    }

    public int getCount() {
        return count;
    }

}
