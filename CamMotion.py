#!/usr/bin/python3 

import picamera
import time
import picamera.array
import numpy as np

def start_camera0(motion_handler, nvecs=80, motion_threshold=100):
    print("Starting camera ...")
    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        camera.framerate = 30
        camera.start_recording(
           '/dev/null', format='h264',
           motion_output=MotionDetector(camera,
                                        motion_handler,
                                        nvecs,
                                        motion_threshold)
        )
        time.sleep(10)
        print("camera is recording ...")
        camera.wait_recording(1)
        print("camera stopping ...")
        camera.stop_recording()
        print("camera stopped")

def start_camera(motion_handler, nvecs=80, motion_threshold=100):
    print("Starting camera ...")
    camera = picamera.PiCamera()
    camera.resolution = (640, 480)
    camera.framerate = 15
    camera.start_recording(
        '/dev/null', format='h264',
        motion_output=MotionDetector(camera,
                motion_handler,
                nvecs,
                motion_threshold)
    )
    return camera


class MotionDetector(picamera.array.PiMotionAnalysis):
    def __init__(self, camera,handler, motion_threshold, active_vecs):
        super().__init__(camera)
        self.camera = camera
        self.motion = False
        self.threshold = motion_threshold
        self.num_active_vectors = active_vecs
        self.motion_handler = handler
        self.counter = 0

    def get_camera(self):
        return self.camera

    def analyse(self, a):
        a = np.sqrt(
            np.square(a['x'].astype(np.float)) +
            np.square(a['y'].astype(np.float))
            ).clip(0, 255).astype(np.uint8)
        # If there're more than num_active_vectors vectors with a magnitude
        # greater than threshold, then say we've detected motion
        if (a > self.threshold).sum() > self.num_active_vectors:
            if not self.motion and self.motion_handler:
                print("Motion detected")
                self.motion = True
                self.motion_handler.handle_motion(True)
                self.counter += 1
        else:
            if self.motion and self.motion_handler:
                print("Motion stopped")
                self.motion = False
                self.motion_handler.handle_motion(False)
