from slackclient import SlackClient
import settings, time

def setupSlack():
    global rog_cam_id, sc
    rog_cam_id = None

    sc = SlackClient(settings.slackToken)
    if sc.rtm_connect():
      while sc.server.connected is True:
          print(sc.rtm_read())
          time.sleep(1)
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
        print("Slack Post EXCEPTION: " + str(ret))
        return
    else:
        print('Slack notified - ' + message)
        return ret['message']['ts']

settings.init()
setupSlack()
# threadid = postSlackMessage('Test')
