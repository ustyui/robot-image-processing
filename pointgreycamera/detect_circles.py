# -*- coding: utf-8 -*-
import os, sys, time
#sys.path.append('/usr/local/lib/python2.7/dist-packages/PyCapture2-0.0.0-py2.7-linux-x86_64.egg')
# adding PyCapture2 path
import cv2
import PyCapture2
import numpy as np

"omit buildinfo, camerainfo"
numCams = 0

"Operation parameters"
#CLOSE_KERNEL_SHAPE = (3,3)
#CLOSE_KERNEL_SHAPE = (9,9)
#OPEN_KERNEL_SHAPE = (9,9)
OPEN_KERNEL_SHAPE = (13,9)

"Target screen size (16/9) "
SCR_LEN = 1920
SCR_WID = 1080

"Expected range of radius of circles"
MINR = int(0.01 * SCR_WID)
MAXR = int(0.06  * SCR_WID)
#MINDIST = int(0.10 * SCR_WID)
MINDIST = MAXR

"set Camera"
while not numCams:
    bus = PyCapture2.BusManager()
    numCams = bus.getNumOfCameras()
    print ("Locating Cameras... May retry for a few times.")
    time.sleep(0.7)

"Set camera on 0th index"
#TODO: Enable 2 cameras streaming at the same time
cam = PyCapture2.Camera()
uid = bus.getCameraFromIndex(0)
cam.connect(uid)

"print camera info "
camInfo = cam.getCameraInfo()
print ("Camera model - ", camInfo.modelName)

"capture image"
def capIm():
    try:
        img = cam.retrieveBuffer()
    except PyCapture2.Fc2Error as fc2Err:
        print("Error retrieving buffer:", fc2Err)
        return False, []
    
    #Get colored data
    newimg = img.convert(PyCapture2.PIXEL_FORMAT.BGR)
    newimg.save("tmp.bmp", PyCapture2.IMAGE_FILE_FORMAT.BMP)
    data = cv2.imread('tmp.bmp', 3)
    return True, data

"set properties of the camera"
cam.setProperty(type = PyCapture2.PROPERTY_TYPE.AUTO_EXPOSURE, autoManualMode = True)
cam.setProperty(type = PyCapture2.PROPERTY_TYPE.GAIN, autoManualMode = False)
cam.setProperty(type = PyCapture2.PROPERTY_TYPE.AUTO_EXPOSURE, onOff = True)
cam.setProperty(type = PyCapture2.PROPERTY_TYPE.GAMMA, onOff = True)

"start"
cam.startCapture()
    
cv2.namedWindow('PyCapImg', cv2.WINDOW_GUI_NORMAL)
cv2.resizeWindow('PyCapImg', 500,550)

while cv2.waitKey(1)&0xFF != 27:
    ret, im = capIm()
  
    if not ret:
        break
    "Convert BGR to HSV"
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    #define range of blue color in HSV
    lower_green = np.array([30,80,80])
    upper_green = np.array([90,255,255])
    lower_blue = np.array([110,50,50])
    upper_blue = np.array([130,255,255])
    
    "opencv filters"
    mask = cv2.inRange(hsv, lower_green, upper_green)    # Threshold the HSV image to get only blue colors
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones(OPEN_KERNEL_SHAPE, dtype = np.uint8)) # Close operation for denoise
    
    # Bitwise-AND mask and original image
    #res = cv2.bitwise_and(im,im, mask= mask)
    
    "Blur the corrected result for denoising and debanding"
    mask = cv2.GaussianBlur(mask, (3, 3), 0)
    edges = cv2.Canny(mask,250,300)
    
    "detect circles"
    circles = cv2.HoughCircles(edges, cv2.HOUGH_GRADIENT,
          dp=2, minDist=MINDIST, param1=25, param2=30,
          minRadius=MINR, maxRadius=MAXR )
    print circles
    
    "put circles on the image"
    if circles is not None and len(circles) > 0:
        circles = circles[0]
        for (x,y,r) in circles:
            x,y,r = int(x), int(y), int(r)
            cv2.circle(im, (x, y), r, (255, 0, 0), 10)
        
#  cv2.imshow('PyCapImg', im)
    cv2.imshow('PyCapImg', im)

cam.stopCapture()
cam.disconnect()
cv2.destroyAllWindows()

try:
    os.remove('tmp.bmp')
except:
  pass




