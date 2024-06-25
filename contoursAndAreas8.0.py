import cv2
import numpy as np
import urllib

# OPTIONS#

### ACESS METHOD ###
# 0 -> acess a local saved image (needs to inform the image path)
# 1 -> physical local camera acess (remember to set the correct vidinput value below according to your purposes)
# 2 -> remote images acess(web), useful for IP cameras, needs to inform the image url
imageAcessMethod = 1
imagePath = r""
imageUrl = ""

### AREA FILTER (IN px) ###
aFilter = 100  # every area smaller is disregarded

### FRAME/IMAGE PASSING ###
# 0 -> manual
# 1 or any other value (passing delay in ms) -> auto
framePassing = 0

### SHOW PARSED VIDEO WITH ALL THE FILTERS###
showparsedvideo = 1

### HSV TO EASE FIND OF CONTOURS###
# better not use, makes the image have too much noise (for some reason)
usehsv = 0

### CHOOSING INPUT###
# 0 - generally first camera in the system. Use 1 with virtual camera from OBS for testing purposes
vidinput = 0

'''HOW TO USE OBS FOR TESTING PURPOSES (and why)
1. Open OBS and add the source "Window Capture" (I prefer using Paint to capture)
2. In the menu "Control" press "Start Virtual Camera"
3. If VideoCapture() value is not "1" - change to this value
4. Run Python File - now it will scan only the Paint Window (any window, use whatever you prefer)
5. This way you can draw different shapes in real time and test them with this program, without the need to draw them on paper
   and show to the camera
'''

### PIXELS TO CM^2 CONVERSION VARS  ###
# base values needs to be discovered by testing, once you have them for your specific camera
# the code can convert any area at any heigth for this camera
baseH = 28  # base distance between the camera and the figure(heigth) in cm
actualH = 28  # distance received by the sensord (heigth) in cm
x = actualH/baseH
baseArea = 50000  # base figure area in pixels
baseAreaCm = 100  # base figure area in cm^2 (real area)
# converts the base area(already know for a specific height)...
actualBaseArea = baseArea/(x*x)
# to the estimated size it should be in the actual height (px)


def nothing(n):
    pass


# pre set hsv values
iLowH = 100
iHighH = 200
iLowS = 0
iHighS = 126
iLowV = 82
iHighV = 255

# pre set canny values (set for local and remote images)
cannyMinVal = 50
cannyMaxVal = 100

if usehsv == 1:
    # dinamical control of hsv (useful when camera acessing)
    cv2.namedWindow('Control')
    cv2.createTrackbar("LowH", "Control", iLowH, 255, nothing)
    cv2.createTrackbar("HighH", "Control", iHighH, 255, nothing)
    cv2.createTrackbar("LowS", "Control", iLowS, 255, nothing)
    cv2.createTrackbar("HighS", "Control", iHighS, 255, nothing)
    cv2.createTrackbar("LowV", "Control", iLowV, 255, nothing)
    cv2.createTrackbar("HighV", "Control", iHighV, 255, nothing)

# only works for camera acess images
cv2.namedWindow('Canny min and max')
cv2.createTrackbar('Min', 'Canny min and max', cannyMinVal, 500, nothing)
cv2.createTrackbar('Max', 'Canny min and max', cannyMaxVal, 500, nothing)

cam = cv2.VideoCapture(vidinput)

print(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(cam.get(cv2.CAP_PROP_FRAME_WIDTH))

if imageAcessMethod == 0:  # local image
    img = cv2.imread(imagePath)
    grayImg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(grayImg, (5, 5), 0)
    canny = cv2.Canny(blur, cannyMinVal, cannyMaxVal, L2gradient=True)

    contours, hierarchy = cv2.findContours(
        canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(img, contours, -1, (0, 255, 0), 3)
    smallImg = cv2.resize(img, (600, 800))  # only for img showing
    cv2.imshow('Detected contours', smallImg)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # FILTERS AND CALCULATES THE AREA FOR EACH CONTOUR
    for i, contour in enumerate(contours):
        if cv2.contourArea(contour) < aFilter:
            continue
        # calcula a area em pixels a partir do contorno (precisao muito alta)
        cv2.drawContours(img, contours, i, (0, 0, 255), 3)
        smallImg = cv2.resize(img, (600, 800))  # only for img showing
        cv2.imshow(f"Contour {i}", smallImg)

        area = cv2.contourArea(contour)  # actual contour area (px)

        areacm = (area*baseAreaCm)/actualBaseArea  # converts to cm^2
        print(f'Contour {i}: {area}px  |   {areacm}cm^2')

        cv2.waitKey(framePassing)
        print('-'*30)
elif imageAcessMethod == 1:  # camera frames
    while True:
        # returns image from the camera
        sucess, frame = cam.read()
        if not sucess:
            print("Error getting the frame, did you select de correct vidinput?")
            break

        cannyMinVal = cv2.getTrackbarPos('Min', 'Canny min and max')
        cannyMaxVal = cv2.getTrackbarPos('Max', 'Canny min and max')

        # Gaussian Blur - reduce image noise. There are other functions to test for our purposes
        img = cv2.GaussianBlur(frame, (5, 5), 0)

        ### HSV REGULATOR TO EASE FIND OF CONTOURS###
        # avoid using in most cases
        if usehsv == 1:
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
            img = cv2.inRange(hsv, lower, higher)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        if showparsedvideo == 1:
            # Output of the image to be analized later
            cv2.imshow('CameraView', img)

    ##################################### END OF IMAGE EDITING, BEGINNING OF CONTOURES#####################################

        # Canny - binarize image contours by their gradient
        raw_contours = cv2.Canny(
            img, cannyMinVal, cannyMaxVal, L2gradient=True)
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
        cv2.imshow('Found contours', frame)

        selContours = []

        for i, contour in enumerate(contours):
            if cv2.contourArea(contour) < aFilter:
                continue
            selContours.append(contour)
            area = cv2.contourArea(contour)  # actual contour area (px)

            areacm = (area*baseAreaCm)/actualBaseArea  # converts to cm^2
            print(f'Contour {i}: {area}px  |   {areacm}cm^2')
        cv2.drawContours(frame, selContours, -1, (0, 0, 255), 3)
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
