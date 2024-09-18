import cv2
import numpy as np
import time
from pymavlink import mavutil

global message
global totalArea
############ OPTIONS ############

### AREA FILTER (IN px) ###
aFilter = 200  # every area smaller is disregarded

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
cam = cv2.VideoCapture(vidinput)

# video codec and video object
fourcc = cv2.VideoWriter_fourcc(*'XVID')
vname = 'Voo ' + str(time.time()) + '.avi'
fps = 1.0
res = (640, 480)
video = cv2.VideoWriter(vname, fourcc, fps, res)
### SHOW PARSED VIDEO WITH ALL THE FILTERS###
showparsedvideo = 0
showdetectedcontours = 0
showfoundcontours = 0
showcanny = 0

### ENABLE/DISABLE EVERY OUTPUT WINDOW, EVEN CANNY VALUES CHANGERS###
showanyoutput = 0

### USE MAVLINK CONNECTION (turn on only on the RPi)
usemavlink = 0
############ END OF OPTIONS ############



### MAVLINK SETTINGS ###
if usemavlink:
    connection_string = '/dev/serial0, 57600'
    master = mavutil.mavlink_connection(connection_string)
    print("Waiting for heartbeat")
    master.wait_heartbeat()
    print("Heartbeat from system (system %u component %u)" % (master.target_system, master.target_component))


    # Set the message interval to 1 second (1000000 microseconds)
    interval_us = 1e5 # Interval in microseconds

    # Send a command to set the message interval for the DISTANCE_SENSOR message
    message = master.mav.command_long_encode(
    master.target_system,         # target_system (typically the vehicle)
    master.target_component,      # target_component (typically the autopilot)
    mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # request command with interval 
    0,                            # confirmation
    132, # ID of the asked attribute (in this case DISTANCE_SENSOR)
    interval_us,                  # param2 (interval in microseconds)
    0, 0, 0, 0, 0                 # param3 to param7 (unused)
)


def nothing(n):
    pass

def getdistance():
    if usemavlink:
        master.mav.send(message)
        print("Request sent - waiting for response")
    # Wait for a response (blocking) to the MAV_CMD_SET_MESSAGE_INTERVAL command and print result
        response = master.recv_match(type='DISTANCE_SENSOR', blocking=True)
        #print(response)
        if response is not None and response.get_type() == 'DISTANCE_SENSOR':
            print("Current distance:",  response.current_distance)
            print("Command accepted")
            return response.current_distance
        else:
            print("Command failed")
            return 1
    else:
        print("Mavlink disconnected - no distance data")
        return 1
 ### PIXELS TO CM^2 CONVERSION VARS  ###
    # base values needs to be discovered by testing, once you have them for your specific camera
    # the code can convert any area at any heigth for this camera

### PIXELS TO CM^2 CONVERSION VARS  ###



baseArea = 46069  # base figure area in pixels
baseAreaCm = 100  # base figure area in cm^2 (real area)
baseH = 24  # base distance between the camera and the figure(heigth) in cm
actualH = 73  # distance received by the sensord (heigth) in cm
x = actualH/baseH

def usecannyfunc(img):
    return cv2.Canny(img, cannyMinVal, cannyMaxVal, L2gradient=True)


# pre set canny values (set for local and remote images)
cannyMinVal = 50
cannyMaxVal = 100

# only works for camera acess images
if showanyoutput and showcanny:
    cv2.namedWindow('Canny min and max')
    cv2.createTrackbar('Min', 'Canny min and max', cannyMinVal, 500, nothing)
    cv2.createTrackbar('Max', 'Canny min and max', cannyMaxVal, 500, nothing)




#RESOLUTION SETTINGS

totalArea = (cam.get(cv2.CAP_PROP_FRAME_WIDTH)*cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
print("Inicial resolution:", cam.get(cv2.CAP_PROP_FRAME_HEIGHT), "x", cam.get(cv2.CAP_PROP_FRAME_WIDTH))
print("Total Area:", totalArea)
resTrack = (cam.get(cv2.CAP_PROP_FRAME_HEIGHT), cam.get(cv2.CAP_PROP_FRAME_WIDTH))

#cam.set( cv2.CAP_PROP_FRAME_WIDTH, resTrack[0])
#cam.set( cv2.CAP_PROP_FRAME_HEIGHT, resTrack[1])


print("FIRST VALUE BY LIDAR BEFORE MAIN LOOP IS:", getdistance())


#### MAIN CODE #####

print("Entering main loop...")
while True:
    
    # returns image from the camera
    sucess, frame = cam.read()
    if not sucess:
        print("Error getting the frame, did you select de correct vidinput?")
        break
    if usemavlink:
        actualH = getdistance()

    if showanyoutput and showcanny:
        cannyMinVal = cv2.getTrackbarPos('Min', 'Canny min and max')
        cannyMaxVal = cv2.getTrackbarPos('Max', 'Canny min and max')

    # Gaussian Blur - reduce image noise. There are other functions to test for our purposes
    img = cv2.GaussianBlur(frame, (5, 5), 0)

    if showparsedvideo and showanyoutput:
        # Output of the image to be analized later
        cv2.imshow('CameraView', img)


    # Canny - binarize image contours by their gradient
    if usecanny:
        raw_contours = usecannyfunc(img)
    # minVal: any contour with gradient less than this value is 0
    # maxVal: any contour with gradient above than this value is 255
    # any value between this two that is connected to a value above max is 255, else is 0
    # L2gradient: when True uses an algoritm more precise
    # needs to be calibrated with different images and gradients, maybe even dinamically by the code itself

    # Find Contours in a binarized image, and returns its points
    contours, hierarchy = cv2.findContours(
        raw_contours, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # cv2.RETR_EXTERNAL - only take the external contours,
    # cv2.CHAIN_APPROX_SIMPLE - form the contours only with the essential points


    # DRAW DETECTED CONTOURS IN GREEN
    cv2.drawContours(frame, contours, -1, (0, 255, 0), 3)
    if showanyoutput and showfoundcontours:
        cv2.imshow('Found contours', frame)

    selContours = []

    for i, contour in enumerate(contours):
        if cv2.contourArea(contour) < aFilter:
            continue
        selContours.append(contour)

        Area = cv2.contourArea(contour)  # actual contour area (px)
        x = actualH/baseH
        actualArea = baseArea/(x*x)
        areacm = (Area*baseAreaCm)/actualArea
        # cv2.putText(frame, f'{i}: {areacm}', contour[0][0], cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 1, cv2.LINE_AA)
        print(f'Contour {i}: {Area}px |  {areacm}cm^2')
    #DRAW SELECTED CONTOURS IN RED
    cv2.drawContours(frame, selContours, -1, (0, 0, 255), 3)
    cv2.imshow('Selected Contours', frame)
    
    print('-'*30)

    video.write(frame)
    # press 'esc' to exit, set to 1 for automatic frame passing
    if cv2.waitKey(framePassing) & 0xFF == 27:
        break
cv2.destroyAllWindows()
video.release()
cam.release()
