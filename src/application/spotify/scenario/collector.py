
import os
from datetime import datetime
from multiprocessing import synchronize
from src.application.scenario import AbstractScenario
from src.services.console import Console

class Scenario(AbstractScenario):
    def __init__(self, args, userDir: str, shutdownEvent: synchronize.Event):
        super().__init__(args, userDir, shutdownEvent)

    def start(self):
        logDir = None
        screenshotDir = None
        logfile = None
        
        if self.args.nolog == False:
            logDir = self.userDir + '/collector/' + datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
            logfile = logDir + '/session.log'
            os.makedirs(logDir, exist_ok=True)
            #if self.args.screenshot:
            #    screenshotDir = logDir + '/screenshot'
            #    os.makedirs(screenshotDir, exist_ok=True)

        verbose = 3 if self.args.verbose else 1
        console = Console(verbose=verbose, ouput=self.args.verbose, logfile=logfile, logToFile=not self.args.nolog)
        console.log('Start scenario Spotify Collector')
        