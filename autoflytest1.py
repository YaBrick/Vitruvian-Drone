import cv2
import numpy as np
import urllib
from pymavlink import mavutil

global message
global totalArea
############ OPTIONS ############

### ACESS METHOD ###
# 0 -> acess a local saved image (needs to inform the image path)
# 1 -> physical local camera acess (remember to set the correct vidinput value below according to your purposes)
# 2 -> remote images acess(web), useful for IP cameras, needs to inform the image url
imageAcessMethod = 1
imagePath = "Tests/test1.png"
imageUrl = ""

### AREA FILTER (IN px) ###
aFilter = 100  # every area smaller is disregarded

### FRAME/IMAGE PASSING ###
# 0 -> manual
# 1 or any other value (passing delay in ms) -> auto
framePassing = 1000    

### MAIN FUNCION - CANNY ###
usecanny = 1
### HSV TO EASE FIND OF CONTOURS###
# better not use, makes the image have too much noise (hsv is currently not properly configured)
usehsv = 0

### CHOOSING INPUT###
# 0 - generally first camera in the system. Use 1 with virtual camera from OBS for testing purposes
vidinput = 0

### SHOW PARSED VIDEO WITH ALL THE FILTERS###
showparsedvideo = 0

showdetectedcontours = 0

showfoundcontours = 0

showcanny = 0

### ENABLE/DISABLE EVERY OUTPUT WINDOW, EVEN CANNY VALUES CHANGERS###
showanyoutput = 1

### USE MAVLINK CONNECTION (turn on only on the RPi)
usemavlink = 1
############ END OF OPTIONS ############


'''HOW TO USE OBS FOR TESTING PURPOSES (and why)
1. Open OBS and add the source "Window Capture" (I prefer using Paint to capture)
2. In the menu "Control" press "Start Virtual Camera"
3. If VideoCapture() value is not "1" - change to this value
4. Run Python File - now it will scan only the Paint Window (any window, use whatever you prefer)
5. This way you can draw different shapes in real time and test them with this program, without the need to draw them on paper
   and show to the camera
'''

### MAVLINK SETTINGS ###
if usemavlink:
    connection_string = '/dev/serial0, 57600'
    master = mavutil.mavlink_connection(connection_string)
    print("Waiting for heartbeat")
    master.wait_heartbeat()
    print("Heartbeat from system (system %u component %u)" % (master.target_system, master.target_component))


    # Set the message interval to 1 second (1000000 microseconds)
    interval_us = 1000000  # Interval in microseconds

    # Send a command to set the message interval for the DISTANCE_SENSOR message
    message = master.mav.command_long_encode(
    master.target_system,         # target_system (typically the vehicle)
    master.target_component,      # target_component (typically the autopilot)
    mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # request command with interval 
    0,                            # confirmation
    400, # ID of the asked attribute (in this case DISTANCE_SENSOR)
    interval_us,                  # param2 (interval in microseconds)
    1, 0, 0, 0, 0                 # param3 to param7 (unused)
)
    
master.mav.command_long_send(
    master.target_system,
    master.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0,
    1, 21196, 0, 0, 0, 0, 0)
response = master.recv_match(type='COMMAND_ACK', blocking=True)
print(response)

            