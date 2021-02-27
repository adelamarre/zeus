# https://pythonspeed.com/articles/python-multiprocessing/ !!!top
from multiprocessing import Array, Event, Lock, current_process, process
from multiprocessing.context import Process
import os
from random import randint
import psutil
from src.services.console import Console
from src.services.drivers import DriverManager
from boto3 import client
from src.services.config import Config
from time import sleep
from os import get_terminal_size
from colorama import Fore
from sys import stdout, argv
from src.services.stats import Stats
from time import time
from psutil import getloadavg
from datetime import datetime, timedelta
from xvfbwrapper import Xvfb
from src.services.x11vncwrapper import X11vnc
from src.application.spotify.Spotify import Adapter
from shutil import rmtree
from gc import collect
from json import loads
from src.services.proxies import ProxyManager, PROXY_FILE_LISTENER
from src.application.spotify.listener import ListenerStat, ListenerProcess

STATE_STARTING = 0
STATE_LOGGING = 1
STATE_LISTENING = 2
STATE_CLOSING = 4

startTime = time()

def shutdown(processes):
    shutdownEvent.set()
    print('Shutdown, please wait...')

    count = 0
    while len(processes):
        leftProcess = []
        if p.is_alive():
            try:
                if count > 1:
                    p.terminate()
                elif count > 4:
                    p.kill()
            except:
                pass
            leftProcess.append(p)
        processes = leftProcess
        sleep(2)
        count += 1

    

def showStats(totalProcess, systemStats: Stats, listenerStats: Array):
    
    width, height = get_terminal_size()
    elapsedTime = str(timedelta(seconds=round(time() - startTime)))
    console.clearScreen()
    separator = '_' * width
    lines = []
    lines.append(Fore.YELLOW + 'ZEUS LISTENER SERVICE STATS')
    #lines.append(Fore.WHITE + 'Browser: ' + Fore.GREEN + data['browser'])
    #lines.append(Fore.WHITE + 'Driver : ' + Fore.GREEN + data['driver'])
    #lines.append('')
    lines += systemStats.getConsoleLines(width)
    #lines.append(Fore.CYAN + 'Queue: %s:' % queueUrl)
    lines.append(Fore.BLUE + separator)
    lines.append(Fore.WHITE + 'Elapsed time  : %s' % (Fore.GREEN + elapsedTime))
    lines.append(Fore.WHITE + 'Total process : %7d' % totalProcess)
    lines.append(Fore.WHITE + 'Logged in: %7d   Played: %7d   Error: %7d   Driver None: %7d' % 
        (listenerStats[ListenerStat.LOGGED_IN],listenerStats[STAT_PLAYED], listenerStats[STAT_ERROR], listenerStats[STAT_DRIVER_NONE]) 
    )
    lines.append(Fore.BLUE + separator)
    index = 1
    for line in lines:
        console.printAt(1, index, line)
        index += 1
    
    ''' index = 1
    for line in lines:
        console.printAt(1, index, line)
        index += 1

    with lockThreadsCount:
        totalCounts = len(threadsCount)
        nbrlines = round(totalCounts / 4)
        if nbrlines == 0:
            nbrlines = 1
        step = round(width / 4)
        tc = 0
        for l in range(nbrlines):
            for c in range(4):
                if tc < totalCounts:
                    console.printAt(c*step, l+index, '#%d T:%d M:%d' % (tc, threadsCount[tc], messagesCount[tc]))
                tc+=1
 '''
    stdout.write('\n')
    stdout.flush()  


if __name__ == '__main__':
    showInfo = False
    noOutput = False
    headless = False
    vnc = False
    for arg in argv:
        if arg == '--info':
            showInfo = True
        if arg == '--nooutput':
            noOutput = True
        if arg == '--headless':
            headless = True
        if arg == '--vnc':
            vnc = True
    
    logDir = (os.path.dirname(__file__) or '.') + '/temp/listener/' + datetime.now().strftime("%m-%d-%Y-%H-%M-%S") + '/'
    logfile =  'all.log'
    os.makedirs(logDir, exist_ok=True)
    screenshotDir = logDir + 'screenshot/'
    os.makedirs(screenshotDir, exist_ok=True)

    shutdownEvent = Event()
    config = Config()
    processes = []
    console = Console(ouput= not noOutput, logfile=logfile)
    proxyManager = ProxyManager(PROXY_FILE_LISTENER)
    

    systemStats = Stats()
   
    maxProcess = config.LISTENER_MAX_PROCESS
    if maxProcess < 0:
        maxProcess = psutil.cpu_count(logical=True)
    
    runnerStats = Array('i', 4)
    

    processStates = Array('i', maxProcess)
    messages = []
    client = client('sqs')
    while True:
        try:
            sleep(config.LISTENER_SPAWN_INTERVAL)
            freeslot = maxProcess - len(processes)
            if freeslot:
                try:
                    
                except:
                    runnerStats[ListenerStat.ERROR] += 1
                    console.exception()    
            
            leftProcesses = []
            for p in processes:
                if p.is_alive():
                    leftProcesses.append(p)
                else:
                    p.join()
            processes = leftProcesses
            if showInfo:
                showStats(len(processes), systemStats, runnerStats)
            #if len(processes) == 0:
            #    break
        except KeyboardInterrupt:
            shutdown(processes)
            break
        except:
            console.exception()
            shutdown(processes)
            break



    
