# -*- coding: utf-8 -*-
import os, sys, time
sys.path.append('/usr/local/lib/python2.7/dist-packages/PyCapture2-0.0.0-py2.7-linux-x86_64.egg')
# adding PyCapture2 path
import cv2
import PyCapture2

"omit buildinfo, camerainfo"
numCams = 0

#set Camera
while not numCams:
    bus = PyCapture2.BusManager()
    numCams = bus.getNumOfCameras()
    print ("Locating Cameras... May retry for a few times.")
    time.sleep(0.7)

#Set camera on 0th index
#TODO: Enable 2 cameras streaming at the same time
cam = PyCapture2.Camera()
uid = bus.getCameraFromIndex(0)
cam.connect(uid)

#print camera info 
camInfo = cam.getCameraInfo()
print ("Camera model - ", camInfo.modelName)

def capIm():
    try:
        img = cam.retrieveBuffer()
    except PyCapture2.Fc2Error as fc2Err:
        print("Error retrieving buffer:", fc2Err)
        return False, []
    
    #Get colored data
    newimg = img.convert(PyCapture2.PIXEL_FORMAT.BGR)
    newimg.save("tmp.bmp", PyCapture2.IMAGE_FILE_FORMAT.BMP)
    data = cv2.imread('tmp.bmp', 0)
    return True, data

cam.startCapture()
    
cv2.namedWindow('PyCapImg', cv2.WINDOW_NORMAL)
#cv2.resizeWindow('PyCapImg', 500,550)

while cv2.waitKey(1)&0xFF != 27:
  ret, im = capIm()
  
  if not ret:
    break

#  cv2.imshow('PyCapImg', im)
  cv2.imshow('grey', im)

cam.stopCapture()
cam.disconnect()
cv2.destroyAllWindows()

try:
  os.remove('tmp.bmp')
except:
  pass




