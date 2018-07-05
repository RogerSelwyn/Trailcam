# Import all the things we need
from gpiozero import MotionSensor
from datetime import datetime
import picamera
import time
import os

# Import the various utility scripts and settings
import utilities as util 
from utilities import (
    logMessage, logError, 
)
import settings

# Main process
def main():
  # Load the settings
  settings.init()

  # Process the command line arguments
  util.processArgs()

  # If we aren't running as a service and the service is already running, we'll get a conflict, so quit
  if not settings.service and util.checkService():
      logMessage('Service running - exiting ')
      exit()

  # Setup the logging
  util.setupLog()

  # If we aren't running in test mode, then setup for Slack communication
  if not settings.testmode:
      util.setupSlack(settings.slackChannel)
      util.postSlackMessage(':snowflake: ' + settings.botUser + ' is up', None, settings.botEmoji, settings.botUser, settings.slackChannel2)
  # Mount the network share
  util.mountShare()

  # Tidy up the temporary capture store in case we left it in a mess
  util.tidyupTempStore()

  # PIR is on pin 18
  pir = MotionSensor(18)

  logMessage('Starting - Video seconds: ' + str(settings.recordtime) + '; Still seconds: ' + str(settings.stillSeconds) + '; Test mode: ' + str(settings.testmode) + '; Service: ' + str(settings.service))

  # Wait an initial duration to allow PIR to settle
  time.sleep(10)

  # Camera time !
  with picamera.PiCamera() as cam:
    # Set the camera up
    timeFM = '%H:%M:%S.%f'
    cam.rotation=settings.camRotation
    cam.resolution=settings.camResolution
    cam.annotate_background = picamera.Color('black')

    # Record when last motion detected
    global motionStart
    pir.when_motion = incrementTimer

    # Keep going for ever
    while True:
        logMessage('Waiting for motion')
        pir.wait_for_motion()
        # print("{} - Motion".format(datetime.now().strftime(timeFM)))
        logMessage('Motion detected recording for '+ str(settings.recordtime)+' seconds')

        # If not in test mode, send a slack alert - Potential hedgehog!
        if not settings.testmode:
            util.postThreadedSlackMessage('Hedgehog alert :hedgehog:', None, settings.botEmoji, settings.botUser)

        # Setup our filenames, so all capture files are consistently named
        output_basefilename = "{}".format(datetime.now().strftime('%Y%m%d-%H%M%S'))
        recordVideo = settings.rootPath + 'videos/' + output_basefilename + '.h264'
        recordStill = settings.rootPath + 'videos/' + output_basefilename + '.jpg'


        # Start recording
        cam.start_recording(recordVideo + '.tmp', format='h264')

        # Start the overall timer
        start_time = datetime.now()
          
        # Set status
        start_record = True
        still_captured = False

        # Make sure timer is set
        motionStart = datetime.now()

        # Keep recording while there is still motion
        while pir.motion_detected:
            # If not first time around, put out a message
            if start_record:
                start_record = False
            else:
                print('Still recording for '+ str(settings.recordtime)+' seconds')

            # Set the timer for this cycle
            start = datetime.now()
      
            # Keep recording for the specified time period
            while (datetime.now() - start).seconds < settings.recordtime:
                # Update the text on the clip every 0.2 seconds
                cam.annotate_text = "Rog Cam "+datetime.now().strftime('%d-%m-%y %H:%M:%S')
                cam.wait_recording(0.2)

                # If we are meant to be capturing a still, check to see if we need to do it now
                if (datetime.now() - start_time).seconds > settings.stillSeconds and not still_captured and settings.stillSeconds > 0:

                    # The various stillMessage() in here are part of some debugging around auto-wide balance, because taking a still upsets it
                    still_captured = True
                    stillMessage(cam, '1')

                    # Store the current AWB
                    storeAWB = cam.awb_gains
                    print(storeAWB)
  
                    # Set the shutter speed to 1/100
                    cam.shutter_speed = 10000
                    stillMessage(cam, '2')
                    
                    # Take the picture on the Still Port
                    cam.capture(recordStill, use_video_port=False)
                    stillMessage(cam, '3')

                    # Set the shutter speed back to auto
                    cam.shutter_speed = 0

                    # Try to set the AWB back to what it was before
                    cam.awb_mode = 'off'
                    cam.awb_gains = storeAWB
                    stillMessage(cam, '4')
                    logMessage('Still captured')
                    util.storeStill(recordStill, output_basefilename)


        # Capture the total recording time
        total_time = (datetime.now() - start_time).seconds

        # Stop recording
        cam.stop_recording()

        logMessage('Stopped recording after ' + str(total_time) + ' seconds')

        # Go to sleep to let everything settle
        time.sleep(5)

        # Rename file
        os.rename(recordVideo + '.tmp', recordVideo)

        # Store the video to NAS, update Plex and post to Slack
        util.storeVideo()
  return


def stillMessage(cam, stillId):
  logMessage(stillId + ' - ' + 'Exposure Speed: ' + str(cam.exposure_speed) + ' Shutter Speed: ' + str(cam.shutter_speed) + ' ISO: ' +str(cam.iso) + ' AG: ' +str(cam.analog_gain) + ' DG: ' +str(cam.digital_gain) + ' AWB: ' +str(cam.awb_gains) + ' Brightness: ' +str(cam.brightness) + ' Contrast: ' +str(cam.contrast) + ' EC: ' +str(cam.exposure_compensation))

# Set the time last motion was seen
def incrementTimer():
    logMessage('Motion event')
    global motionStart
    motionStart = datetime.now()
    return
    


# Initiate everything
if __name__== "__main__":
  try:
      main()
  except KeyboardInterrupt:
      if not settings.testmode:
          util.postSlackMessage(':zap: ' + settings.botUser + ' is going down', None, settings.botEmoji, settings.botUser, settings.slackChannel2)
      logMessage('Finishing')
      exit()
