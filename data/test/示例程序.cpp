#include <iostream>
#include <string>

class CleaningRobot {
private:
    std::string model;
    int batteryCapacity;
    bool isCleaning;

public:
    CleaningRobot(std::string model, int batteryCapacity)
        : model(model), batteryCapacity(batteryCapacity), isCleaning(false) {}

    void startCleaning() {
        isCleaning = true;
        std::cout << model << " 开始清扫" << std::endl;
    }

    void stopCleaning() {
        isCleaning = false;
        std::cout << model << " 停止清扫" << std::endl;
    }

    void returnToCharge() {
        std::cout << model << " 返回充电" << std::endl;
    }
};

int main() {
    CleaningRobot robot("SC-2000", 5200);
    robot.startCleaning();
    robot.stopCleaning();
    robot.returnToCharge();
    return 0;
}
