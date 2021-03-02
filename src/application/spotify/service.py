#!/usr/bin/python3.8
import os
import signal
import sys
from configparser import ConfigParser
from datetime import datetime
from getpass import getuser
from multiprocessing import Event
from time import sleep

import urllib3
from psutil import cpu_count
from src.application.spotify.listener import \
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
    
    def start(self):
        print('Start as user %s' % getuser())

        logDir = self.userDir + '/listener/' + datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
        screenshotDir = logDir + '/screenshot'
        
        if self.args.nolog == False:
            os.makedirs(logDir, exist_ok=True)
            os.makedirs(screenshotDir, exist_ok=True)

        config = ConfigParser()
        config.read(self.userDir + '/config.service.ini')


        SQS_ENDPOINT = None
        MAX_PROCESS     = cpu_count()
        SPAWN_INTERVAL  = 0.5
        #OVERRIDE_PLAYLIST = False

        if 'LISTENER' in config.sections():
            listenerConfig      = config['LISTENER']
            SERVER_ID           = listenerConfig.get('server_id', 'undefined').strip()
            SQS_ENDPOINT        = listenerConfig.get('sqs_endpoint').strip()
            MAX_PROCESS         = listenerConfig.getint('max_process', MAX_PROCESS)
            SPAWN_INTERVAL      = listenerConfig.getfloat('spawn_interval', SPAWN_INTERVAL)
            SECRET              = listenerConfig.get('secret').strip()
        
        if SQS_ENDPOINT is None:
            sys.exit('you need to set the sqs_endpoint in the config file.')
        
        if SECRET is None:
            sys.exit('you need to set the stats server password.')

        if self.args.verbose:
            verbose = 3
        else:
            verbose = 1

        console = Console(verbose=verbose, ouput=self.args.verbose, logfile=logDir + '/session.log', logToFile=not self.args.nolog)
        shuddownEvent = Event()

        pp = SpotifyListenerProcessProvider(
            queueEndPoint=SQS_ENDPOINT,
            shutdownEvent=shuddownEvent,
            console=console,
            #headless=args.headless,
            #vnc= args.vnc,
            screenshotDir=screenshotDir
            )

        pm = ProcessManager(
            serverId=SERVER_ID,
            userDir=self.userDir,
            console=console,
            processProvider=pp,
            maxProcess=MAX_PROCESS,
            spawnInterval=SPAWN_INTERVAL,
            showInfo=self.args.info,
            shutdownEvent=shuddownEvent,
        )

        def signalHandler(signum, frame):
            pm.stop()

        signal.signal(signal.SIGINT, signalHandler)
        signal.signal(signal.SIGTERM, signalHandler)

        
        systemStats = Stats()
        statsServer = HttpStatsServer(apiKey=SECRET, console=console, userDir=self.userDir, statsProviders=[systemStats, pp, pm])
        statsServer.start()
        
        if self.args.drymode:
            while not self.shutdownEvent.is_set():
                sleep(1)
        else:
            pm.start()

        statsServer.stop()
