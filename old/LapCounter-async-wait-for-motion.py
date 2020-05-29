#!/usr/bin/env python3
import sys
from gpiozero import LED
from gpiozero import MotionSensor
from threading import Thread
from threading import _active as active_threads
import pygame, time, ctypes
import time, signal
import asyncio
import datetime
import random
import websockets
from websockets import WebSocketServerProtocol
 
WS_PORT = 5678
MOTION_SENSOR_PIN = 4
LED_PIN = 17
Start = False 
MotionSensed = False
Laps = -1
clients = set()

class CheerLeader(Thread):
    def __init__(self):
        super().__init__()
        pygame.init()
        self.sound = pygame.mixer.Sound("/home/pi/workspace/laps-counter/Cheer.wav")
        self.sound.set_volume(100)
    def run(self):
        global Laps
        cheered = False
        while True:
            if Laps > 0 and Laps % 10 == 0:
                if not cheered:
                    self.sound.play()
                    cheered = True
            else:
                cheered = False
                time.sleep(1.0)

async def register(wsock):
    global clients, Laps
    #print("A new client registered: {}".format((wsock,Laps)))
    clients.add((wsock,Laps))

async def unregister(client):
    global clients
    #print("A client unregistered: {}".format(client))
    clients.remove(client)

async def wait_for_motion():
    global Start, Laps, SENSOR
    await asyncio.wait(asyncio.ensure_future(SENSOR.wait_for_motion()))
    print(f"Motion! Start?{Start}")
    if Start:
        #print("Montion detected and counted!")
        Laps += 1
    #else:
        #print("Montion detected but not counted")
    LED.on()
async def wait_for_no_motion():
     global SENSOR
     SENSOR.wait_for_no_motion()
     print("Motion stopped!")
     LED.off()

async def update_client(client, laps):
      print("update client!")
      try:
          wsock, L = client
          if L:
              L = laps - L
              print("sending ")
              await wsock.send(str(L))
              print("sent ")

      except Exception as e:
          print(str(e))
          print("Client {} seems gone".format(client))
          await unregister(client)

async def producer_handler(wsock, path):
    global Laps, Start
    while True:
        await wait_for_motion()
        if Start:
            print("Updating clients")
            await asyncio.wait([update_client(client, Laps) for client in clients])
        await wait_for_no_motion()


async def commander(cmd):
    global Start
    print(cmd)
    if cmd == "start":
       print("Set Start to True!")
       Start = True
    elif cmd == "stop":
       Start = False
    elif cmd == "reset":
       Laps = 0
    
async def consumer_handler(wsock, path):
    while True:
        async for msg in wsock:
            print(f"msg = {msg}")
            await commander(msg)

async def handler(wsock, path):
    await register(wsock)
    consumer = asyncio.ensure_future(
        consumer_handler(wsock, path)
    ) 
    producer = asyncio.ensure_future(
        producer_handler(wsock, path)
    ) 

    done, pending = await asyncio.wait(
        [consumer, producer],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()

cheer = CheerLeader()
cheer.start()

old_signal_handler = signal.getsignal(signal.SIGINT)
def exit_cleanup(sig, tmp):
    global LED
    LED.off()
    signal.signal(signal.SIGINT, old_signal_handler)
    thrds = active_threads.items()
    for id, thrd in thrds:
        if thrd == cheer:
            r = ctypes.pythonapi.PyThreadState_SetAsyncExc(id,ctypes.py_object(SystemExit))
            if r > 1:
                print('Failed to stop sensor')
                sys.exit(1)
            else:
                thrd.join()
    sys.exit(0)

LED = LED(LED_PIN)
SENSOR = MotionSensor(MOTION_SENSOR_PIN)

signal.signal(signal.SIGINT, exit_cleanup)

print(f"Starting WS server at port {WS_PORT}")
start_server = websockets.serve(handler, "0.0.0.0", WS_PORT)

loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.run_forever()
cheer.join()
