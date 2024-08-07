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

### ENABLE/DISABLE EVERY OUTPUT WINDOW, EVEN CANNY VALUES CHANGERS###
showanyoutput = 1

### USE MAVLINK CONNECTION (turn on only on the RPi)
usemavlink = 0
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
            return 000
    else:
        print("Mavlink disconnected - no distance data")
        return 000
            

### PIXELS TO CM^2 CONVERSION VARS  ###
#RPi CAMERA 2.1:
#Vertical Field of View (VFoV) = 48,8´
#Horizontal Field of View (HFoV) = 62,2´
def AreaConverter(distance, Area):
    vx = 0.907 * distance #ratio between lidar distance and Vertical Field of View (VFoV) of 48,8´ - in case of using other camera the ratio = 2*tan([camera VFoV angle]/2)*x
    hx = 1.206 * distance #ratio between lidar distance and Horizontal Field of View (HFoV) of 62,2- in case of using other camera the ratio = 2*tan([camera HFoV angle]/2)*x

    S_multiplier = vx*hx
    actualArea = Area/totalArea*S_multiplier #convert to the estimated size it should be in the actual height (px)
    return float('{:.1f}'.format(actualArea))

def usehsvfunc(img):
    lh = cv2.getTrackbarPos('LowH', 'Control')
    ls = cv2.getTrackbarPos('LowS', 'Control')
    lv = cv2.getTrackbarPos('LowV', 'Control')
    hh = cv2.getTrackbarPos('HighH', 'Control')
    hs = cv2.getTrackbarPos('HighS', 'Control')
    hv = cv2.getTrackbarPos('HighV', 'Control')
    # Grayscaler by the H HSV values (H - Hue, S - Saturation, V - Value, instead or RGB)
    lower = np.array([lh, ls, lv], dtype="uint8")
    higher = np.array([hh, hs, hv], dtype="uint8")
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, w = img.shape[:2]
    return cv2.inRange(hsv, lower, higher)   

def usecannyfunc(img):
    return cv2.Canny(img, cannyMinVal, cannyMaxVal, L2gradient=True)



# pre set hsv values
iLowH = 100
iHighH = 200
iLowS = 0
iHighS = 126
iLowV = 82
iHighV = 100

# pre set canny values (set for local and remote images)
cannyMinVal = 50
cannyMaxVal = 100

if usehsv == 1:
    # dinamical control of hsv (useful when camera acessing)
    cv2.namedWindow('Control', cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Control", 400, 100) 
    cv2.createTrackbar("LowH", "Control", iLowH, 255, nothing)
    cv2.createTrackbar("HighH", "Control", iHighH, 255, nothing)
    cv2.createTrackbar("LowS", "Control", iLowS, 255, nothing)
    cv2.createTrackbar("HighS", "Control", iHighS, 255, nothing)
    cv2.createTrackbar("LowV", "Control", iLowV, 255, nothing)
    cv2.createTrackbar("HighV", "Control", iHighV, 255, nothing)

# only works for camera acess images
if showanyoutput:
    cv2.namedWindow('Canny min and max')
    cv2.createTrackbar('Min', 'Canny min and max', cannyMinVal, 500, nothing)
    cv2.createTrackbar('Max', 'Canny min and max', cannyMaxVal, 500, nothing)


cam = cv2.VideoCapture(vidinput)

#RESOLUTION SETTINGS

totalArea = (cam.get(cv2.CAP_PROP_FRAME_WIDTH)*cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
print("Inicial resolution:", cam.get(cv2.CAP_PROP_FRAME_HEIGHT), "x", cam.get(cv2.CAP_PROP_FRAME_WIDTH))
print("Total Area:", totalArea)
resTrack = (cam.get(cv2.CAP_PROP_FRAME_HEIGHT), cam.get(cv2.CAP_PROP_FRAME_WIDTH))

#cam.set( cv2.CAP_PROP_FRAME_WIDTH, resTrack[0])
#cam.set( cv2.CAP_PROP_FRAME_HEIGHT, resTrack[1])


print("FIRST VALUE BY LIDAR BEFORE MAIN LOOP IS:", getdistance())

if imageAcessMethod == 0:  # local image
    img = cv2.imread(imagePath)
    cannyMinVal = 50
    cannyMaxVal = 100
    canny = cv2.Canny(img, cannyMinVal, cannyMaxVal, L2gradient=True)

    contours, hierarchy = cv2.findContours(
        canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(img, contours, -1, (0, 255, 0), 3)
    cv2.imshow('Detected contours', img)

    selContours = []
    # FILTERS AND CALCULATES THE AREA FOR EACH CONTOUR
    for i, contour in enumerate(contours):
        if cv2.contourArea(contour) < aFilter:
            continue
        selContours.append(contour)

        # calcula a area em pixels a partir do contorno (precisao muito alta)
        area = cv2.contourArea(contour)  #contour area (px)
        actualArea = AreaConverter(getdistance(), area)  # converts to cm^2
        print(f'Contour {i}: {area}px  |   {actualArea}cm^2')
    cv2.drawContours(img, selContours, -1, (0, 0, 255), 3)
    cv2.imshow('Selected Contours', img)
    print('-'*30)
    while True:
        if cv2.waitKey(framePassing) & 0xFF == 27:
            break
    cv2.destroyAllWindows()
elif imageAcessMethod == 1:  # camera frames
    print("Entering main loop...")
    while True:
        # returns image from the camera
        sucess, frame = cam.read()
        if not sucess:
            print("Error getting the frame, did you select de correct vidinput?")
            break
        if showanyoutput:
            cannyMinVal = cv2.getTrackbarPos('Min', 'Canny min and max')
            cannyMaxVal = cv2.getTrackbarPos('Max', 'Canny min and max')

        # Gaussian Blur - reduce image noise. There are other functions to test for our purposes
        img = cv2.GaussianBlur(frame, (5, 5), 0)

        ### HSV REGULATOR TO EASE FIND OF CONTOURS###
        # avoid using in most cases
        if usehsv and showanyoutput:
            img = usehsvfunc(img)

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
        cv2.drawContours(frame, contours, -1, (0, 255, 0), 3)
        if showanyoutput:
            cv2.imshow('Found contours', frame)

        selContours = []

        for i, contour in enumerate(contours):
            if cv2.contourArea(contour) < aFilter:
                continue
            selContours.append(contour)

            Area = cv2.contourArea(contour)  # actual contour area (px)
            actualArea = AreaConverter(getdistance(), Area)
            
            areaPercent = float('{:.1f}'.format((Area / totalArea * 100)))
            print(f'Contour {i}: {Area}px | {areaPercent}%  |  {actualArea}cm^2')
        cv2.drawContours(frame, selContours, -1, (0, 0, 255), 3)
        if showanyoutput:
            cv2.imshow('Selected Contours', frame)
        print('-'*30)



        # press 'esc' to exit, set to 1 for automatic frame passing
        if cv2.waitKey(framePassing) & 0xFF == 27:
            break
    cv2.destroyAllWindows()
elif imageAcessMethod == 2:  # url images
    pass
else:
    print("[ERROR], invalid imageAcessMethod value")
cv2.destroyAllWindows()
