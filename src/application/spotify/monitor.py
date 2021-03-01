
import sys
from src.application.scenario import AbstractScenario
from src import VERSION
from src.services.aws import RemoteQueue
from src.services.config import Config
from json import loads
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
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def refreshAll(self):
        terminal = self.terminal
        terminal.newPage()
        terminal.append(Fore.RED + 'Venom Monitor v%s' % VERSION)
        terminal.appendSeparator()
        terminal.append('Servers:')
        terminal.appendSeparator()

        remoteQueueStats = self.remoteQueue.getStats()
        terminal.append('  Queue:')
        if remoteQueueStats['error']:
            terminal.append('\tRemote queue error: %s' % (Fore.RED + remoteQueueStats.error))
        else:
            terminal.appendTemplate('\tMessages: {messageCount:d}   Used: {usedMessageCount:d}', remoteQueueStats)
        terminal.appendSeparator()

        for server in self.servers:
            self.refreshServer(server)    
        terminal.flush()

    def refreshServer(self, server: str):
        terminal = self.terminal
        host = server.strip()
        data = get('https://%s:63443/?k=%s' % (host, self.monitorConfig['secret']), verify=False).text
        try:
            remoteStats = RemoteStats(data)
            terminal.appendTemplate('{id:s} ({host:s})', {'host': Fore.LIGHTBLACK_EX + host, 'id': remoteStats.manager['serverId']}, Fore.YELLOW)
            terminal.append()
            terminal.append('  Runner:')
            if remoteStats.runner['played']:
                remoteStats.runner['errorPercent'] =  (remoteStats.runner['error'] / remoteStats.runner['played']) * 100
            else:
                remoteStats.runner['errorPercent'] = 0.0
            terminal.appendTemplate('\tLoging: {loggingIn:4d}   Playing: {playing:4d}   Played : {played:8d}   Errors: {errorPercent:.2f}%', remoteStats.runner, 
                    valueColors={'errorPercent': Fore.RED, 'played': Fore.LIGHTGREEN_EX})
            terminal.append()
            terminal.append('  System:')
            terminal.appendTemplate('\tCpu : {cpuCountP:4d} / {cpuCountL:4d}   Load:       {cpuPercentAvg:.2f}%', remoteStats.system)
            terminal.appendTemplate('\tMem Total: {memTotal:.2f}go  Available: {memAvailable:.2f}go   Used: {memActive:.2f}%%', remoteStats.system, valueColor=Fore.CYAN)
            terminal.append()
            terminal.append('  Process Manager:')
            terminal.appendTemplate('\tStart at : {startTime:s}    Since : {elapsedTime:s}', remoteStats.manager)
            terminal.appendTemplate('\tProcess  : {processCount:d} / {maxProcess:d}   interval: {spawnInterval:.2f}s', remoteStats.manager)
            terminal.appendSeparator()
        except:
            terminal.append(Fore.RED + 'The server is unreachable or the password is not accepted.' )
    
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