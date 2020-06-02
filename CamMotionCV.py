from imutils.video import VideoStream
import datetime
import imutils
import time, os, sys
import cv2

class MotionDetector:
    def __init__(self, min_area=20):
        self.capture = False
        self.min_area = min_area
        self.prevGrayedFrame = None
        self.vs = cv2.VideoCapture(0)
        time.sleep(2.0)
        if not self.vs.isOpened():
            print("Camera is not opened")
            sys.exit(1)

    def motion_detected(self, frame, gray):
            frame = imutils.resize(frame, width=500)
            # compute the absolute difference between the current frame and
            # first frame
            delta = cv2.absdiff(self.prevGrayedFrame, gray)
            thresh = cv2.threshold(delta, 20, 255, cv2.THRESH_BINARY)[1]
            # dilate the thresholded image to fill in holes, then find contours
            # on thresholded image
            thresh = cv2.dilate(thresh, None, iterations=2)
            cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            # loop over the contours
            motion = False
            for c in cnts:
                # if the contour is too small, ignore it
                if cv2.contourArea(c) < self.min_area:
                    continue
                motion = True
                break
            return (motion, thresh, delta)

    def detect_motion(self):
        # loop over the frames of the video
        motion_start = False
        # initialize the first frame in the video stream
        lap=0
        is_a_lap = False
        (w,h) = (int(self.vs.get(3)), int(self.vs.get(4)))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 10
        cap_path = "./capture" 
        os.makedirs(cap_path, exist_ok = True)
        timestamp = datetime.datetime.now().strftime("%m%d%Y-%I:%M:%S%p")
        video_cap = cv2.VideoWriter(
                  "{}/bird-{}.avi".format(cap_path,timestamp),
                  fourcc, fps, (w,h))
        T0 = 0
        while True:
            # grab the current frame
            T = time.time()
            ret,frame = self.vs.read()
            # resize the frame, convert it to grayscale, and blur it
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            # if the first frame is None, initialize it
            if self.prevGrayedFrame is None:
                self.prevGrayedFrame = gray
                continue
            if T0 == 0:
                motion,thresh,delta = self.motion_detected(frame, gray)
            else:
                pass
                # We do not do motion detection when recording is going on
            self.prevGrayedFrame = gray
            cv2.putText(frame,
                      datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                      (10, frame.shape[0] - 10),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            # show the frame and record if the user presses a key
            cv2.imshow("Scene", frame)
            #cv2.imshow("Thresh", thresh)
            #cv2.imshow("Diff", delta)

            if motion:
                # Start recording timer if it isn't running
                if T0 == 0:
                    T0 = T

            if T0 > 0 and T - T0 <= 10:  
                # Keep recording 10s
                video_cap.write(frame)
                time.sleep(0.0417)
            elif T0 > 0:
                # If we come here, we know we have finished a 10s recording
                # Turn off the timer
                T0 = 0
            else:
                # No motion detected as the timer is not started
                pass
            key = cv2.waitKey(1) & 0xFF
            # if the `q` key is pressed, break from the lop
            if key == ord("q"):
                break
        # cleanup the camera and close any open windows
        if video_cap is not None:
            video_cap.release()
        self.vs.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    motion_sensor = MotionDetector(min_area=20)
    motion_sensor.detect_motion()
