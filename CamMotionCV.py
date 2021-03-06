from imutils.video import VideoStream
import datetime
import imutils
import time, os, sys
import cv2

class MotionDetector:
    def __init__(self, src="picam", show=False, min_area=250):
        self.src = src
        self.show = show
        self.capture = False
        self.min_area = min_area
        if self.src == "picam":
            #self.vs = VideoStream(src=0).start()
            self.vs = cv2.VideoCapture(0)
            time.sleep(2.0)
        else:
            # otherwise, we are reading from a video file
            self.vs = cv2.VideoCapture(self.src)

        if not self.vs.isOpened():
            print("Camera is not opened")
            sys.exit(1)
    def set_capture(self, flag):
        self.capture = flag
    def detect_motion(self, motion_handler):
        # loop over the frames of the video
        motion_start = False
        # initialize the first frame in the video stream
        motionStartFrame = None
        lap=0
        is_a_lap = False
        (w,h) = (int(self.vs.get(3)), int(self.vs.get(4)))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_cap = None
        fps = 10
        cap_path = os.environ.get('CAPTURE_DIR', None)
        cap_path = cap_path if cap_path else "./capture" 
        os.makedirs(cap_path, exist_ok = True)
        while True:
            # grab the current frame and initialize the occupied/unoccupied
            # text
            ret,frame = self.vs.read()
            #frame = frame if self.src == "picam" else frame[1]
            # if the frame could not be grabbed, then we have reached the end
            # of the video
            if frame is None:
                print("No frame available")
                break
            # resize the frame, convert it to grayscale, and blur it
            frame1 = imutils.resize(frame, width=500)
            gray = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            # if the first frame is None, initialize it
            if motionStartFrame is None:
                motionStartFrame = gray
                continue
            # compute the absolute difference between the current frame and
            # first frame
            frameDelta = cv2.absdiff(motionStartFrame, gray)
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
                if cv2.contourArea(c) < self.min_area:
                    continue
                motion = True
                break
            if motion:
                if not motion_start:
                    #print("Motion started")
                    motion_start = True
                    is_a_lap = motion_handler.handle_motion(True)
                    if self.capture and is_a_lap and video_cap is None:
                        video_cap = cv2.VideoWriter(
                                "{}/lap{}.avi".format(cap_path,lap),
                                fourcc, fps, (w,h))
                        lap += 1

                if video_cap is not None:
                    video_cap.write(frame)
            else:
                is_a_lap = False
                if motion_start:
                    #print("Motion stopeed")
                    motion_start = False
                    motion_handler.handle_motion(False)
                if video_cap:
                    video_cap.write(frame)
                    video_cap.release()
                    video_cap = None
            motionStartFrame = gray
            if self.show:
                text = "LAP {}".format(lap)
                # draw the text and timestamp on the frame
                cv2.putText(frame, text, (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
                # show the frame and record if the user presses a key
                cv2.imshow("Scene", frame)
                cv2.imshow("Thresh", thresh)
                cv2.imshow("Diff", frameDelta)
                key = cv2.waitKey(1) & 0xFF
                # if the `q` key is pressed, break from the lop
                if key == ord("q"):
                    break
        # cleanup the camera and close any open windows
        if video_cap is not None:
            video_cap.release()
        #self.vs.stop() if self.src == "picam" else self.vs.release()
        self.vs.release()
        cv2.destroyAllWindows()
