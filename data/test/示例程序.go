package main

import "fmt"

type CleaningRobot struct {
	model          string
	batteryCapacity int
	isCleaning     bool
}

func NewCleaningRobot(model string, batteryCapacity int) *CleaningRobot {
	return &CleaningRobot{
		model:          model,
		batteryCapacity: batteryCapacity,
		isCleaning:     false,
	}
}

func (r *CleaningRobot) StartCleaning() {
	r.isCleaning = true
	fmt.Printf("%s 开始清扫\n", r.model)
}

func (r *CleaningRobot) StopCleaning() {
	r.isCleaning = false
	fmt.Printf("%s 停止清扫\n", r.model)
}

func (r *CleaningRobot) ReturnToCharge() {
	fmt.Printf("%s 返回充电\n", r.model)
}

func main() {
	robot := NewCleaningRobot("SC-2000", 5200)
	robot.StartCleaning()
	robot.StopCleaning()
	robot.ReturnToCharge()
}
