#!/usr/bin/python3.8
import os
import signal
from src.application.spotify.scenario.config.listener import ListenerConfig
from src.services.config import Config
from src.application.statscollector import StatsCollector
from src.services.aws import RemoteQueue
import sys
from configparser import ConfigParser
from datetime import datetime
from getpass import getuser
from multiprocessing import Event
from time import sleep

import urllib3
from psutil import cpu_count
from src.application.spotify.scenario.listener import \
    ListenerProcessProvider as SpotifyListenerProcessProvider
from src.services.console import Console
from src.services.httpserver import HttpStatsServer
from src.services.processes import ProcessManager
from src.services.stats import Stats

urllib3.disable_warnings()
from src.application.scenario import AbstractScenario


class Scenario(AbstractScenario):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.configFile = self.userDir + '/config.service.ini' 
    
    def start(self):
        print('Start as user %s' % getuser())

        logDir = None
        screenshotDir = None
        logfile = None
        
        if self.args.nolog == False:
            logDir = self.userDir + '/service/' + datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
            logfile = logDir + '/session.log'
            os.makedirs(logDir, exist_ok=True)
            if self.args.screenshot:
                screenshotDir = logDir + '/screenshot'
                os.makedirs(screenshotDir, exist_ok=True)
        
        verbose = 3 if self.args.verbose else 1
        console = Console(verbose=verbose, ouput=self.args.verbose, logfile=logfile, logToFile=not self.args.nolog)
        configData = ListenerConfig(self.userDir + '/config.service.ini').getConfig()
        
        pp = SpotifyListenerProcessProvider(
            appArgs=self.args,
            accountRemoteQueue=RemoteQueue(configData[ListenerConfig.ACCOUNT_SQS_ENDPOINT]),
            statsCollector=StatsCollector(configData[ListenerConfig.COLLECTOR_SQS_ENDPOINT], 'spotify', configData[ListenerConfig.SERVER_ID]),
            shutdownEvent=self.shutdownEvent,
            console=console,
            headless= False,
            vnc= self.args.vnc or (configData[ListenerConfig.MAX_PROCESS] == 1),
            screenshotDir=screenshotDir
        )

        pm = ProcessManager(
            serverId=configData[ListenerConfig.SERVER_ID],
            userDir=self.userDir,
            console=console,
            processProvider=pp,
            maxProcess=configData[ListenerConfig.MAX_PROCESS],
            spawnInterval=configData[ListenerConfig.SPAWN_INTERVAL],
            showInfo=not self.args.noinfo,
            shutdownEvent=self.shutdownEvent,
            stopWhenNoProcess=False
        )

        #Start Statistics HTTP server
        systemStats = Stats()
        statsServer = HttpStatsServer(apiKey=configData[ListenerConfig.SECRET], console=console, userDir=self.userDir, statsProviders=[systemStats, pp, pm])
        statsServer.start()
        
        #Start Process manager
        pm.start()
        
        # Stop Statistics HTTP server
        statsServer.stop()
