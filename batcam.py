# Import all the things we need
import os
import time
from datetime import datetime

import picamera
from gpiozero import MotionSensor

import settings
from utilities import Bat_Log

_LOGGER = Bat_Log(settings.rootPath)


class Bat_Cam:
    def __init__(self):
        self.cam = picamera.PiCamera()
        self.cam.rotation = settings.camRotation
        self.cam.resolution = settings.camResolution
        self.cam.annotate_background = picamera.Color("black")
        self.recordVideo = None
        self.motionLogged = False

        # PIR is on pin 18
        self.pir = MotionSensor(18)
        self.pir.when_motion = self.motionDetected

        self.cam.start_preview()
        time.sleep(2)
        # print(self.cam.awb_mode)

    def capture_video(self):
        self.motionLogged = False
        start = datetime.now()
        self.start_capture()

        try:
            while (datetime.now() - start).seconds < settings.recordTime:
                self.cam.annotate_text = settings.camTitle + " " + datetime.now().strftime("%d-%m-%y %H:%M:%S")
                # time.sleep(2 / 10)
                self.cam.wait_recording(0.2)
        except KeyboardInterrupt:
            _LOGGER.logMessage("Keyboard interupt")
            self.stop_capture()
            raise

        self.stop_capture()

    def start_capture(self):
        output_basefilename = "{}".format(datetime.now().strftime("%Y%m%d-%H%M%S"))
        self.recordVideo = settings.rootPath + "videos/" + output_basefilename + ".h264"
        _LOGGER.logMessage("Start capture: " + self.recordVideo)
        self.cam.start_recording(self.recordVideo + ".tmp", format="h264")

    def stop_capture(self):
        self.cam.stop_recording()
        if self.motionLogged:
            _LOGGER.logMessage("Stop capture - motion detected: " + self.recordVideo)
            os.rename(self.recordVideo + ".tmp", self.recordVideo)
        else:
            _LOGGER.logMessage("Stop capture - deleted: " + self.recordVideo)
            os.remove(self.recordVideo + ".tmp")

    # Motion Detected
    def motionDetected(self):
        self.motionLogged = True
        _LOGGER.logMessage("Motion detected")
        return


# Initiate everything
if __name__ == "__main__":
    _LOGGER.logMessage("Starting")
    batcam = Bat_Cam()
    try:
        _LOGGER.logMessage("Starting camera")
        while True:
            batcam.capture_video()

    except KeyboardInterrupt:
        _LOGGER.logMessage("Stopping camera")

    _LOGGER.logMessage("Finishing")
