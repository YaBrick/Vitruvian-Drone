from pymavlink import mavutil
import time
global message
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

### SHOW PARSED VIDEO WITH ALL THE FILTERS###
showparsedvideo = 1 

### MAIN FUNCION - CANNY ###
usecanny = 1
### HSV TO EASE FIND OF CONTOURS###
# better not use, makes the image have too much noise (hsv is currently not properly configured)
usehsv = 0

### CHOOSING INPUT###
# 0 - generally first camera in the system. Use 1 with virtual camera from OBS for testing purposes
vidinput = 0

### STOP EVERY OUTPUT WINDOW, EVEN CANNY VALUES CHANGERS###
showanyoutput = 0

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
    message = master.mav.command_long_encode(
        master.target_system,  # Target system ID
        master.target_component,  # Target component ID
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # ID of command to send
        0,  # Confirmation
        132,  # param1: Message ID to be streamed
        1000000, # param2: Interval in microseconds
        0,       # param3 (unused)
        0,       # param4 (unused)
        0,       # param5 (unused)
        0,       # param5 (unused)
        0        # param6 (unused)
        )


def nothing(n):
    pass

def getdistance():
    if usemavlink:
        master.mav.send(message)
        print("Request sent - waiting for response")
    # Wait for a response (blocking) to the MAV_CMD_SET_MESSAGE_INTERVAL command and print result
        response = master.recv_match(blocking=True)
        print(response)
        if response is not None and response.get_type() == 'DISTANCE_SENSOR':
            print("Command accepted")
            return response.current_distance
        else:
            print("Command failed")
            return 000
    else:
        return 000
            

while True:
    print(getdistance)
    time.sleep(1)