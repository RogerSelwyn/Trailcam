from slackclient import SlackClient
import time
import settings

import botcommands as bc
import utilities as util 

# Process the individual chat message. 
# If it is a proper message and not a message subtype, then process it 
def processChat(chat):
  if (
    chat['type'] == 'message' and 
    'subtype' not in chat and 
    'upload' not in chat
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
  
  # Setup settings
  settings.init()

  # Wait for network to come up
  util.waitForNetUp(settings.botUser2)

  # Setup slack
  util.setupSlack(settings.slackChannel2)

  # Send message saying we are up and running
  bc.postMessage(':snowflake: ' + settings.botUser2 + ' is up', None)

  # If we connected to slack, then process messages. If there is no message, sleep for 10 seconds
  if util.sc.rtm_connect():
    while util.sc.server.connected is True:
        chat = util.sc.rtm_read()
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

