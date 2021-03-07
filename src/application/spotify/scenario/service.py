#!/usr/bin/python3.8
import os
import signal
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

        config = ConfigParser()
        config.read(self.userDir + '/config.service.ini')

        ACCOUNT_SQS_ENDPOINT = None
        COLLECTOR_SQS_ENDPOINT = None
        MAX_PROCESS     = cpu_count()
        SPAWN_INTERVAL  = 0.5
        SERVER_ID = None
        SECRET = None

        if 'LISTENER' in config.sections():
            listenerConfig          = config['LISTENER']
            SERVER_ID               = listenerConfig.get(Config.SERVER_ID, None)
            ACCOUNT_SQS_ENDPOINT    = listenerConfig.get(Config.ACCOUNT_SQS_ENDPOINT, None)
            COLLECTOR_SQS_ENDPOINT  = listenerConfig.get(Config.COLLECTOR_SQS_ENDPOINT, None)
            MAX_PROCESS             = listenerConfig.getint(Config.MAX_PROCESS, MAX_PROCESS)
            SPAWN_INTERVAL          = listenerConfig.getfloat(Config.SPAWN_INTERVAL, SPAWN_INTERVAL)
            SECRET                  = listenerConfig.get(Config.SECRET).strip()
        
        if ACCOUNT_SQS_ENDPOINT is None:
            sys.exit('you need to set the account_sqs_endpoint in the config file.')
        
        if COLLECTOR_SQS_ENDPOINT is None:
            sys.exit('you need to set the collector_sqs_endpoint in the config file.')
        
        if SERVER_ID is None:
            sys.exit('you need to set the server_id in the config file.')
        
        if SECRET is None:
            sys.exit('you need to set the stats server password.')

        
    
        pp = SpotifyListenerProcessProvider(
            appArgs=self.args,
            accountRemoteQueue=RemoteQueue(ACCOUNT_SQS_ENDPOINT),
            statsCollector=StatsCollector(COLLECTOR_SQS_ENDPOINT, 'spotify', SERVER_ID),
            shutdownEvent=self.shutdownEvent,
            console=console,
            headless= False,
            vnc= self.args.vnc or (MAX_PROCESS == 1),
            screenshotDir=screenshotDir
        )

        pm = ProcessManager(
            serverId=SERVER_ID,
            userDir=self.userDir,
            console=console,
            processProvider=pp,
            maxProcess=MAX_PROCESS,
            spawnInterval=SPAWN_INTERVAL,
            showInfo=not self.args.noinfo,
            shutdownEvent=self.shutdownEvent,
            stopWhenNoProcess=False
        )

        #Start Statistics HTTP server
        systemStats = Stats()
        statsServer = HttpStatsServer(apiKey=SECRET, console=console, userDir=self.userDir, statsProviders=[systemStats, pp, pm])
        statsServer.start()
        
        #Start Process manager
        pm.start()
        
        # Stop Statistics HTTP server
        statsServer.stop()
