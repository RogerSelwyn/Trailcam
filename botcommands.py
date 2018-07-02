from slackclient import SlackClient
import os, subprocess, picamera, io
from datetime import datetime
from utilities import postSlackMessage, checkService
import settings
import utilities


# Stop the trailcam service and post a message on outcome to Slack
def stopService(threadid):
  print('Stopping trailcam service')
  os.system("sudo service trailcam stop") 
  if checkService():
      postSlackMessage(':no_entry: Service still running', threadid, ':ghost:', 'Cam Control')
  else:
      postSlackMessage(':white_check_mark: Service is stopped', threadid, ':ghost:', 'Cam Control')
  return

# Start the trailcam service and post a message on outcome to Slack
def startService(threadid):
  print('Starting trailcam service')
  os.system("sudo service trailcam start") 
  if checkService():
      postSlackMessage(':white_check_mark: Service is started', threadid, ':ghost:', 'Cam Control')
  else:
      postSlackMessage(':no_entry: Service is stopped', threadid, ':ghost:', 'Cam Control')
  return

# Shutdown the Pi
def shutdownPi(threadid):
  print('Pi shutting down')
  postSlackMessage(':white_check_mark: Pi shutting down', threadid, ':ghost:', 'Cam Control')
  subprocess.call(["sudo", "shutdown", "-h", "now"])
  return

# Reboot the Pi
def rebootPi(threadid):
  print('Pi rebooting')
  postSlackMessage(':white_check_mark: Pi rebooting', threadid, ':ghost:', 'Cam Control')
  subprocess.call(["sudo", "reboot"])
  return

# take a still
def takeStill(threadid):
  print('Taking still')
  output_basefilename = "{}".format(datetime.now().strftime('%Y%m%d-%H%M%S'))
  recordStill = settings.rootPath + 'videos/' + output_basefilename + '.jpg'
  with picamera.PiCamera() as cam:
      cam.rotation=settings.camRotation
      cam.resolution=settings.camStillResolution
      cam.annotate_background = picamera.Color('black')
      cam.shutter_speed = 10000
      cam.capture(recordStill, use_video_port=False)
      postSlackStill(recordStill, output_basefilename + '.jpg', output_basefilename + '.jpg', "Still")
  os.remove(recordStill)
  return

# Tell slack it send a bad message
def invalidMessage(threadid, message):
  postSlackMessage(':no_entry: Invalid command - ' + message, threadid, ':ghost:', 'Cam Control')
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
        postSlackMessage(':no_entry: Still failed', threadid, ':ghost:', 'Cam Control')
    return



