"""扫地机器人控制示例代码"""

class CleaningRobot:
    """扫地机器人类"""

    def __init__(self, model: str, battery_capacity: int):
        self.model = model
        self.battery_capacity = battery_capacity
        self.current_battery = battery_capacity

    def start_cleaning(self):
        """开始清扫"""
        print(f"{self.model} 开始清扫...")

    def stop_cleaning(self):
        """停止清扫"""
        print(f"{self.model} 停止清扫")

    def return_to_charge(self):
        """返回充电"""
        print(f"{self.model} 返回充电座")


if __name__ == "__main__":
    robot = CleaningRobot("SC-2000", 5200)
    robot.start_cleaning()
    robot.stop_cleaning()
    robot.return_to_charge()
