// 扫地机器人控制脚本

class CleaningRobot {
    constructor(model, batteryCapacity) {
        this.model = model;
        this.batteryCapacity = batteryCapacity;
        this.isCleaning = false;
    }

    startCleaning() {
        this.isCleaning = true;
        console.log(`${this.model} 开始清扫`);
    }

    stopCleaning() {
        this.isCleaning = false;
        console.log(`${this.model} 停止清扫`);
    }

    returnToCharge() {
        console.log(`${this.model} 返回充电`);
    }
}

// 使用示例
const robot = new CleaningRobot("SC-2000", 5200);
robot.startCleaning();
