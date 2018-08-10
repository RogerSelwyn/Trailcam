import subprocess, os, logging, sys, getopt, http.client, io, threading, time, urllib, requests
from shutil import copyfile
from datetime import datetime
from subprocess import call, Popen
from slackclient import SlackClient
import settings

global storeThread
storeThread = False 

# Mounts share from local SMB location
# Creates the mount point if needed
# Then mounts the share to it in RW mode
def mountShare():
    if not os.path.exists(settings.storePath):
        logMessage('Creating mount point ' + settings.storePath)
        command = "sudo mkdir " + settings.storePath
        Popen(command, shell=True)
    if not os.path.ismount(settings.storePath):
        logMessage('Mounting share //' + settings.remoteHost + '/' + settings.remoteShare)
        command = "sudo mount -t cifs -o"
        command = command + " username=" + settings.remoteUser 
        command = command + ",password=" + settings.remotePassword
        command = command + ",rw,uid=pi,gid=pi"
        command = command + "  '//" + settings.remoteHost + "/" + settings.remoteShare + "'"
        command = command + " " + settings.storePath
        Popen(command, shell=True)
    return

# Sets up log file location, and setups the basic config
def setupLog():
    if not os.path.exists(settings.rootPath + 'trailcam_log'):
        os.makedirs(settings.rootPath + 'trailcam_log')

    if not os.path.exists(settings.rootPath + 'videos'):
        os.makedirs(settings.rootPath + 'videos')

    logfile = settings.rootPath + "trailcam_log/trailcam_log-"+str(datetime.now().strftime("%Y%m%d-%H%M"))+".csv"
    logging.basicConfig(filename=logfile, level=logging.INFO,
        format='%(asctime)s %(levelname)s, %(message)s',
        datefmt='%Y-%m-%d, %H:%M:%S,')
    return

# Logs a message to the log file, and prints it to console
def logMessage(message):
    pidMessage = str(os.getpid()) + ', ' + str(threading.currentThread().ident) + ', ' + message
    logging.info(pidMessage)
    print(message)
    return

# Logs an error message, prints it to console and notifies slack if not in test mode
def logError(message):
    logging.error(message)
    print(message)
    if not settings.testmode:
        postSlackMessage(message, None, settings.botEmoji, settings.botUser)
    return

# Run thread conversion and storage in separate thread
# Only run thread if not already running
def storeVideo():
    global storeThread
    if not storeThread:
        storeThread = True
        thread = threading.Thread(target=threadedStoreVideos)
        thread.daemon = True
        thread.start()
    return

# Run video storage against each file in directory until empty
def threadedStoreVideos():
    global storeThread
    logMessage('Subprocess started')
    folder = settings.rootPath + "videos/"
    while len([name for name in sorted(os.listdir(folder)) if name.endswith(".h264")]) > 0:
        for the_file in os.listdir(folder):
          if the_file.endswith(".h264"):
              file_path = os.path.join(folder, the_file)
              try:
                  if os.path.isfile(file_path):
                      storeIndividualVideo(file_path, the_file[:-5])
              except Exception as e:
                  logMessage(str(e))
    storeThread = False
    logMessage('Subprocess stopped')
    return

