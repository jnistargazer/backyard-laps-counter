from imutils.video import VideoStream
import datetime
import imutils
import time, os, sys, argparse
import cv2

class MotionDetector:
    def __init__(self, min_area=20, record_len=5, show=False, output="/var/birding/capture"):
        self.show = show
        self.min_area = min_area
        self.record_len = record_len
        self.vs = cv2.VideoCapture(0)
        self.output = output
        time.sleep(2.0)
        if not self.vs.isOpened():
            print("Camera is not opened")
            sys.exit(1)

    def motion_detected(self, curr, prev):
        # compute the absolute difference between the current frame and
        # first frame
        delta = cv2.absdiff(prev, curr)
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
            timestamp = datetime.datetime.now().strftime("%m%d%Y-%I:%M:%S%p")
            cv2.imwrite("{}/bird-{}.jpg".format(self.output,timestamp), thresh)
            cv2.imwrite("{}/bird-{}-a.jpg".format(self.output,timestamp), prev)
            cv2.imwrite("{}/bird-{}-b.jpg".format(self.output,timestamp), curr)
            break
        return (motion, thresh, delta)

    def show_frame(self, frame):
        if self.show:
            cv2.imshow("Scene", frame)
    def detect_motion(self):
        # loop over the frames of the video
        motion_start = False
        # initialize the first frame in the video stream
        lap=0
        is_a_lap = False
        (w,h) = (int(self.vs.get(3)), int(self.vs.get(4)))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 28
        os.makedirs(self.output, exist_ok = True)
        timestamp = datetime.datetime.now().strftime("%m%d%Y-%I:%M:%S%p")
        video_cap = cv2.VideoWriter(
                  "{}/bird-{}.avi".format(self.output,timestamp),
                  fourcc, fps, (w,h))
        T0 = 0
        event = 0
        num_frames = 0
        prev_5_frames = []
        quit = False
        prevGrayedFrame = None
        while not quit:
            # grab the current frame
            T = time.time()
            DT = datetime.datetime.fromtimestamp(T).strftime("%A %d %B %Y %I:%M:%S%p")
            ret,frame = self.vs.read()
            
            cv2.putText(frame,"{}".format(DT),
                (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
            self.show_frame(frame)
            if T0 == 0:
                # resize the frame, convert it to grayscale, and blur it
                frame_resized = imutils.resize(frame, width=500)
                gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)
                if prevGrayedFrame is None:
                    # if the first frame is None, initialize it
                    prevGrayedFrame = gray
                    continue
                else:
                    prevGrayedFrame = gray
                motion,thresh,delta = self.motion_detected(gray,prevGrayedFrame)

            if motion:
                # Start recording timer if it isn't running
                if T0 == 0:
                    T0 = T
                    DT0 = datetime.datetime.fromtimestamp(T).strftime("%m/%d/%Y %I:%M:%S%p")
                    event += 1
                    num_frames = 0
                    for f in prev_5_frames:
                        video_cap.write(f)
                        num_frames += 1
                    prev_5_frames = []
            else:
                if len(prev_5_frames) == 5:
                    prev_5_frames = prev_5_frames[1:5]
                prev_5_frames.append(frame)

            while T0 > 0 and T - T0 <= self.record_len:  
                # Keep recording 10s
                cv2.putText(frame,"Event #{} @ {}".format(event, DT0),
                      (10, frame.shape[0] - 25),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
                video_cap.write(frame)
                num_frames += 1
                ret,frame = self.vs.read()
                self.show_frame(frame)
                T = time.time()
                # show the frame and record if the user presses a key
                key = cv2.waitKey(1) & 0xFF
                # if the `q` key is pressed, break from the lop
                if key == ord("q"):
                    quit = True
                    break
            T0 = 0
            if num_frames > 0:
                print("Event #{}: {} frames recorded".format(event,num_frames))
                num_frames = 0

            if quit is not True:
                # show the frame and record if the user presses a key
                key = cv2.waitKey(1) & 0xFF
                # if the `q` key is pressed, break from the lop
                if key == ord("q"):
                    quit = True
        # cleanup the camera and close any open windows
        if video_cap is not None:
            video_cap.release()
        self.vs.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    aparser = argparse.ArgumentParser()
    aparser.add_argument("-v", "--show", nargs="?", const="yes", default="no", help="Show video")
    aparser.add_argument("-o", "--output", default="./", help="video output dir")
    aparser.add_argument("-s", "--sensitivity", type=int, default=200, help="Motion detection sensitity (smaller number means more sensitive)")
    aparser.add_argument("-l", "--record-length", type=int, default=5, help="Video record length (in seconds) when motion detected")
    args = vars(aparser.parse_args())
    show = False
    sensitivity = 50
    record_len = 5
    if args.get("show", "false") in ["true", "yes", "True", "Yes"]:
        show = True
    if args.get("sensitivity", None):
        sensitivity = args.get("sensitivity")
    if args.get("output", None):
        output = args.get("output")
    if args.get("record_length", None):
        record_len = args.get("record_length")

    print("SHOW: {}, SENSITIVITY: {}, OUTPUT DIR: {}, RECORD-LENGTH: {}".format(show, sensitivity, output, record_len))
    motion_sensor = MotionDetector(min_area=sensitivity,
                                   show=show,
                                   output=output,
                                   record_len=record_len)
    motion_sensor.detect_motion()
