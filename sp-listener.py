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

STAT_LOGGED_IN = 0
STAT_PLAYED = 1
STAT_ERROR = 2
STAT_DRIVER_NONE = 3

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
        (listenerStats[STAT_LOGGED_IN],listenerStats[STAT_PLAYED], listenerStats[STAT_ERROR], listenerStats[STAT_DRIVER_NONE]) 
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

def run(
    console: Console, 
    shutdownEvent: Event, 
    headless: bool, 
    user: dict,
    proxy: dict,
    playlist: str,
    vnc: bool,
    screenshotDir,
    stats: Array,
    states: Array
    ):
        
        tid = current_process().pid
        console.log('#%d Start' % tid)

        driver = None
        try:
            if shutdownEvent.is_set():
                return 
            vdisplay = None
            x11vnc = None
            if headless == False:
                width = 1280
                height = 1024
                if 'windowSize' in user:
                    [width,height] = user['windowSize'].split(',')
                vdisplay = Xvfb(width=width, height=height, colordepth=24, tempdir=None, noreset='+render')
                vdisplay.start()
                if vnc:
                    x11vnc = X11vnc(vdisplay)
                    x11vnc.start()

            driverManager = DriverManager(console, shutdownEvent)
            driverData = driverManager.getDriver(
                type='chrome',
                uid=tid,
                user=user,
                proxy=proxy,
                headless= headless
            )
            if not driverData:
                raise Exception('No driverData was returned from adapter')
            driver = driverData['driver']
            userDataDir = driverData['userDataDir']
            if not driver:
                raise Exception('No driver was returned from adapter')
            
        except:
            stats[STAT_DRIVER_NONE] += 1
            console.exception('Driver unavailable')
        else:
            try:
                spotify = Adapter(driver, console, shutdownEvent)
                spotify.login(user['email'], user['password'])
                stats[STAT_LOGGED_IN] += 1
                console.log('#%d Logged In' % tid)
                spotify.playPlaylist(playlist, shutdownEvent, 80, 100)
                console.log('#%d Played' % tid)
                stats[STAT_PLAYED] += 1
            except Exception as e:
                stats[STAT_ERROR] += 1
                try:
                    id = randint(10000, 99999)
                    
                    with open(screenshotDir + ('%d.log' % id), 'w') as f:
                        f.write(str(e))
                    driver.save_screenshot(screenshotDir  + ('%d.png' % id))
                except:
                    console.exception()
                            
        if driver:
            try:
                driver.quit()
                del driver
            except:
                pass
        if userDataDir:
            try:
                rmtree(path=userDataDir, ignore_errors=True)
            except:
                pass
        if x11vnc: #Terminate vnc server if any
            try:
                x11vnc.stop()
                del x11vnc
            except:
                pass
        if vdisplay:
            try:
                vdisplay.stop()
                del vdisplay
            except:
                pass
        collect()

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
    runnerStats[STAT_PLAYED] = 0
    runnerStats[STAT_LOGGED_IN] = 0
    runnerStats[STAT_ERROR] = 0
    runnerStats[STAT_DRIVER_NONE] = 0
    
    

    processStates = Array('i', maxProcess)
    messages = []
    client = client('sqs')
    while True:
        try:
            sleep(config.LISTENER_SPAWN_INTERVAL)
            freeslot = maxProcess - len(processes)
            if freeslot:
                try:
                    if len(messages) < 1:
                        if freeslot > 10:
                            nbrOfMessages = 10
                        else:
                            nbrOfMessages = freeslot
                        response = client.receive_message(
                            QueueUrl=config.SQS_ENDPOINT,
                            MaxNumberOfMessages=nbrOfMessages,
                            VisibilityTimeout=600,
                            WaitTimeSeconds=2,
                        )
                        if 'Messages' in response:
                            newMessages = response['Messages']
                            messages =  newMessages + messages
                    
                    if len(messages):
                        message = messages.pop()
                        body = loads(message['Body'])
                        proxy = None
                        if config.LISTENER_OVERIDE_PLAYLIST:
                            body['playlist'] = config.LISTENER_OVERIDE_PLAYLIST
                        if config.LISTENER_OVERIDE_PROXY:
                            proxy = proxyManager.getRandomProxy()
                            
                        p = Process(target=run, args=(
                            console, 
                            shutdownEvent, 
                            headless, 
                            body['user'],
                            proxy,
                            body['playlist'],
                            vnc,
                            screenshotDir,
                            runnerStats,
                            processStates,
                            
                        ))
                        p.start()
                        processes.append(p)
                        client.delete_message(
                            QueueUrl=config.SQS_ENDPOINT,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                except:
                    runnerStats[STAT_ERROR] += 1
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
            if len(processes) == 0:
                break
        except KeyboardInterrupt:
            shutdown(processes)
            break
        except:
            console.exception()
            shutdown(processes)
            break



    
