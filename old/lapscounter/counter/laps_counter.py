import sys
from gpiozero import LED
from gpiozero import MotionSensor
from threading import Thread
from threading import _active as active_threads
import pygame, time, ctypes
 
theColor = "black"
Cheer = False
Start = False 
Laps = 0
class MotionDetector(Thread):
    def __init__(self, label):
        super().__init__()
        MOTION_SENSOR_PIN = 4
        LED_PIN = 17
        self.led = LED(LED_PIN)
        self.sensor = MotionSensor(MOTION_SENSOR_PIN)
        self.led.off()
        self.label = label
    def run(self):
        self.start_counting()

    def start_counting(self):
        global theColor, Cheer, Start, Laps
        while True: 
            self.sensor.wait_for_motion()
            if not Start:
                continue
            if Laps > 0:
                if Laps % 10 == 0:
                    theColor="red"
                    Cheer = True
                else:
                    theColor="black"
                self.led.on()
            self.label.updateLabel()
            Laps += 1
            self.sensor.wait_for_no_motion() 
            self.led.off()
    def stop_counting(self):
         Start = False
 
class AppLapCounterUI:
    def __init__(self):
 
        pygame.init()
        self.sound = pygame.mixer.Sound("/home/pi/laps-counter/Cheer.wav")
        self.sound.set_volume(100)
        self.sensor = None

    def start_sensor(self):
        global Start
        Start = True
        if self.sensor:
            return
        self.sensor = MotionDetector(self)
        self.sensor.start()
    def stop_sensor(self):
        if self.sensor:
            self.sensor.stop_counting()
    def not_in_use(self):
        if not self.sensor:
            return
        if hasattr(self.sensor, '_thread_id'):
           id = self.sensor._thread_id
        else:
           for id, thrd in active_threads.items():
               if thrd == self.sensor:
                   break
        r = ctypes.pythonapi.PyThreadState_SetAsyncExc(id,ctypes.py_object(SystemExit))
        if r > 1:
            print('Failed to stop sensor')
            sys.exit(1)
        else:
            self.sensor.join()
            self.sensor = None
        
    def reset_btn_clicked(self):
        global Laps
        print("Counter reset to 0")
        Laps = 0
        self.updateLabel()
    def start_btn_clicked(self):
        global Start
        Start = not Start
        if Start:
            bg_clr = '#00FF00'
            txt = 'Stop'
            print("Starting sensor")
            self.start_sensor()
            print("Sensor started")
        else:
            bg_clr = '#FF0000'
            txt = 'Start'
            print("Stopping sensor")
            self.stop_sensor()
            print("Sensor stopped")
    def updateLabel(self):
        global Laps, theColor, Cheer
        print("Lap #{}".format(Laps))
        if Laps < 10:
            displayText = "000{}".format(Laps)
        elif Laps < 100:
            displayText = "00{}".format(Laps)
        elif Laps < 1000:
            displayText = "0{}".format(Laps)
        elif Laps < 10000:
            displayText = "{}".format(Laps)
        print("Lap #"+displayText)
        if Cheer:
            self.sound.play()
            Cheer = False
