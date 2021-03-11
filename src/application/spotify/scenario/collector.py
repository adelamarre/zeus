
import os
from datetime import datetime
from multiprocessing import synchronize
from src.application.collectors import StatsCollector
from src.application.spotify.scenario.config.collector import CollectorConfig
from src.application.scenario import AbstractScenario
from src.services.console import Console
from src.services.aws import RemoteQueue

class Scenario(AbstractScenario):
    def __init__(self, args, userDir: str, shutdownEvent: synchronize.Event):
        super().__init__(args, userDir, shutdownEvent)

    def start(self):
        logDir = None
        logfile = None
        
        if self.args.nolog == False:
            logDir = self.userDir + '/collector/' + datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
            logfile = logDir + '/session.log'
            os.makedirs(logDir, exist_ok=True)

        verbose = 3 if self.args.verbose else 1
        console = Console(verbose=verbose, ouput=True, logfile=logfile, logToFile=not self.args.nolog)
        console.log('Start scenario Spotify Collector')
        
        config = CollectorConfig(self.userDir + '/config.ini').getConfig()

        remoteQueue = RemoteQueue(config[CollectorConfig.COLLECTOR_SQS_ENDPOINT])
        statsCollector = StatsCollector(userDir=self.userDir, console=console)

        while True:
            try:
                remoteQueue.provision(10)
                while remoteQueue.hasMessage():
                    message = remoteQueue.pop()
                    statsCollector.collect(message)
                    remoteQueue.deleteMessage(message)
                if self.shutdownEvent.is_set():
                    break
            except:
                console.exception()
                pass

        