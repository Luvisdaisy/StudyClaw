package com.studyclaw.robot;

/**
 * 扫地机器人
 */
public class CleaningRobot {
    private String model;
    private int batteryCapacity;
    private boolean isCleaning;

    public CleaningRobot(String model, int batteryCapacity) {
        this.model = model;
        this.batteryCapacity = batteryCapacity;
        this.isCleaning = false;
    }

    public void startCleaning() {
        this.isCleaning = true;
        System.out.println(model + " 开始清扫");
    }

    public void stopCleaning() {
        this.isCleaning = false;
        System.out.println(model + " 停止清扫");
    }

    public void returnToCharge() {
        System.out.println(model + " 返回充电");
    }

    public static void main(String[] args) {
        CleaningRobot robot = new CleaningRobot("SC-2000", 5200);
        robot.startCleaning();
        robot.stopCleaning();
        robot.returnToCharge();
    }
}
