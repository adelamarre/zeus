# https://pythonspeed.com/articles/python-multiprocessing/ !!!top
from multiprocessing import current_process, Process, Event
from src.services.console import Console
from src.services.drivers import DriverManager
from src.application.spotify import Spotify
import boto3
from traceback import format_exc
from src.services.config import Config
from json import loads
from time import sleep
from os import environ, get_terminal_size, stat, terminal_size
from traceback import format_exc
from shutil import rmtree
from colorama import Fore, Back, Style
from sys import stdout, argv
from xvfbwrapper import Xvfb
from src.services.stats import Stats
from queue import LifoQueue
from time import time
from psutil import virtual_memory, cpu_count, getloadavg
from datetime import timedelta


def runner(context):
    #environ["DISPLAY"] = ":0"
    driverManager = context['driverManager']
    user = context['user']
    console = context['console']
    playlist = context['playlist']
    queueUrl = context['queueUrl']
    receiptHandle = context['receiptHandle']
    shutdownEvent = context['shutdownEvent']
    
    pid = current_process().pid
    
    try: 
        vdisplay = Xvfb(width=1280, height=1024, colordepth=24, tempdir=None, noreset='+render')
        vdisplay.start()
        driverData = driverManager.getDriver(
            type='chrome',
            uid=pid,
            user=user,
        )
        if not driverData:
            return

        driver = driverData['driver']
        userDataDir = driverData['userDataDir']
        if not driver:
            return
    except:
        console.error('Unavailale webdriver: %s' % format_exc())
    else:
        spotify = Spotify.Adapter(driver, console, shutdownEvent)
        if spotify.login(user['email'], user['password']):
            if not shutdownEvent.is_set():
                spotify.playPlaylist(playlist, 90, 110)
        
        client = boto3.client('sqs')
        client.delete_message(
            QueueUrl=queueUrl,
            ReceiptHandle=receiptHandle
        )           
    if driver:
        try:
            driver.quit()
        except:
            pass
    if userDataDir:
        try:
            rmtree(path=userDataDir, ignore_errors=True)
        except:
            pass
    if vdisplay:
        try:
            vdisplay.stop()
        except:
            pass

def shutdown():
    print('Shutdown, please wait...')
    for p in processes:
        if p.is_alive():
            try:
                p.terminate()
            except:
                pass
    driverManager.purge()

def showStats(data, queueUrl, stats: Stats):
    width, height = get_terminal_size()
    console.clearScreen()
    separator = '_' * width
    lines = []
    lines.append(Fore.YELLOW + 'ZEUS LISTENER SERVICE STATS')
    lines.append(Fore.WHITE + 'Browser: ' + Fore.GREEN + data['browser'])
    lines.append(Fore.WHITE + 'Driver : ' + Fore.GREEN + data['driver'])
    lines.append('')
    lines += stats.getConsoleLines(width)
    lines.append(Fore.CYAN + 'Queue: %s:' % queueUrl)
    lines.append(Fore.BLUE + separator)
    lines.append(Fore.WHITE + 'Elapsed time  : %s' % (Fore.GREEN + data['elapsedTime']))
    lines.append(Fore.WHITE + 'Total process : %7d' % int(data['totalProcess']))
    lines.append(Fore.WHITE + 'Message read  : %7d' % int(data['totalMessageReceived']))
    lines.append(Fore.BLUE + separator)
    index = 1
    for line in lines:
        console.printAt(1, index, line)
        index += 1

    stdout.write('\n')
    stdout.flush()  

def couldSpawnProcess(count, min, max, interval, load_threshold, lastProcessStart):
    if (time() - lastProcessStart) < interval:
        return False
    result = False
    if (count < min):
        result = True
    elif ((max != -1) and (max > count)):
        result = True
    elif (max == -1) and ((time() - lastProcessStart) > load_threshold):
        memstat = virtual_memory()
        load = [x / cpu_count() * 100 for x in getloadavg()]
        result = load[0] < 95.0
    return result

if __name__ == '__main__':
    startTime = time()
    for arg in argv:
        showInfo = (arg == '--info')
    
    config = Config()
    processes = []
    console = Console()
    driverManager = DriverManager(console)
    driverVersion = driverManager.getDriverVersion('chrome')
    browserVersion = driverManager.getBrowserVersion('chrome')
    client = boto3.client('sqs')
    shutdownEvent = Event()
    lock = Event()
    totalMessageReceived = 0
    stats = Stats()
    messages = []
    lastProcessStart = 0
    while True:
        try:
            sleep(config.LISTENER_SPAWN_PROCESS_INTERVAL)
            if couldSpawnProcess(
                len(processes),
                config.LISTENER_MIN_PROCESS,
                config.LISTENER_MAX_PROCESS,
                config.LISTENER_SPAWN_PROCESS_INTERVAL,
                config.LISTENER_LOAD_THRESHOLD,
                lastProcessStart
            ):

            #if (((config.LISTENER_MAX_PROCESS == -1) or (len(processes) < config.MAX_LISTENER_PROCESS)) and stats.couldStartProcess()):)
                if len(messages) < 1:
                    response = client.receive_message(
                        QueueUrl=config.SQS_URL,
                        MaxNumberOfMessages=10,
                        VisibilityTimeout=600,
                        WaitTimeSeconds=2,
                    )
                    if 'Messages' in response:
                        newMessages = response['Messages']
                        messages =  newMessages + messages
                        totalMessageReceived += len(messages)

                if len(messages):
                    message = messages.pop()
                    body = loads(message['Body'])
                    if config.LISTENER_OVERIDE_PLAYLIST:
                        body['playlist'] = config.LISTENER_OVERIDE_PLAYLIST

                    context = {
                        'driverManager': driverManager,
                        'console': console,
                        'user': body['user'],
                        'playlist': body['playlist'],
                        'lock': lock,
                        'queueUrl': config.SQS_URL,
                        'receiptHandle': message['ReceiptHandle'],
                        'shutdownEvent': shutdownEvent
                    }
                    lastProcessStart = time()
                    p = Process(target=runner, args=(context,))
                    processes.append(p)
                    p.start()

            leftProcesses = []
            for p in processes:
                if p.is_alive():
                    leftProcesses.append(p)
            processes = leftProcesses
            if showInfo:
                showStats({
                    'totalProcess': len(processes),
                    'totalMessageReceived': totalMessageReceived,
                    'elapsedTime': str(timedelta(seconds=round(time() - startTime))),
                    'browser': browserVersion,
                    'driver': driverVersion,
                }, config.SQS_URL, stats)
        except KeyboardInterrupt:
            shutdown()
            break
        except:
            console.exception()
            break




    