# Convert video to MP4 and store in final location
# Remove capture file
# Post to slack if not in test mode
# Tell Plex to update the library
def storeIndividualVideo(input_video, output_basefilename):
    output_filename = "{}.mp4".format(output_basefilename)
    output_video = findStoreFileName(output_filename)
    logMessage('Saving video to ' + output_video)
    call(["MP4Box", "-add", input_video, output_video], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(input_video)
    updatePlex()
    if not settings.testmode and settings.slackVideo:
        postSlackVideo(output_video, output_filename, output_filename, "Hedgehog")
    elif not settings.testmode:
        ratingKey = plex_ratingKey(output_basefilename)
        if ratingKey == None:
            postSlackMessage('Video uploaded to Plex - ' + output_filename + ' - URL not found', None, settings.botEmoji, settings.botUser)
        else:
            plexURL = 'plex://play/?metadataKey=%2Flibrary%2Fmetadata%2F' + ratingKey + '&metadataType=1&server=' + settings.plexServerKey
            postSlackMessage('Video uploaded to Plex - <' + plexURL + '|' + output_filename + '>', None, settings.botEmoji, settings.botUser)
    return

# Store still in final location
# Remove capture file
def storeStill(input_still, output_basefilename):
    output_filename = "{}.jpg".format(output_basefilename)
    output_still = findStoreFileName(output_filename)
    logMessage('Saving still to ' + output_still)
    copyfile(input_still, output_still)
    os.remove(input_still)
    return 

# Process command line arguments
def processArgs():
    argv = sys.argv[1:] 
    try:
        opts, args = getopt.getopt(argv,"hr:t:s:p:",["recordtime=", "testmode=", "service=", "phototime="])
    except getopt.GetoptError:
        print('trailcam.py -r <recordtime> -t <testmode> -s <service> -p <phototime> ')
        sys.exit(2)
    for opt, arg in opts:
        # Help
        if opt == '-h':
            print('trailcam.py -r <recordtime> -s <service> -p <phototime>')
            sys.exit()
        # Set the time for which each recording will last
        elif opt in ("-r", "--recordtime"):
            settings.recordtime = int(arg)
        # Set if we are testing
        elif opt in ("-t", "--testmode"):
            if arg == 'True':
                settings.testmode = True
            else:
                settings.testmode = False
        # Set if this is being run as a service
        elif opt in ("-s", "--service"):
            if arg == 'True':
                settings.service = True
            else:
                settings.service = False
        # Set the point at which we should take a photo
        elif opt in ("-p", "--phototime"):
            settings.stillSeconds = int(arg)
    return

# Figure out where we want to store the output. Preferably on the share we mounted.
def findStoreFileName(output_filename):
    if os.path.isdir(settings.storePath + settings.remoteSubfolder):
        storePath = settings.storePath + settings.remoteSubfolder + "/"
    elif os.path.isdir('/media/pi/SD Card'):
        storePath = "/media/pi/SD Card/"
    elif os.path.isdir('/mnt/usb/videos'):
        storePath = "/mnt/usb/videos/"
    elif os.path.isdir('/mnt/usb1/videos'):
        storePath = "/mnt/usb1/videos/"
    elif os.path.isdir('/mnt/usb2/videos'):
        storePath = "/mnt/usb2/videos/"
    else:
        storePath = settings.rootPath + "videos/"
    storeFileName = storePath + output_filename
    return storeFileName

# Send REST call to update Plex
def updatePlex():
    conn =http.client.HTTPConnection(settings.plexServer)
    conn.request("GET", "/library/sections/" + settings.plexLibrary + "/refresh?X-Plex-Token=" + settings.plexToken)
    resp = conn.getresponse()
    if resp.reason != 'OK':
        logError('Plex Update EXCEPTION: ' + str(resp.status) + ' Reason: ' + resp.reason)
    else:
        logMessage('Updated Plex')
    return

# Setup slack communication
def setupSlack(inSC):
    global sc, slackChannel
    slackChannel = inSC

    sc = SlackClient(settings.slackToken)
    sc.api_call("auth.test")["user_id"]
    return

# Initiate threaded slack message post to run async
def postThreadedSlackMessage(message, threadid = None, iconemoji = None, user_name = None, overrideChannel = None):
  thread = threading.Thread(target=postSlackMessage, args=(message, threadid, iconemoji, user_name, overrideChannel))
  thread.daemon = True
  thread.start()
  return


# Send a slack message
# - threadid replies previous item
# - iconemoji overrides the default user icon
# - user_name overrides the default user name
def postSlackMessage(message, threadid = None, iconemoji = None, user_name = None, overrideChannel = None):
    outputChannel = slackChannel
    if not overrideChannel is None:
      outputChannel = overrideChannel
    try:
        ret = sc.api_call(
          "chat.postMessage",
          channel=outputChannel,
          thread_ts=threadid,
          icon_emoji=iconemoji,
          username=user_name,
          text=message
        )
    except Exception as e:
        logMessage(e)

    if not 'ok' in ret or not ret['ok']:
        logError("Slack Post EXCEPTION: " + str(ret))
        return
    else:
        logMessage('Slack notified - ' + message)
        return ret['message']['ts']

# Posts the video to slack
def postSlackVideo(input_video, input_filename, input_title, input_comment):
  with open(input_video, 'rb') as f:
    try:
        ret = sc.api_call(
            "files.upload",
            channels=settings.slackChannel,
            filename=input_filename,
            initial_comment=input_comment,
            title=input_title,
            file=io.BytesIO(f.read())
        )
    except Exception as e:
        logMessage(e)

    if not 'ok' in ret or not ret['ok']:
        logError("Slack Post EXCEPTION: " + str(ret))
    else:
        logMessage('Slack video uploaded - ' + input_filename)
    return

# Check to see if we are running as a service
def checkService():
    try:
        output = subprocess.check_output(['service', 'trailcam', 'status'])
    except:
        return False
    else:
        return True

# Tidy up our capture store
def tidyupTempStore():
  folder = settings.rootPath + "videos/"
  for the_file in os.listdir(folder):
    file_path = os.path.join(folder, the_file)
    try:
        if os.path.isfile(file_path):
            os.unlink(file_path)
        #elif os.path.isdir(file_path): shutil.rmtree(file_path)
    except Exception as e:
        logMessage(e)

# Check to see if connected to network
def is_online():
    '''
    Determine whether or not network is online
    by sending a HTTP GET request. If the network is
    online the function will return true. If the network
    is not online the function will return false
    '''

    timeout = 0.30
    url = 'http://www.google.com'

    try:
        print('Sending request to {}'.format(url))
        response = urllib.request.urlopen(url, timeout=timeout)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        # Generally using a catch-all is a bad practice but
        # I think it's ok in this case
        response = False
    if response:
        return True
    else:
        return False

# Get the Plex video ratingKey
def plex_ratingKey(video_title):
    url = 'http://' + settings.plexServer + '/library/sections/' + settings.plexLibrary + '/all?X-Plex-Token=' + settings.plexToken

    i = 0
    while i < 5:
        i += 1 
        time.sleep(2)
        response = requests.get(url, headers={"Accept":"application/json"})
        data = response.json()['MediaContainer']['Metadata']
        for video in data:
            if video['title'] == video_title:
                return video['ratingKey']
                break

# Wait for Network to come up
def waitForNetUp(botUser):
  netUp = False
  while not netUp:
      netUp = is_online()
      if not netUp:
          print('Net down - ' + botUser)
          time.sleep(1)
  print('Net up - ' + settings.botUser)
  return



