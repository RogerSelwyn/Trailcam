from slackclient import SlackClient
import time
import settings
from utilities import setupSlack, is_online

import botcommands as bc
import utilities

# Process the individual chat message. 
# If it is a proper message and not a message subtype, then process it 
def processChat(chat):
  if (
    chat['type'] == 'message' and 
    'subtype' not in chat
  ):
    processMessage(chat['text'], chat['ts'])

# Figure out what action to take based on the input command and available functions
def processMessage(message, threadid):
  switcher = {
    'stop': bc.stopServiceCommand,
    'start': bc.startServiceCommand,
    'shutdown': bc.shutdownPiCommand,
    'reboot': bc.rebootPiCommand,
    'still': bc.takeStillCommand,
    'plex': bc.updatePlexCommand,
    'power up': bc.powerIncreaseCommand,
    'power down': bc.powerReduceCommand,
  }
  func = switcher.get(message.lower().strip())
  if func is None:
    bc.invalidCommand(threadid, message.lower())
  else:
    func(threadid)
  return

# main process
def main():
  # bc.powerChange(0, 'up')

  while not is_online():
      print('Net down.')
  print('Net up.')

  # Setup settings
  settings.init()

  # Setup slack
  setupSlack(settings.slackChannel2)

  # Send message saying we are up and running
  bc.postMessage(':snowflake: ' + settings.botUser2 + ' is up', None)

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
      bc.postMessage(':zap: ' + settings.botUser2 + ' is going down', None)
      print('Finishing')
      exit()

