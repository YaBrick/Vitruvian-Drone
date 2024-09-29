import cv2
import numpy as np
from pymavlink import mavutil
import time
import sys
import logging

# Global variables
totalArea = None
message = None
# OPTIONS
aFilter = 200  # Area filter in pixels
framePassing = 1  # Frame passing delay in ms (0 -> manual)
usecanny = True  # Use Canny edge detection
vidinput = 0  # Video input (0 for first camera, 1 for virtual camera)

# Initialize camera and video writer
cam = cv2.VideoCapture(vidinput)
fourcc = cv2.VideoWriter_fourcc(*'XVID')
video_filename = f'Voo_{time.time()}.avi'
fps = 15.0
res = (640, 480)
video = cv2.VideoWriter(video_filename, fourcc, fps, res)

### LOGGER CONFIG ###
logger = logging.getLogger('LOGS')
logger.setLevel(logging.DEBUG)

# Create a formatter to define the log format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create a file handler to write logs to a file
file_handler = logging.FileHandler(f'logs/computing{time.time()}.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Create a stream handler to print logs to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # You can set the desired log level for console output
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)



# Canny parameters
cannyMinVal = 50
cannyMaxVal = 100

# Distance sensor configuration
usemavlink = False  # Change to True if using MAVLink
interval_us = 1e5

if usemavlink:
    connection_string = '/dev/serial0, 256000'
    master = mavutil.mavlink_connection(connection_string)
    logger.debug("Waiting for heartbeat")
    master.wait_heartbeat()
    logger.debug("Heartbeat received")
    

    message = master.mav.command_long_encode(
    master.target_system,         # target_system (typically the vehicle)
    master.target_component,      # target_component (typically the autopilot)
    mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # request command with interval 
    0,                            # confirmation
    132, # ID of the asked attribute (in this case DISTANCE_SENSOR)
    interval_us,                  # param2 (interval in microseconds)
    0, 0, 0, 0, 0)
    master.mav.send(message)


def get_distance():
    if usemavlink:
        
        response = master.recv_match(type='DISTANCE_SENSOR', blocking=False)
        if response and response.get_type() == 'DISTANCE_SENSOR':
            return response.current_distance
    logger.error("Mavlink disconnected or command failed")
    return 100

def count_center(contour):
    # Count moments of the contour
    M = cv2.moments(contour)

    # Count the center of the contour
    if M['m00'] != 0:
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
    else:
        # If M['m00'] == 0 (generally means that contour is too small)
        cx, cy = 0, 0
    return cx, cy

# Main loop
logger.debug("Entering main loop...")
while True:
    # Capture frame
    success, frame = cam.read()
    actualH = get_distance()
    actualH = actualH*1.05
    logger.debug(f'actualH: {actualH}cm')
    if not success:
        logger.critical("Error getting the frame, did you select the correct vidinput?")
        break
    # Process image
    img = cv2.GaussianBlur(frame, (5, 5), 0)
    if usecanny:
        raw_contours = cv2.Canny(img, cannyMinVal, cannyMaxVal, L2gradient=True)
        contours, _ = cv2.findContours(raw_contours, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) # RETR_TREE -> ALL CONTOURS
                                                                                            # RETR_EXTERNAL -> ONLY EXTERNAL

        # Draw contours
        cv2.drawContours(frame, contours, -1, (0, 255, 0), 3)

        selected_contours = []
        for i, contour in enumerate(contours):
            if cv2.contourArea(contour) < aFilter:
                continue
            
            selected_contours.append(contour)
            """ Area = cv2.contourArea(contour)  # actual contour area (px)
            x = actualH/baseH
            actualArea = baseArea/(x*x)
            areacm = (Area*baseAreaCm)/actualArea"""
            # 46069
            # 40cm perimetro
            areapx = cv2.contourArea(contour)  # contour area (px)
            perimeterpx = cv2.arcLength(contour, True) # contour perimeter (px)
            x = actualH/24
            actualArea = 46069/(x*x) # base area in actual heigth (px)
            actualPerimeter = 858.55/x # base perimeter in actual heigth (px)
            areacm = (areapx*100)/actualArea # contour area (cm^2)
            perimetercm = (perimeterpx*40)/actualPerimeter # contour perimeter (cm)
            logger.debug(f'{contour[0][0][0]}, {contour[0][0][1]}')

            #find center of the contour
            cx, cy = count_center(contour)
            cv2.putText(frame, f'A{i}: {areacm:3.2f}cm^2', (cx-50, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(frame, f'P{i}: {perimetercm:3.2f}cm', (cx-50, cy-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
            
            cv2.putText(frame, f'H: {actualH:3.2f}cm', (25, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,94,255), 2, cv2.LINE_AA)
            #cv2.putText(frame, str(areacm), contour[0][0], cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 1, cv2.LINE_AA)
            logger.info(f'Contour {i}: {areapx}px | {areacm:.2f}cm^2 ,\n Perimeter: {perimeterpx}px | {perimetercm:.2f}cm')

        # Draw selected contours
        cv2.drawContours(frame, selected_contours, -1, (0, 0, 255), 3)
    # Show results
    try:
        if sys.argv[1] and sys.argv[1] == 'ssh':
            pass
    except:
        cv2.imshow('Contours', frame)
    video.write(frame)

    # Break on ESC key
    if cv2.waitKey(framePassing) & 0xFF == 27:
        break

# Cleanup
cv2.destroyAllWindows()
video.release()
cam.release()
