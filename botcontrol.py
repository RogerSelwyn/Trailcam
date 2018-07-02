from slackclient import SlackClient
import time, os, subprocess
import settings
from utilities import (
    setupSlack, postSlackMessage
)
import utilities

def processChat(chat):
  if chat['type'] == 'message' and not chat.get('subtype') == 'bot_message' and not chat.get('subtype') == 'message_replied':
    processMessage(chat['text'], chat['ts'])

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

def shutdownPi(threadid):
  print('Pi shutting down')
  postSlackMessage(':white_check_mark: Pi shutting down', threadid, ':ghost:', 'Cam Control')
  subprocess.call(["sudo", "shutdown", "-h", "now"])
  return

def invalidMessage(threadid):
  postSlackMessage(':no_entry: Invalid command', threadid, ':ghost:', 'Cam Control')
  return

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

def main():
  settings.init()
  setupSlack(settings.slackChannel2)
  if utilities.sc.rtm_connect():
    while utilities.sc.server.connected is True:
        chat = utilities.sc.rtm_read()
        if len(chat) == 0:
            time.sleep(10)
        else:
            processChat(chat[0])


if __name__== "__main__":
  try:
      main()
  except KeyboardInterrupt:
      print('Finishing')
      exit()

