from datetime import datetime
import json

def init():
    global recordtime, testmode, service
    global storePath, rootPath
    global stillSeconds
    global remoteHost, remoteShare, remoteSubfolder, remoteUser, remotePassword
    global plexServer, plexLibrary, plexToken, plexServerKey
    global slackToken, slackChannel, slackChannel2, slackVideo
    global botEmoji, botEmoji2, botUser, botUser2
    global camRotation, camResolution, camStillResolution, camTitle 

    # Default record time, if motion is still detected this time is repeated
    recordtime = 20

    # Default to test mode, so I don't need to keep specifying when testing :-)
    # Switches off Slack
    testmode = True

    # Default to not a service. Will exit if service is running
    service = False

    # Where the code is stored
    rootPath = '/home/pi/Trailcam/'

    # Length of time into video a still should be taken. 0 = disable
    stillSeconds = 0

    # Folder on share to store content in
    remoteSubfolder = "Videos"

    # Camera rotation, 180 for inverted camera
    camRotation = 0

    # Camera resolution
    camResolution = (1640, 1232)
    camStillResolution = (3280, 2464)

    # Camera annotation title
    camTitle = 'Hog Cam'
    
    # Bot Emojis
    botEmoji = ':hedgehog:'
    botEmoji2 = ':dragon:'

    # Bot Emojis
    botUser = 'Hog Cam'
    botUser2 = 'Pi Control'

    # Post video to slack
    slackVideo = False

    # Load JSON config
    with open(rootPath + 'config/config.json', 'r') as f:
        config = json.load(f)

    # Host to mount share from
    remoteHost = config['remoteHost']

    # Share to mount on remote host
    remoteShare = config['remoteShare']
    
    # User to connect to remote share with
    remoteUser = config['remoteUser']

    # Password for user
    remotePassword = config['remotePassword']

    # Plex server url
    plexServer = config['plexServer']

    # Plex library ID
    plexLibrary = config['plexLibrary']

    # Plex token
    plexToken = config['plexToken']

    # Plex server key
    plexServerKey = config['plexServerKey']

    # Slack token for bot
    slackToken = config['slackToken'] 

    # Slack channel to post to
    slackChannel = config['slackChannel']

    # Slack channel to receive from
    slackChannel2 = config['slackChannel2']

    # Where to store the output to
    storePath = '/mnt/' + remoteHost + '/'

