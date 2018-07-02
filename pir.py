from datetime import datetime
import picamera, time
from gpiozero import MotionSensor

pir = MotionSensor(18)
print('{} Settle'.format(datetime.now().strftime('%H:%M:%S:%f')))
time.sleep(10)
print('{} Start'.format(datetime.now().strftime('%H:%M:%S:%f')))

while True:
    pir.wait_for_motion()
    print('{} Motion'.format(datetime.now().strftime('%H:%M:%S.%f')))
    pir.wait_for_no_motion()
    print('{} No Motion'.format(datetime.now().strftime('%H:%M:%S.%f')))
