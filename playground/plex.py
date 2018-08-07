from slackclient import SlackClient
import requests, json
import utilities, settings

if __name__ == '__main__':
    settings.init()
    utilities.setupSlack(settings.slackChannel2)

    url = 'http://' + settings.plexServer + '/library/sections/28/all?X-Plex-Token=' + settings.plexToken

    response = requests.get(url, headers={"Accept":"application/json"})

    data = response.json()['MediaContainer']['Metadata']

    for video in data:
        if video['title'] == '20180807-104301':
            print(video['ratingKey'])
            break

  
 