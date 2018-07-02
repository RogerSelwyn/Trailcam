from slackclient import SlackClient
import time
import settings
from utilities import setupSlack

from botutilities import (
    stopService, startService, shutdownPi, invalidMessage, takeStill
)
import utilities

# Process the individual chat message. 
# If it is a proper message and not the bot replying, then process it 
def processChat(chat):
  if chat['type'] == 'message' and not chat.get('subtype') == 'bot_message' and not chat.get('subtype') == 'message_replied' and not chat.get('subtype') == 'file_share':
    processMessage(chat['text'], chat['ts'])

# Figure out what action to take based on the input command and available functions
def processMessage(message, threadid):
  switcher = {
    'stop': stopService,
    'start': startService,
    'shutdown': shutdownPi,
    'still': takeStill
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

