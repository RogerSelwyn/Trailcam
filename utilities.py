import subprocess, os, logging, sys, getopt, http.client, io
from shutil import copyfile
from datetime import datetime
from subprocess import call, Popen
from slackclient import SlackClient
import settings

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

def logMessage(message):
    logging.info(message)
    print(message)
    return

def logError(message):
    logging.error(message)
    print(message)
    if not settings.testmode:
        postSlackMessage(message)
    return

def storeVideo(input_video, output_basefilename):
    output_filename = "{}.mp4".format(output_basefilename)
    output_video = findStoreFileName(output_filename)
    logMessage('Saving video to ' + output_video)

    call(["MP4Box", "-add", input_video, output_video], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_video, output_filename

def storeStill(input_still, output_basefilename):
    output_filename = "{}.jpg".format(output_basefilename)
    output_still = findStoreFileName(output_filename)
    logMessage('Saving still to ' + output_still)
    copyfile(input_still, output_still)
    return output_still, output_filename

def processArgs():
    argv = sys.argv[1:] 


    try:
        opts, args = getopt.getopt(argv,"hr:t:s:",["recordtime=", "testmode=", "service="])
    except getopt.GetoptError:
        print('trailcam.py -r <recordtime> -t <testmode> -s <service>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('trailcam.py -r <recordtime> -s <service>')
            sys.exit()
        elif opt in ("-r", "--recordtime"):
            settings.recordtime = int(arg)
        elif opt in ("-t", "--testmode"):
            if arg == 'True':
                settings.testmode = True
            else:
                settings.testmode = False
        elif opt in ("-s", "--service"):
            settings.service = arg

    return

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

def updatePlex():
    conn =http.client.HTTPConnection(settings.plexServer)
    conn.request("GET", "/library/sections/" + settings.plexLibrary + "/refresh?X-Plex-Token=" + settings.plexToken)
    resp = conn.getresponse()
    if resp.reason != 'OK':
        logError('Plex Update EXCEPTION: ' + str(resp.status) + ' Reason: ' + resp.reason)
    else:
        logMessage('Updated Plex')
    return

def setupSlack():
    global rog_cam_id, sc
    rog_cam_id = None

    sc = SlackClient(settings.slackToken)
    rog_cam_id = sc.api_call("auth.test")["user_id"]
    return

def postSlackMessage(message, threadid = None):
    ret = sc.api_call(
      "chat.postMessage",
      channel=settings.slackChannel,
      thread_ts=threadid,
      text=message
    )
    if not 'ok' in ret or not ret['ok']:
        logError("Slack Post EXCEPTION: " + str(ret))
        return
    else:
        logMessage('Slack notified - ' + message)
        return ret['message']['ts']


def postSlackVideo(input_video, input_filename, input_title, input_comment):
  with open(input_video, 'rb') as f:
    ret = sc.api_call(
        "files.upload",
        channels=settings.slackChannel,
        filename=input_filename,
        title=input_title,
        file=io.BytesIO(f.read())
    )
    if not 'ok' in ret or not ret['ok']:
        logError("Slack Post EXCEPTION: " + str(ret))
    else:
        logMessage('Slack video uploaded - ' + input_filename)
    return

def checkService():
    try:
        output = subprocess.check_output(['service', 'trailcam', 'status'])
    except:
        return False
    else:
        logMessage('Service running - exiting ')
        return True
