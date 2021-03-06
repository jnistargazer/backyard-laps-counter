from imutils.video import VideoStream
import argparse
import datetime
import imutils
import time
import cv2

class MotionDetector:
    def __init__(self, src="picam", show=False):
        self.src = src
        self.show = show
        if self.src == "picam":
            self.vs = VideoStream(src=0).start()
            time.sleep(2.0)
        # otherwise, we are reading from a video file
        else:
            self.vs = cv2.VideoCapture(src)
# initialize the first frame in the video stream
        self.firstFrame = None
    def detect_motion(self, motion_handler):
        # loop over the frames of the video
        motion_start = False
        motions = 0
        while True:
            # grab the current frame and initialize the occupied/unoccupied
            # text
            frame = vs.read()
            frame = frame if src == "picam" else frame[1]
            # if the frame could not be grabbed, then we have reached the end
            # of the video
            if frame is None:
                break
            # resize the frame, convert it to grayscale, and blur it
            frame = imutils.resize(frame, width=500)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            # if the first frame is None, initialize it
            if firstFrame is None:
                firstFrame = gray
                continue
            # compute the absolute difference between the current frame and
            # first frame
            frameDelta = cv2.absdiff(firstFrame, gray)
            thresh = cv2.threshold(frameDelta, 50, 255, cv2.THRESH_BINARY)[1]
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
                if cv2.contourArea(c) < args["min_area"]:
                    continue
                motion = True
                break
            if motion:
                if not motion_start:
                    motion_start = True
                    self.motion_handler.handle_motion()
            else:
                motion_start = False
            if self.show:
                text = "LAP {}".format(motions)
                # draw the text and timestamp on the frame
                cv2.putText(frame, text, (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
                # show the frame and record if the user presses a key
                cv2.imshow("Security Feed", frame)
                cv2.imshow("Thresh", thresh)
                cv2.imshow("Frame Delta", frameDelta)
                key = cv2.waitKey(1) & 0xFF
                # if the `q` key is pressed, break from the lop
                if key == ord("q"):
                    break
    # cleanup the camera and close any open windows
    self.vs.stop() if self.src == "picam" else vs.release()
    cv2.destroyAllWindows()
