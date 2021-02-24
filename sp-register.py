# https://pythonspeed.com/articles/python-multiprocessing/ !!!top
from json import dumps
from multiprocessing import Array, Event, Lock, current_process
from multiprocessing.context import Process
import os
from src.services.x11vncwrapper import X11vnc
import sys
import psutil
from requests.api import head
from xvfbwrapper import Xvfb
from src.services.console import Console
from src.services.drivers import DriverManager
from src.application.spotify.register import Register, RegisterContext
import boto3
from src.services.config import Config
from time import sleep
from os import get_terminal_size, mkdir
from colorama import Fore
from sys import stdout, argv
from src.services.stats import Stats
from time import time
from psutil import virtual_memory, cpu_count, getloadavg
from datetime import datetime, timedelta
from src.application.spotify.Spotify import Adapter
from random import randint
from shutil import rmtree
from gc import collect
from src.services.proxies import ProxyManager, PROXY_FILE_REGISTER, PROXY_FILE_LISTENER
from src.services.userAgents import UserAgentManager
from src.services.users import UserManager

STAT_ACCOUNT_CREATED = 0
STAT_ERROR = 1
STAT_DRIVER_NONE = 2

STATE_STARTING = 0
STATE_FORM = 1
STATE_SUBMIT = 2
STATE_CLOSING = 4

def shutdown(shutdownEvent, processes):
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
    lines.append(Fore.YELLOW + 'ZEUS REGISTER SERVICE STATS')
    #lines.append(Fore.WHITE + 'Browser: ' + Fore.GREEN + data['browser'])
    #lines.append(Fore.WHITE + 'Driver : ' + Fore.GREEN + data['driver'])
    #lines.append('')
    lines += systemStats.getConsoleLines(width)
    #lines.append(Fore.CYAN + 'Queue: %s:' % queueUrl)
    lines.append(Fore.BLUE + separator)
    lines.append(Fore.WHITE + 'Elapsed time  : %s' % (Fore.GREEN + elapsedTime))
    lines.append(Fore.WHITE + 'Total process : %7d' % totalProcess)
    lines.append(Fore.WHITE + 'Account created: %7d   Error: %7d   Driver None: %7d' % 
        (listenerStats[STAT_ACCOUNT_CREATED], listenerStats[STAT_ERROR], listenerStats[STAT_DRIVER_NONE]) 
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


def runner(
    console: Console, 
    shutdownEvent: Event, 
    headless: bool, 
    user: dict,
    proxy: dict,
    playlist: str,
    vnc: bool,
    sqsEndpoint: str,
    screenshotDir: str,
    runnerStats: Array,
    processStates: Array
    ):
        tid = current_process().pid
        console.log('#%d Start' % tid)
        driver = None
        vdisplay = None
        x11vnc = None
        userDataDir = None
        spotify = None
        try:
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
            del driverManager
            collect()
            if not driverData or not driverData['driver']:
                if vdisplay:
                    vdisplay.stop()
                if x11vnc:
                    x11vnc.stop()
                raise Exception('No driver was returned from adapter')

            driver = driverData['driver']
            userDataDir = driverData['userDataDir']
        except Exception as e:
            runnerStats[STAT_DRIVER_NONE] += 1
            console.exception('Driver unavailable')
        else:
            try:
                spotify = Adapter(driver, console, shutdownEvent)
                console.log('#%d Start create account for %s' % (tid, user['email']))
                spotify.register(user)
                try:
                    boto3.client('sqs').send_message(
                        QueueUrl=sqsEndpoint,
                        MessageBody=dumps({
                            'user': user,
                            'playlist': playlist
                        }),
                        DelaySeconds=1,
                    )
                except:
                    console.exception('#%d Failed to send message to the queue' % tid)
                else:
                    console.log('#%d Account created for %s' % (tid, user['email']))
                    runnerStats[STAT_ACCOUNT_CREATED] += 1
            except Exception as e:
                runnerStats[STAT_ERROR] += 1
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
        if spotify:
            try:
                del spotify
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
        console.log('#%d Stop' % tid)
        collect()

if __name__ == '__main__':
    cpid = current_process().pid
    startTime = time()
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

    #Manage log 
    logDir = (os.path.dirname(__file__) or '.') + '/temp/register/' + datetime.now().strftime("%m-%d-%Y-%H-%M-%S") + '/'
    logfile =  logDir + 'all.log'
    os.makedirs(logDir, exist_ok=True)
    screenshotDir = logDir + 'screenshot/'
    os.makedirs(screenshotDir, exist_ok=True)

    #Util
    shutdownEvent = Event()
    config = Config()
    console = Console(ouput= not noOutput, logfile=logfile)
    proxyRegisterManager = ProxyManager(proxyFile=PROXY_FILE_REGISTER)
    proxyListenerManager = ProxyManager(proxyFile=PROXY_FILE_LISTENER)
    userManager = UserManager(console)
    userAgentManager = UserAgentManager()
    client = boto3.client('sqs')
    systemStats = Stats()
    processes = []
    users = []
    
    maxProcess = config.REGISTER_MAX_PROCESS
    if maxProcess < 0:
        maxProcess = psutil.cpu_count(logical=True)

    #Process communication
    runnerStats = Array('i', 4)
    processStates = Array('i', maxProcess)
    runnerStats[STAT_ACCOUNT_CREATED] = 0
    runnerStats[STAT_ERROR] = 0
    runnerStats[STAT_DRIVER_NONE] = 0
    
    
    try:
        totalAccountCount = int(input('How much account to create ?'))
    except:
        sys.exit()

    chanel = 0
    
    for x in range(totalAccountCount):
        users.append({
            'user': userManager.createRandomUser(
                proxy = proxyListenerManager.getRandomProxy(),
                userAgent= userAgentManager.getRandomUserAgent(),
                application='sp',
            ),
            'playlist': config.PLAYLIST
        })
        
    
    while True:
        try:
            sleep(config.REGISTER_SPAWN_INTERVAL)
            freeslot = maxProcess - len(processes)
            if freeslot and len(users):
                try:
                    userData = users.pop() 
                    proxy = proxyRegisterManager.getRandomProxy()
                    p = Process(target=runner, args=(
                        console, 
                        shutdownEvent, 
                        headless, 
                        userData['user'],
                        proxy,
                        userData['playlist'],
                        vnc,
                        config.SQS_ENDPOINT,
                        screenshotDir,
                        runnerStats,
                        processStates,
                    ))
                    p.start()
                    processes.append(p)
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
    print('Stopped')



    
