import cv2
import numpy as np

            #OPTIONS#

###LIMITING CONTOURS by MANUAL threshold###
usethresh = 0
###LIMITING CONTOURS by ADAPTIVE threshold###
useadaptivethresh = 1
###SHOW PARSED VIDEO WITH ALL THE FILTERS###
showparsedvideo = 1
###HSV TO EASE FIND OF CONTOURS###
usehsv= 1
###CHOOSING INPUT###
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
def nothing(n):
    pass

iLowH = 100
iHighH = 200
iLowS = 0
iHighS = 126
iLowV = 82
iHighV = 255

cv2.namedWindow('Control')
cv2.createTrackbar("LowH", "Control", iLowH, 255, nothing)
cv2.createTrackbar("HighH", "Control", iHighH, 255, nothing)
cv2.createTrackbar("LowS", "Control", iLowS, 255, nothing)
cv2.createTrackbar("HighS", "Control", iHighS, 255, nothing)
cv2.createTrackbar("LowV", "Control", iLowV, 255, nothing)
cv2.createTrackbar("HighV", "Control", iHighV, 255, nothing)

cam = cv2.VideoCapture(vidinput) 


while True:
    # returns image from the camera 
    sucess, frame = cam.read()

    lh = cv2.getTrackbarPos('LowH', 'Control')
    ls = cv2.getTrackbarPos('LowS', 'Control')
    lv = cv2.getTrackbarPos('LowV', 'Control')
    hh = cv2.getTrackbarPos('HighH', 'Control')
    hs = cv2.getTrackbarPos('HighS', 'Control')
    hv = cv2.getTrackbarPos('HighV', 'Control')
    # Gaussian Blur - reduce image noise. There are other functions to test for our purposes
    img = cv2.GaussianBlur(frame, (5, 5), 0)

    # Morphological closing 
#    kernel = np.ones((5,5),np.uint8)
#    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)

    ###HSV REGULATOR TO EASE FIND OF CONTOURS###
    if usehsv == 1:

        #Grayscaler by the H HSV values (H - Hue, S - Saturation, V - Value, instead or RGB)
        lower = np.array([lh, ls, lv], dtype = "uint8")
        higher = np.array([hh, hs, hv], dtype = "uint8")
    
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, w = img.shape[:2]
        img = cv2.inRange(hsv, lower, higher)






    ###LIMITING CONTOURS by threshold###
    if usethresh == 1:
    
        #set a thresh
        thresh = 20
        #get threshold image
        ret, img = cv2.threshold(img, thresh, 255, cv2.THRESH_BINARY)
    if useadaptivethresh == 1:
        img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 20)

    if showparsedvideo == 1:
        cv2.imshow('CameraView', img) #Output of the image to be analized later

#####################################END OF IMAGE EDITING, BEGINNING OF CONTOURES#####################################
    
    # Canny - finds contours by binarizing the image and finding them by their gradient
    raw_contours = cv2.Canny(img, 50, 100, L2gradient=True)
    # valormin: any contour with gradient less than this value is not 
    # valormax: qualquer valor acima dele é considerado uma borda
    # valoresintermediarios que estiverem conectados a um valor max sao considerados bordas
    # L2gradient: when True uses an algoritm more precise
    # needs to be calibrated with different images and gradients, maybe even dinamically by the code itself
    

    #Find Contours. Basically there are already chosen contours in raw_contours, but this function kinda filters them
    contours, hierarchy = cv2.findContours(
        raw_contours, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # cv2.RETR_EXTERNAL - only take the external contours, 
    # cv2.CHAIN_APPROX_SIMPLE - form the contours only with the essential points
    


    
    img_contours = np.uint8(np.zeros((frame.shape[0],frame.shape[1]))) #generate empty contour array of arrays to be shown
    ext_contours = np.uint8(np.zeros((frame.shape[0],frame.shape[1]))) #generate empty contour array of arrays to show in the second window

    sel_contours=[]
    max=0

    for contour in contours:
        if contour.shape[0]>max:
            sel_contours=contour
            max=contour.shape[0]
    #print(sel_contours)

    
    cv2.drawContours(img_contours, sel_contours, -1, (255,255,255), 1)
    if len(sel_contours) > 0:
        area = cv2.contourArea(sel_contours)
    else:
        area = '0000'
    
    #print text accurately in the window
    font                   = cv2.FONT_HERSHEY_SIMPLEX #font (in case you'd want to change it?..)
    bottomLeftCornerOfText = (10, 30) #spacing from the left bottom side of the border (in pixels)
    fontScale              = 1
    fontColor              = (255,255,255) #color of the text
    thickness              = 1
    lineType               = 2

    cv2.putText(img_contours,f'{area} pixels', 
    bottomLeftCornerOfText, 
    font, 
    fontScale,
    fontColor,
    thickness,
    lineType)
    # write the contours to the window
    cv2.imshow('Result', img_contours)

    ###OUTPUT OF THE RAW CONTOURS###
    RAW_CONTOURS = 1
    if RAW_CONTOURS == 1:
        cv2.drawContours(ext_contours, contours, -1, (255,255,255), 1)
        cv2.imshow('RAW', ext_contours)


    # press 'esc' to exit
    if cv2.waitKey(1) & 0xFF == 27:
        break
cv2.destroyAllWindows()
