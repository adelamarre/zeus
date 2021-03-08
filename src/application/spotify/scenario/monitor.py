
from src.application.spotify.scenario.config.monitor import MonitorConfig
from src.application.spotify.scenario.listener import ListenerRemoteStat, ListenerStat
import sys
from src.application.scenario import AbstractScenario
from src import VERSION
from src.services.aws import RemoteQueue, RemoteQueueStats
from src.services.config import Config
from json import loads, dumps
from datetime import datetime
from colorama import Fore
from src import VERSION
from psutil import cpu_count
from src.services.terminal import Terminal
from time import time, sleep
from requests import get

class RemoteStats:
    def __init__(self, jsonData) -> None:
        self.__dict__ = loads(jsonData)



class Scenario(AbstractScenario):
    GLOBAL = 'global'
    SERVERS = 'servers'
    QUEUE = 'queue'

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.statistics = {}
        self.configFile = self.userDir + '/config.ini' 
    
    def fetchStats(self):
        self.statistics = {
            Scenario.GLOBAL: {
                ListenerRemoteStat.LOGGING_IN: 0,
                ListenerRemoteStat.PLAYING: 0,
                ListenerRemoteStat.PLAYED: 0,
                ListenerRemoteStat.ERROR: 0,
            },
            Scenario.QUEUE: {
                RemoteQueueStats.MESSAGE_COUNT: 0,
                RemoteQueueStats.USED_MESSAGE_COUNT: 0,
                RemoteQueueStats.ERROR_MESSAGE: None
            },
            Scenario.SERVERS: []
        }
        
        self.statistics[Scenario.QUEUE] = self.remoteQueue.getStats()
            
        serversStats = self.statistics[Scenario.SERVERS]
        globalStats = self.statistics[Scenario.GLOBAL]

        for server in self.servers:
            
            try:
                host = server.strip()
                serverStat = loads(get('https://%s:63443/?k=%s' % (host, self.config['secret']), verify=False).text)
                serverStat['host'] = host
                for key in globalStats:
                    globalStats[key] += serverStat['runner'][key]

                serversStats.append(serverStat)

            except Exception as e:
                self.statistics['servers'].append({
                    'host': host,
                    'exception': e
                })

    def refreshAll(self):
        terminal = self.terminal
        self.fetchStats()

        queueStats = self.statistics[Scenario.QUEUE]
        serversStats = self.statistics[Scenario.SERVERS]
        globalStats = self.statistics[Scenario.GLOBAL]


        terminal.newPage()
        terminal.append(Fore.RED + 'Venom Monitor v%s' % VERSION)
        terminal.appendSeparator()

        terminal.append('Servers:    ')
        if globalStats[ListenerRemoteStat.PLAYED]:
            globalStats['errorPercent'] =  (globalStats[ListenerRemoteStat.ERROR] / globalStats[ListenerRemoteStat.PLAYED]) * 100
        else:
            globalStats['errorPercent'] = 0.0
        terminal.appendTemplate('\tLoging: {loggingIn:4d}   Playing: {playing:4d}   Played : {played:8d}   Errors: {errorPercent:.2f}%', globalStats, 
                valueColors={'errorPercent': Fore.RED, ListenerRemoteStat.PLAYED: Fore.LIGHTGREEN_EX})
        terminal.appendSeparator()

        
        terminal.append('  Queue:')
        try:
            if queueStats[RemoteQueueStats.ERROR_MESSAGE]:
                terminal.append('\tRemote queue error: %s' % (Fore.RED + queueStats[RemoteQueueStats.ERROR_MESSAGE]))
            else:
                terminal.appendTemplate('\tMessages: {messageCount:d}   Used: {usedMessageCount:d}', queueStats)
        except Exception as e:
            message = (getattr(e, 'message', repr(e)))
            terminal.append(Fore.RED + 'Error: %s' % message)

        terminal.appendSeparator()

        for server in serversStats:
            self.refreshServer(server)    

        terminal.flush()

    def refreshServer(self, serverStat: dict):
        terminal = self.terminal
        try:
            host = serverStat['host']
            
            if 'exception' in serverStat:
                terminal.append(Fore.RED + '%s %s Connection Error, check the ip/host address or password'  % (Fore.YELLOW + 'Server ' + host, Fore.RED))
                return
            runnerStats = serverStat['runner']
            systemStats = serverStat['system']
            managerStats = serverStat['manager']
            version = runnerStats.get('version', 'unknown')
            terminal.appendTemplate('{id:s} {version:s} ({host:s})', {
                'version': Fore.LIGHTGREEN_EX + version,
                'host': Fore.LIGHTBLACK_EX + host, 
                'id': managerStats['serverId']
            })
            #terminal.append()
            #terminal.append('  Runner:')
            if runnerStats['played']:
                runnerStats['errorPercent'] =  (runnerStats['error'] / runnerStats['played']) * 100
            else:
                runnerStats['errorPercent'] = 0.0
            terminal.appendTemplate('\tPrepare: {prepare:4d}   Loging: {loggingIn:4d}   Playing: {playing:4d}   Played : {played:8d}   Errors: {errorPercent:.2f}%', runnerStats, 
                    valueColors={'errorPercent': Fore.RED, ListenerRemoteStat.PLAYED: Fore.LIGHTGREEN_EX})
            #terminal.append()
            #terminal.append('  System:')
            terminal.appendTemplate('\tCpu : {cpuCountP:4d} / {cpuCountL:4d}   Load:       {cpuPercentAvg:5.2f}%', systemStats)
            terminal.appendTemplate('\tMem Total: {memTotal:.2f}go  Available: {memAvailable:.2f}go   Used: {memActive:.2f}%%', systemStats, valueColor=Fore.CYAN)
            #terminal.append()
            #terminal.append('  Process Manager:')
            terminal.appendTemplate('\tStart at : {startTime:s}    Since : {elapsedTime:s}', managerStats)
            terminal.appendTemplate('\tProcess  : {processCount:3d} / {maxProcess:3d}   interval: {spawnInterval:.2f}s', managerStats)
            terminal.appendSeparator()
        except Exception as e:
            message = (getattr(e, 'message', repr(e)))
            terminal.append(Fore.RED + 'Error: %s' % message)
            #Terminal.append(dumps(serverStat, indent=4))
    
    def start(self):
        defautlConfig = {
            MonitorConfig.POLL_INTERVAL: 2.0
        }
        configData = MonitorConfig(self.configFile).getConfig(defautlConfig)
        self.config = configData
        self.terminal = Terminal('-')
        self.servers = configData[MonitorConfig.SERVERS].split(',')
        self.remoteQueue = RemoteQueue(configData[MonitorConfig.ACCOUNT_SQS_ENDPOINT])
        
        lastRefreshTime = 0
        while True:
            if self.shutdownEvent.is_set():
                break
            if (time() - lastRefreshTime) > configData[MonitorConfig.POLL_INTERVAL]:
                self.refreshAll()
                lastRefreshTime = time()
            sleep(1)
