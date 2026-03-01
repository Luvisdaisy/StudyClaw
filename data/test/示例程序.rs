pub struct CleaningRobot {
    model: String,
    battery_capacity: u32,
    is_cleaning: bool,
}

impl CleaningRobot {
    pub fn new(model: &str, battery_capacity: u32) -> Self {
        Self {
            model: model.to_string(),
            battery_capacity,
            is_cleaning: false,
        }
    }

    pub fn start_cleaning(&mut self) {
        self.is_cleaning = true;
        println!("{} 开始清扫", self.model);
    }

    pub fn stop_cleaning(&mut self) {
        self.is_cleaning = false;
        println!("{} 停止清扫", self.model);
    }

    pub fn return_to_charge(&self) {
        println!("{} 返回充电", self.model);
    }
}

fn main() {
    let mut robot = CleaningRobot::new("SC-2000", 5200);
    robot.start_cleaning();
    robot.stop_cleaning();
    robot.return_to_charge();
}
