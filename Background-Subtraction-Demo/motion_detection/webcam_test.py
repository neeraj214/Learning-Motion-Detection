# Simple webcam test script
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret: print('Webcam OK')
cap.release()