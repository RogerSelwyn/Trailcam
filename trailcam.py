from gpiozero import MotionSensor
from datetime import datetime
import picamera
import time
import os
from utilities import (
    mountShare, logMessage, logError, storeVideo, 
    storeStill, processArgs, setupLog, updatePlex, 
    setupSlack, postSlackMessage, postSlackVideo, checkService
)
import settings

def main():
  settings.init()
  processArgs()
  if not settings.service and checkService():
      exit()
  setupLog()
  setupSlack()
  mountShare()
  pir = MotionSensor(18)

  logMessage('Starting - Record time ' + str(settings.recordtime) + ' seconds')

  # Wait an initial duration to allow PIR to settle
  time.sleep(10)

  while True:
    print('Waiting for motion')
    pir.wait_for_motion()
    logMessage('Motion detected recording for '+ str(settings.recordtime)+' seconds')
    if not settings.testmode:
        threadid = postSlackMessage('Hedgehog alert :hedgehog:')
    recordVideo = settings.rootPath + 'videos/video.h264'
    recordStill = settings.rootPath + 'videos/still.jpg'
    output_basefilename = "{}".format(datetime.now().strftime('%Y%m%d-%H%M'))
    with picamera.PiCamera() as cam:
        cam.rotation=180
        cam.resolution=(1640, 1232)
        cam.annotate_background = picamera.Color('black')
        cam.start_recording(recordVideo)
        start_time = datetime.now()
          
        start_record = True
        still_captured = False

        while pir.motion_detected:
            if start_record:
                start_record = False
            else:
                print('Still recording for '+ str(settings.recordtime)+' seconds')

            start = datetime.now()
            while (datetime.now() - start).seconds < settings.recordtime:
                cam.annotate_text = "Rog Cam "+datetime.now().strftime('%d-%m-%y %H:%M:%S')
                cam.wait_recording(0.2)
                if (datetime.now() - start_time).seconds > 2 and not still_captured:
                    logMessage('Still captured')
                    still_captured = True
                    cam.shutter_speed = 10000
                    cam.capture(recordStill, use_video_port=False)

        total_time = (datetime.now() - start_time).seconds
        cam.stop_recording()

    logMessage('Stopped recording after ' + str(total_time) + ' seconds')
    storeStill(recordStill, output_basefilename)
    time.sleep(5)

    output_video, output_filename = storeVideo(recordVideo, output_basefilename)
    if not settings.testmode:
        postSlackVideo(output_video, output_filename, output_filename, "Hedgehog")
    updatePlex()
    time.sleep(10)

if __name__== "__main__":
  main()