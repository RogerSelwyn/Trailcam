# Trailcam

Trailcam built on Raspberry Pi 3 Model B and Pi NoIR Camera V2

## Overview

Configure setup in settings.py, plus any secure configuration in config/config.json

Initiate using:

```python3 trailcam.py -t <testmode> -s <service>```

Currently setup to default to testmode=True so I don't have to keep entering -t True when testing. Also setup to service=False, since I also run this as a service.

The code checks to see if it is already running as a service, and exits if it is. Comes of developing on the same platform as I'm operating on and me forgetting to stop the service when testing. My service is setup like this:

```
[Unit]
Description=Trailcam
After=multi-user.target

[Service]
Type=idle
ExecStart=/usr/bin/python3 /home/pi/Trailcam/trailcam.py -t False -s True > /home/pi/Trailcam/log.txt
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
```

## Integration
Integrates with Plex and Slack
* **Plex** - Uploads video and still to my NAS which my Plex media server is pointing at, then initiates a library refresh for the specific library
* **Slack** - Posts a notification on motion detected, and the video to my slack channel. Therefore you need 'slackclient' installed ```pip3 install slackclient```

## Hardware
* Raspberry Pi 3 Model B
* Pi NoIR Camera V2
* wittyPi Mini (Real Time Clock and power management/scheduling)
* Adafruit PIR (motion) sensor
* BW 48 LED Illuminator Light Lamp CCTV IR Infrared Night Vision
* Naturebytes Cam Case
* Anker PowerCore II 10000

## Credits
Major credits to Chris Johnstone for documenting out how to do the basic setup, from which I have then extended to meet my own needs:
* From 2016 - [https://peaknature.co.uk/blog/how-to-build-a-raspberry-pi-trail-cam--part-1-introduction]
* From 2018 - [https://peaknature.co.uk/blog/how-to-build-a-raspberry-pi-zero-trail-camera--part-1-what-you-need]

Also Naturebytes for their work on developing a full trail camera kit and making the case available as a seperate purchase:
* https://shop.naturebytes.org/product/wildlife-cam-case/
