from slackclient import SlackClient
import os, subprocess, picamera, io, time, threading
from datetime import datetime
from utilities import postSlackMessage, checkService, updatePlex
import settings
import utilities


# Stop the trailcam service and post a message on outcome to Slack
def stopService(threadid):
  print('Stopping trailcam service')
  os.system("sudo service trailcam stop") 
  if checkService():
      postMessage(':no_entry: Service still running', threadid)
  else:
      postMessage(':white_check_mark: Service is stopped', threadid)
  return

# Start the trailcam service and post a message on outcome to Slack
def startService(threadid):
  print('Starting trailcam service')
  os.system("sudo service trailcam start") 
  if checkService():
      postMessage(':white_check_mark: Service is started', threadid)
  else:
      postMessage(':no_entry: Service is stopped', threadid)
  return

def updatePlexCommand(threadid):
  updatePlex()
  postMessage(':white_check_mark: Updating Plex', threadid)
  return


# Shutdown the Pi
def shutdownPi(threadid):
  print('Pi shutting down')
  postMessage(':white_check_mark: Pi shutting down', threadid)
  thread = threading.Thread(target=threadedCommand, args=(["sudo", "shutdown", "-h", "now"],))
  thread.daemon = True
  thread.start()
  return

# Reboot the Pi
def rebootPi(threadid):
  print('Pi rebooting')
  postMessage(':white_check_mark: Pi rebooting', threadid)
  thread = threading.Thread(target=threadedCommand, args=(["sudo", "reboot"],))
  thread.daemon = True
  thread.start()
  return

# Move to separate thread to try and get the service shutdown status message being shown
def threadedCommand(piCommand):
  subprocess.call(piCommand)
  return
 

# Take a still - Set camera parameters, start the camera, wait for 2 seconds, take still, stop the camera, post to slack
def takeStill(threadid):
  print('Taking still')
  postMessage(':white_check_mark: Taking still', threadid)
  output_basefilename = "{}".format(datetime.now().strftime('%Y%m%d-%H%M%S'))
  recordStill = settings.rootPath + 'videos/' + output_basefilename + '.jpg'
  with picamera.PiCamera() as cam:
      cam.rotation=settings.camRotation
      cam.resolution=settings.camStillResolution
      cam.annotate_background = picamera.Color('black')
      cam.shutter_speed = 10000
      cam.start_preview()
      time.sleep(2)
      cam.capture(recordStill, use_video_port=False)
      cam.stop_preview()
  postSlackStill(recordStill, output_basefilename + '.jpg', output_basefilename + '.jpg', "Still")
  os.remove(recordStill)
  return

# Tell slack it send a bad message
def invalidMessage(threadid, message):
  postMessage(':no_entry: Invalid command - ^' + message + '^', threadid)
  return

# Posts the still to slack
def postSlackStill(input_still, input_filename, input_title, input_comment):
  with open(input_still, 'rb') as f:
    ret = utilities.sc.api_call(
        "files.upload",
        channels=settings.slackChannel2,
        filename=input_filename,
        initial_comment=input_comment,
        title=input_title,
        file=io.BytesIO(f.read())
    )
    if not 'ok' in ret or not ret['ok']:
        postSlackMessage(':no_entry: Still failed', threadid, settings.botEmoji2, settings.botUser2)
    return

def powerReduce(threadid):
  postMessage(':white_check_mark: Power consumption reducing', threadid)
  powerChange(0, 'up')
  postMessage(':white_check_mark: Power consumption reduced', threadid)
  setupSlack(settings.slackChannel2)
  return

def powerIncrease(threadid):
  postMessage(':white_check_mark: Power consumption increasing', threadid)
  powerChange(1, 'down')
  postMessage(':white_check_mark: Power consumption increased', threadid)
  setupSlack(settings.slackChannel2)
  return

# Post slack message, with correct emoji and user
def postMessage(message, threadid = None):
  postSlackMessage(message, threadid, settings.botEmoji2, settings.botUser2)
  return

# Reduce power consumption
def powerChange(onOff, upDown):
  os.system("echo " + str(onOff) + " | sudo tee /sys/devices/platform/soc/3f980000.usb/buspower >/dev/null") 
  # os.system("sudo tvservice --off") 
  os.system("sudo ifconfig wlan0 " + upDown)
  time.sleep(5)
  return

