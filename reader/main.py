"""
An example of detecting ArUco markers with OpenCV.
"""
import os
import cv2
import sys

from cv2 import threshold
import cv2.aruco as aruco
import numpy as np
import math
from dotenv import load_dotenv
from socket_connection import connectSocket, sendData, is_connected

load_dotenv()

DEVICE = int(os.environ.get("WEBCAM"))
SOCKET_SERVER_URL = os.environ.get("SOCKET_SERVER_URL")

connectSocket(SOCKET_SERVER_URL)

# default values

adaptiveThreshWinSizeMin = 3
adaptiveThreshWinSizeMax = 90
adaptiveThreshWinSizeStep = 10
adaptiveThreshConstant = 2
margin=45
bin_threshold=100
captureBits=False

rows=220
cols=200
width=297
height=420

def run_opencv():
    global captureBits

    cap = cv2.VideoCapture(DEVICE)

    # create window
    cv2.startWindowThread()
    cv2.namedWindow("preview")
    cv2.namedWindow("controls")


    cropped = np.zeros((height,width,3), np.uint8)
    while cap.isOpened():
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        # create empty image (do I still need this? )
        # frame[:,:,2] = np.zeros([frame.shape[0], frame.shape[1]])

        # Check if frame is not empty
        if not ret:
            continue

        # Convert from BGR to RGB
        #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        (T, threshInv) = cv2.threshold(gray, adaptiveThreshWinSizeMax, 255, cv2.THRESH_BINARY_INV)

        alpha = 1.5  # Contrast control (1.0-3.0)
        beta = 0  # Brightness control (0-100)

        adjusted = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

        aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_1000)
        parameters = aruco.DetectorParameters_create()

        parameters.adaptiveThreshWinSizeMin = adaptiveThreshWinSizeMin
        parameters.adaptiveThreshWinSizeMax = adaptiveThreshWinSizeMax
        parameters.adaptiveThreshWinSizeStep = adaptiveThreshWinSizeStep
        parameters.adaptiveThreshConstant = adaptiveThreshConstant
        #parameters.adaptiveThreshConstant = 10
        #parameters.minMarkerPerimeterRate = 0.001
        #parameters.maxMarkerPerimeterRate = 8
        #parameters.maxErroneousBitsInBorderRate = 0.8
        #parameters.adaptiveThreshWinSizeMax = 10
        
        markers_pos, ids, _ = aruco.detectMarkers(frame, aruco_dict, parameters=parameters)
        frame = aruco.drawDetectedMarkers(frame, markers_pos, ids)
        if ids is not None:
            corner_ids=[[1],[2],[4],[3]]
            has_all = all(x in ids for x in corner_ids)
            if has_all:
                #print(corners)
                corners=[]
                for corner_id in corner_ids:
                    item_index=0
                    for id in ids:
                        if (id == corner_id):
                            break
                        item_index+=1
                    center = np.mean(markers_pos[item_index][0], axis=0)
                    center_coordinates = (int(center[0]), int(center[1]))          
                    corners.append(center_coordinates)
                    #cv2.circle(frame, center_coordinates, 10, (255, 0, 255), 2)

                points = np.int0(corners)

                # Define corresponding points in output image
                input_pts = np.float32(points)
                output_pts = np.float32([[0,0],[width,0],[width,height],[0,height]])

                # Get perspective transform and apply it
                M = cv2.getPerspectiveTransform(input_pts,output_pts)
                cropped = cv2.warpPerspective(frame,M,(width,height))

                cv2.polylines(frame, [points], 1, (255, 0, 0), 2)
            
                if captureBits == True or True:
                    img_grey = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
                    blur = cv2.GaussianBlur(img_grey,(5,5),0)
                    ret3,th3 = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
                    captureBitsFromImage(th3, width, height, rows, cols)
                    captureBits=False

        img_grey = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)

        blur = cv2.GaussianBlur(img_grey,(5,5),0)
        ret3,th3 = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        # th3 = cv2.threshold(img_grey,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        
        # Display the resulting frame
        cv2.imshow('preview', adjusted)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
    # After the loop release the cap object
    cap.release()
    # Destroy all the windows
    cv2.destroyAllWindows()


def captureBitsFromImage(img, width, height, rows, cols):
    global margin
    data_image = np.zeros((rows*4,cols*4,1), np.uint8)
    interval = (width-margin*2)/(cols)
    array_x = np.arange(margin+interval/2, width-margin, interval)
    array_y = np.arange(margin+interval/2, height-margin, interval)
    print("len", len(array_x))
    bin_array = [] 
    data_y = 0
    for pos_y in array_y:
        data_x=0
        for pos_x in array_x:
            k = img[math.floor(pos_y), math.floor(pos_x)]
            cv2.circle(img, [int(pos_x), int(pos_y)], 1, (255, 0, 255), 1)
            bin = '1' if k < bin_threshold else '0'
            bin_array.append(bin)
            #data_image[data_y, data_x]=k
            start_point=(int(data_x*4), int(data_y*4))
            end_point=(int(data_x*4+4), int(data_y*4+4))
            color = 255 if k > bin_threshold else 0
            data_image = cv2.rectangle(data_image, start_point, end_point, (color), -1)
            data_x+=1
        data_y+=1
    print(data_y, data_x)
    s = "".join(bin_array)
    numbers = [s[i:i+8] for i in range(0, len(s), 8)]
    cv2.imshow('data_image', data_image)
    bits = map(lambda s: int(s, 2), numbers) 
    bits = map(lambda n: alphabet[n], bits) 
    textSound = "".join(list(bits))
    print(textSound)
    if is_connected:
        sendData(textSound)

run_opencv()