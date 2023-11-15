from dal.scopes.robot import Robot, FleetRobot

def sendToRobot(action_name: str, flow_name: str, robot_name: str):
    if robot_name == "Default":
        robot = Robot()
    else:
        robot = FleetRobot(robot_name)
    robot.send_cmd(command=action_name, flow=flow_name)
    return True


sendToRobot("START", "test_flow1", "Default")