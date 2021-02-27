
#!/usr/bin/python3.8
from src.services.console import Console
import sys, os, argparse
from getpass import getuser
from configparser import ConfigParser
import signal
from requests import get
from json import loads
from colorama import Fore
from src.services.terminal import Terminal
import traceback
from time import sleep

VERSION = '1.0.0'

if __name__ == '__main__':
    if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS'.
        APP_PATH = sys._MEIPASS
    else:
        APP_PATH = os.path.dirname(os.path.abspath(__file__))


    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', help="Set the log path to the app dir", action="store_true", default=False)

    
    print('Start as user %s' % getuser())

    args = parser.parse_args()
    
    if args.debug:
        userDir = APP_PATH + '/temp'
    else:
        userDir = '/home/%s/.venom' % getuser()
    
    config = ConfigParser()
    config.read(userDir + '/config.ini')
    if 'MANAGER' in config.sections():
        listenerConfig      = config['MANAGER']
        SERVERS        = listenerConfig.get('servers', '').strip().split(',')
    
    def stop(signum, frame):
        sys.exit()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    terminal = Terminal('-')

    class RemoteStats:
        def __init__(self, jsonData) -> None:
            self.__dict__ = loads(jsonData)

        

    remoteStats = RemoteStats

    while True:
        sleep(1)
        terminal.newPage()
        terminal.append('Venom Manager v%s' % VERSION)
        terminal.appendSeparator()
        terminal.append('Servers:')
        terminal.appendSeparator()
        
        for server in SERVERS:
            
            ip = server.strip()
            data = get('https://%s:63443/?k=6253a4f08f16ad236dd5cb8f7aaba35f' % ip, verify=False).text
            try:
                remoteStats = RemoteStats(data)
                #system = data['system']
                #runner = data['runner']
                #manager = data['manager']
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
                terminal.appendTemplate('{id:s} ({ip:s})', {'ip': Fore.LIGHTBLACK_EX + ip, 'id': remoteStats.manager['serverId']}, Fore.YELLOW)
                terminal.append()
                terminal.append('  Runner:')
                if remoteStats.runner['played']:
                    remoteStats.runner['errorPercent'] = remoteStats.runner['error'] / remoteStats.runner['played']
                else:
                    remoteStats.runner['errorPercent'] = 0.0
                terminal.appendTemplate('\tPlayed : {played:8d}   Playing: {playing:4d} Loging: {loggingIn:4d}   Errors: {errorPercent:.2f}%%', remoteStats.runner)
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
                terminal.append('error - %s' % (traceback.format_exc()))
                break

            terminal.flush()
