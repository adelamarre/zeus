
from src.application.spotify.listener import ListenerRemoteStat, ListenerStat
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
                serverStat = loads(get('https://%s:63443/?k=%s' % (host, self.monitorConfig['secret']), verify=False).text)
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
                terminal.append(Fore.RED + '%s %sConnection Error, check the ip/host address or password'  % (Fore.YELLOW + 'Server ' + host, Fore.RED))
                return
            runnerStats = serverStat['runner']
            systemStats = serverStat['system']
            managerStats = serverStat['manager']
            
            terminal.appendTemplate('{id:s} ({host:s})', {'host': Fore.LIGHTBLACK_EX + host, 'id': managerStats['serverId']}, Fore.YELLOW)
            terminal.append()
            terminal.append('  Runner:')
            if runnerStats['played']:
                runnerStats['errorPercent'] =  (runnerStats['error'] / runnerStats['played']) * 100
            else:
                runnerStats['errorPercent'] = 0.0
            terminal.appendTemplate('\tLoging: {loggingIn:4d}   Playing: {playing:4d}   Played : {played:8d}   Errors: {errorPercent:.2f}%', runnerStats, 
                    valueColors={'errorPercent': Fore.RED, ListenerRemoteStat.PLAYED: Fore.LIGHTGREEN_EX})
            terminal.append()
            terminal.append('  System:')
            terminal.appendTemplate('\tCpu : {cpuCountP:4d} / {cpuCountL:4d}   Load:       {cpuPercentAvg:5.2f}%', systemStats)
            terminal.appendTemplate('\tMem Total: {memTotal:.2f}go  Available: {memAvailable:.2f}go   Used: {memActive:.2f}%%', systemStats, valueColor=Fore.CYAN)
            terminal.append()
            terminal.append('  Process Manager:')
            terminal.appendTemplate('\tStart at : {startTime:s}    Since : {elapsedTime:s}', managerStats)
            terminal.appendTemplate('\tProcess  : {processCount:3d} / {maxProcess:3d}   interval: {spawnInterval:.2f}s', managerStats)
            terminal.appendSeparator()
        except Exception as e:
            message = (getattr(e, 'message', repr(e)))
            terminal.append(Fore.RED + 'Error: %s' % message)
            #Terminal.append(dumps(serverStat, indent=4))
    
    def start(self):
        defautlConfig = {
            'poll_interval': 2.0
        }
        monitorConfig = Config.getMonitorConfig(self.configFile, defautlConfig)

        if not monitorConfig:
            sys.exit('I can not continue without configuraton')
        

        #https://sqs.eu-west-3.amazonaws.com/884650520697/18e66ed8d655f1747c9afbc572955f46

        if not monitorConfig['sqs_endpoint']:
            sys.exit('you need to set the sqs_endpoint in the config file.')

        if not monitorConfig['servers']:
            sys.exit('you need to set the servers list in the config file.')

        if not monitorConfig['secret']:
            sys.exit('you need to set the password to access servers stats.')

        self.monitorConfig = monitorConfig
        self.terminal = Terminal('-')
        self.servers = monitorConfig['servers'].split(',')
        self.remoteQueue = RemoteQueue(monitorConfig['sqs_endpoint'])
        
        lastRefreshTime = 0
        while True:
            if self.shutdownEvent.is_set():
                break
            if (time() - lastRefreshTime) > monitorConfig['poll_interval']:
                self.refreshAll()
                lastRefreshTime = time()
            sleep(1)
             
            

"""
{
    "system": {
        "memTotal": 62.81103515625,
        "memAvailable": 60.04899978637695,
        "memActive": 4.4,
        "cpuCountP": 8,
        "cpuCountL": 16,
        "cpuPercentAvg": 0.4
    },
    "runner": {
        "version": "1.0.7",
        "error": 0,
        "driverNone": 0,
        "played": 0,
        "loggingIn": 0,
        "playing": 0,
        "overriddePlaylist": true
    },
    "manager": {
        "maxProcess": 100,
        "processCount": 0,
        "spawnInterval": 0.3,
        "startTime": "2021-02-27 13:18:58.417318",
        "elapsedTime": "0:03:23"
    }
}
"""