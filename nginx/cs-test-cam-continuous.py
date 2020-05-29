from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2

camera = PiCamera()
rawCapture = PiRGBArray(camera)


time.sleep(0.1)

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    image = frame.array
    cv2.imshow("Test Image", image)
    key = cv2.waitKey(0) & 0xFF
    rawCapture.truncate(0)
    if key == ord('q'):
        break

