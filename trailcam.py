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
                if (datetime.now() - start_time).seconds > settings.stillSeconds and not still_captured and settings.stillSeconds > 0:
                    logMessage('Still captured')
                    still_captured = True
                    logMessage('Exposure Speed 1: ' + str(cam.exposure_speed) + ' Shutter Speed: ' + str(cam.shutter_speed) + ' ISO: ' +str(cam.iso) + ' AG: ' +str(cam.analog_gain) + ' DG: ' +str(cam.digital_gain) + ' AWB: ' +str(cam.awb_gains) + ' Brightness: ' +str(cam.brightness) + ' Contrast: ' +str(cam.contrast) + ' EC: ' +str(cam.exposure_compensation))
                    storeAWB = cam.awb_gains
                    print(storeAWB)
                    cam.shutter_speed = 10000
                    logMessage('Exposure Speed 2: ' + str(cam.exposure_speed) + ' Shutter Speed: ' + str(cam.shutter_speed) + ' ISO: ' +str(cam.iso) + ' AG: ' +str(cam.analog_gain) + ' DG: ' +str(cam.digital_gain) + ' AWB: ' +str(cam.awb_gains) + ' Brightness: ' +str(cam.brightness) + ' Contrast: ' +str(cam.contrast) + ' EC: ' +str(cam.exposure_compensation))
                    
                    cam.capture(recordStill, use_video_port=False)
                    logMessage('Exposure Speed 3: ' + str(cam.exposure_speed) + ' Shutter Speed: ' + str(cam.shutter_speed) + ' ISO: ' +str(cam.iso) + ' AG: ' +str(cam.analog_gain) + ' DG: ' +str(cam.digital_gain) + ' AWB: ' +str(cam.awb_gains) + ' Brightness: ' +str(cam.brightness) + ' Contrast: ' +str(cam.contrast) + ' EC: ' +str(cam.exposure_compensation))
                    cam.shutter_speed = 0
                    cam.awb_mode = 'off'
                    cam.awb_gains = storeAWB
                    logMessage('Exposure Speed 4: ' + str(cam.exposure_speed) + ' Shutter Speed: ' + str(cam.shutter_speed) + ' ISO: ' +str(cam.iso) + ' AG: ' +str(cam.analog_gain) + ' DG: ' +str(cam.digital_gain) + ' AWB: ' +str(cam.awb_gains) + ' Brightness: ' +str(cam.brightness) + ' Contrast: ' +str(cam.contrast) + ' EC: ' +str(cam.exposure_compensation))

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
  try:
      main()
  except KeyboardInterrupt:
      logMessage('Finishing')
      exit()
