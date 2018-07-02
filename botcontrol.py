from slackclient import SlackClient
import time, os, subprocess
import settings
from utilities import (
    setupSlack, postSlackMessage
)
import utilities

# Process the individual chat message. 
# If it is a proper message and not the bot replying, then process it 
def processChat(chat):
  if chat['type'] == 'message' and not chat.get('subtype') == 'bot_message' and not chat.get('subtype') == 'message_replied':
    processMessage(chat['text'], chat['ts'])

# Stop the trailcam service and post a message on outcome to Slack
def stopService(threadid):
  print('Stopping trailcam service')
  os.system("sudo service trailcam stop")    
  try:
      output = subprocess.check_output(['service', 'trailcam', 'status'])
  except:
      postSlackMessage(':white_check_mark: Service is stopped', threadid, ':ghost:', 'Cam Control')
  else:
      postSlackMessage(':no_entry: Service still running', threadid, ':ghost:', 'Cam Control')
  return

# Start the trailcam service and post a message on outcome to Slack
def startService(threadid):
  print('Starting trailcam service')
  os.system("sudo service trailcam start")
  try:
      output = subprocess.check_output(['service', 'trailcam', 'status'])
  except:
      postSlackMessage(':no_entry: Service is stopped', threadid, ':ghost:', 'Cam Control')
  else:
      postSlackMessage(':white_check_mark: Service is started', threadid, ':ghost:', 'Cam Control')
  return

# Shutdown the Pi
def shutdownPi(threadid):
  print('Pi shutting down')
  postSlackMessage(':white_check_mark: Pi shutting down', threadid, ':ghost:', 'Cam Control')
  subprocess.call(["sudo", "shutdown", "-h", "now"])
  return

# Tell slack it send a bad message
def invalidMessage(threadid):
  postSlackMessage(':no_entry: Invalid command', threadid, ':ghost:', 'Cam Control')
  return

# Figure out what action to take based on the input command and available functions
def processMessage(message, threadid):
  switcher = {
    'stop': stopService,
    'start': startService,
    'shutdown': shutdownPi,
  }
  func = switcher.get(message.lower())
  if func is None:
    invalidMessage(threadid)
  else:
    func(threadid)
  return

# main process
def main():
  # Setup settings
  settings.init()

  # Setup slack
  setupSlack(settings.slackChannel2)

  # If we connected to slack, then process messages. If there is no message, sleep for 10 seconds
  if utilities.sc.rtm_connect():
    while utilities.sc.server.connected is True:
        chat = utilities.sc.rtm_read()
        if len(chat) == 0:
            time.sleep(10)
        else:
            processChat(chat[0])

# Initiate the main process
if __name__== "__main__":
  try:
      main()
  except KeyboardInterrupt:
      print('Finishing')
      exit()

