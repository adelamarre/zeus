
import os, sys, subprocess
from src.application.collectors import StatsCollector
from src.services.aws import RemoteQueue
from src.application.spotify.scenario.config.monitor import MonitorConfig
from src.application.scenario import AbstractScenario
from flask import Flask, g                                                        
from multiprocessing import Process
from time import sleep
from src.services.console import Console
from src.services.db import Db
from src.application.system.scenario.admininterface.app import makeAdminApp
import tornado

class Scenario(AbstractScenario):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        

    def start(self):
        logfile = self.userDir + '/session.log'
        configFile = self.userDir + '/config.ini' 
        verbose = 3 if self.args.verbose else 1
        console = Console(verbose=verbose, ouput=self.args.verbose, logfile=logfile, logToFile=not self.args.nolog)
        defautlConfig = {
            MonitorConfig.POLL_INTERVAL: 2.0
        }
        configData = MonitorConfig(configFile).getConfig(defautlConfig)
        #app.context = {
        #    'userDir': self.userDir,
        #    'console': console,
        #    'config': configData
        #}
        remoteQueue = RemoteQueue(configData[MonitorConfig.COLLECTOR_SQS_ENDPOINT])
        statsCollector = StatsCollector(userDir=self.userDir, console=console)

        app = makeAdminApp(userDir=self.userDir, console=console, config=configData)
        app.listen(5000)
        #tornado.ioloop.IOLoop.current().start()
        #sys.exit()
        p = Process(target=tornado.ioloop.IOLoop.current().start)
        p.start()
        while True:
            sleep(0.5)
            if not p.is_alive():
                p.join()
                p = Process(target=tornado.ioloop.IOLoop.current().start)
                p.start()
                break
            
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

            if self.shutdownEvent.is_set():
                p.kill()
                p.join()
                break


