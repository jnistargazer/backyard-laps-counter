import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont
from gpiozero import LED
from gpiozero import MotionSensor
from threading import Thread
from threading import _active as active_threads
from PyQt5.QtCore import QTimer, Qt
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
 
class AppLapCounterUI(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(500, 300)
 
        layout = QVBoxLayout()
 
        fnt = QFont('Open Sans', 240, QFont.Bold)
 
        self.lbl = QLabel()
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setFont(fnt)
        self.lbl.setText("0000")
        self.lbl.setStyleSheet("color: black")
 
        self.start_btn = QPushButton("Start", self)
        #self.start_btn.setToolTip('Click to start or stop the counter')
        self.start_btn.move(10,0)
        self.start_btn.clicked.connect(self.start_btn_clicked)
        self.start_btn.setStyleSheet('QPushButton {background-color: #FF0000; color: red;}')
        self.reset_btn = QPushButton("Rest", self)
        #self.reset_btn.setToolTip('Click to reset the counter to 0')
        self.reset_btn.move(120,0)
        self.reset_btn.clicked.connect(self.reset_btn_clicked)
        self.reset_btn.setStyleSheet('QPushButton {background-color: #FF0000; color: red;}')
        
        layout.addWidget(self.lbl)
        self.setLayout(layout)

        #timer = QTimer(self)
        #timer.timeout.connect(self.updateLabel)
        #timer.start(1000)
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
        self.start_btn.setStyleSheet('QPushButton {background-color: ' + bg_clr + '; color: black;}')
        self.start_btn.setText(txt)
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
        self.lbl.setText(displayText)
        self.lbl.setStyleSheet("color: {}".format(theColor))
        if Cheer:
            self.sound.play()
            Cheer = False
 
app = QApplication(sys.argv)
ui =  AppLapCounterUI()
ui.show()
app.exit(app.exec_())
