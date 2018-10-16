# -*- coding: utf-8 -*-
import sys
sys.path.append('')
import PySpin
import cv2
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
MINR = int(0.005 * SCR_WID)
MAXR = int(0.06  * SCR_WID)
#MINDIST = int(0.10 * SCR_WID)
MINDIST = MAXR

def main():
    """
    Example entry point; please see Enumeration example for more in-depth
    comments on preparing and cleaning up the system.

    :return: True if successful, False otherwise.
    :rtype: bool
    """    
    # Retrieve singleton reference to system object
    system = PySpin.System.GetInstance()
    
    # Retrieve list of cameras from the system
    cam_list = system.GetCameras()
    
    num_cameras = cam_list.GetSize()
    
    print 'Number of cameras detected: %d' % num_cameras    
    
    # Finish if there are no cameras
    if num_cameras == 0:
    
        # Clear camera list before releasing system
        cam_list.Clear()
    
        # Release system instance
        system.ReleaseInstance()
    
        print 'Not enough cameras!'
        raw_input('Done! Press Enter to exit...')
        return False
    
    # Run address of each camera
    cam = cam_list.GetByIndex(0)
    
    
    # Retrieve TL device nodemap and print device information
    nodemap_tldevice = cam.GetTLDeviceNodeMap()
    
    # Initialize camera
    cam.Init()
    
    # Retrieve GenICam nodemap
    nodemap = cam.GetNodeMap()
    
    # Acquire images        
    # In order to access the node entries, they have to be casted to a pointer type (CEnumerationPtr here)
    node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
    
    if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
        print 'Unable to set acquisition mode to continuous (enum retrieval). Aborting...'
        return False

    # Retrieve entry node from enumeration node
    node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
    if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(node_acquisition_mode_continuous):
        print 'Unable to set acquisition mode to continuous (entry retrieval). Aborting...'
        return False

    # Retrieve integer value from entry node
    acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()

    # Set integer value from entry node as new value of enumeration node
    node_acquisition_mode.SetIntValue(acquisition_mode_continuous)
    
    cam.TLStream.StreamBufferHandlingMode.SetValue(PySpin.StreamBufferHandlingMode_NewestFirst)

    print 'Acquisition mode set to continuous...'

    #  Begin acquiring images
    #
    #  *** NOTES ***
    #  What happens when the camera begins acquiring images depends on the
    #  acquisition mode. Single frame captures only a single image, multi
    #  frame catures a set number of images, and continuous captures a
    #  continuous stream of images. Because the example calls for the
    #  retrieval of 10 images, continuous mode has been set.
    #
    #  *** LATER ***
    #  Image acquisition must be ended when no more images are needed.
    cam.BeginAcquisition()

    print 'Acquiring images...'

    #  Retrieve device serial number for filename
    #
    #  *** NOTES ***
    #  The device serial number is retrieved in order to keep cameras from
    #  overwriting one another. Grabbing image IDs could also accomplish
    #  this.
    device_serial_number = ''
    node_device_serial_number = PySpin.CStringPtr(nodemap_tldevice.GetNode('DeviceSerialNumber'))

    if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
        device_serial_number = node_device_serial_number.GetValue()
        print 'Device serial number retrieved as %s...' % device_serial_number
    
    cv2.namedWindow('PyCapImg', cv2.WINDOW_GUI_NORMAL)
    cv2.resizeWindow('PyCapImg', 500,550)
    
    while cv2.waitKey(1)&0xFF != 27:
        try:
            image_result = cam.GetNextImage()
            
            if image_result.IsIncomplete():
                print 'Image incomplete with image status %d ...' % image_result.GetImageStatus()

            else:

                #  Convert image to mono 8
                #
                #  *** NOTES ***
                #  Images can be converted between pixel formats by using
                #  the appropriate enumeration value. Unlike the original
                #  image, the converted one does not need to be released as
                #  it does not affect the camera buffer.
                #
                #  When converting images, color processing algorithm is an
                #  optional parameter.
                image_converted = image_result

                filename = 'Acquisition.bmp'

                #  Save image
                #
                #  *** NOTES ***
                #  The standard practice of the examples is to use device
                #  serial numbers to keep images of one device from
                #  overwriting those of another.
                image_converted.Save(filename)
                print 'Image saved at %s' % filename

                #  Release image
                #
                #  *** NOTES ***
                #  Images retrieved directly from the camera (i.e. non-converted
                #  images) need to be released in order to keep from filling the
                #  buffer.
                image_result.Release()
                print ''
                
                im = cv2.imread(filename, 3)
                
                "Convert BGR to HSV"
                hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
                #define range of blue color in HSV
                lower_red = np.array([86,80,80])
                upper_red = np.array([120,255,255])
                lower_green = np.array([40,70,70])
                upper_green = np.array([90,255,255])
                lower_blue = np.array([110,50,50])
                upper_blue = np.array([130,255,255])
                
                "opencv filters"
                mask = cv2.inRange(hsv, lower_green, upper_green)    # Threshold the HSV image to get only blue colors
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones(OPEN_KERNEL_SHAPE, dtype = np.uint8)) # Close operation for denoise
                
                # Bitwise-AND mask and original image
                #res = cv2.bitwise_and(im,im, mask= mask)
                
                "Blur the corrected result for denoising and debanding"
                mask = cv2.GaussianBlur(mask, (5, 5), 0)
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
                
                cv2.imshow('PyCapImg', im)
                

        except PySpin.SpinnakerException as ex:
            print 'Error: %s' % ex
            return False
        
    # Release reference to camera
    # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being automatically
    # cleaned up when going out of scope.
    # The usage of del is preferred to assigning the variable to None.
    del cam

    # Clear camera list before releasing system
    cam_list.Clear()

    # Release system instance
    system.ReleaseInstance()
    
if __name__ == '__main__':
    main()
