import logging
import os
from datetime import datetime


class Bat_Log:
    def __init__(self, rootPath):
        self.rootPath = rootPath
        self.logPath = self.rootPath + "batcam_log"
        self.videoPath = self.rootPath + "videos"

        if not os.path.exists(self.logPath):
            os.makedirs(self.logPath)

        if not os.path.exists(self.videoPath):
            os.makedirs(self.videoPath)

        logfile = self.logPath + "/batcam_log-" + str(datetime.now().strftime("%Y%m%d-%H%M")) + ".csv"
        logging.basicConfig(
            filename=logfile,
            level=logging.INFO,
            format="%(asctime)s %(levelname)s, %(message)s",
            datefmt="%Y-%m-%d, %H:%M:%S,",
        )
        return

    def logMessage(self, message):
        # Logs a message to the log file, and prints it to console
        pidMessage = message
        logging.info(pidMessage)
        print(message)
        return
