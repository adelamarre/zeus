# https://pythonspeed.com/articles/python-multiprocessing/ !!!top
from multiprocessing import Array, Event, Lock
import psutil
from src.services.console import Console
from src.services.drivers import DriverManager
from src.application.spotify.listener import Listener, ListenerContext
import boto3
from src.services.config import Config
from time import sleep
from os import get_terminal_size, stat
from colorama import Fore
from sys import stdout, argv
from src.services.stats import Stats
from time import time
from psutil import virtual_memory, cpu_count, getloadavg
from datetime import timedelta




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
    totalThreads = 0
    totalMessages = 0
    for count in data['threadsCount']:
        totalThreads += count
    
    for count in data['messagesCount']:
        totalMessages += count
    

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
    lines.append(Fore.WHITE + 'Total process : %7d, threads: %7d' % (int(data['totalProcess']), totalThreads))
    lines.append(Fore.WHITE + 'Message read  : %7d' % int(data['totalMessageReceived']))
    lines.append(Fore.BLUE + separator)

    
    index = 1
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
    
    totalMessageReceived = 0
    stats = Stats()
    messages = []
    lastProcessStart = 0
    lockThreadsCount = Lock()
    
    def _showStats():
        showStats({
            'totalProcess': len(processes),
            'totalMessageReceived': totalMessageReceived,
            'elapsedTime': str(timedelta(seconds=round(time() - startTime))),
            'browser': browserVersion,
            'driver': driverVersion,
            'threadsCount': threadsCount,
            'messagesCount': messagesCount,
        }, config.SQS_URL, stats)

    maxProcess = config.LISTENER_MAX_PROCESS
    if maxProcess < 0:
        maxProcess = psutil.cpu_count(logical=True)
    
    threadPerProcess = round(config.LISTENER_MAX_THREAD / maxProcess)
    
    threadsCount = Array('i', maxProcess)
    messagesCount = Array('i', maxProcess)

    chanel = 0
    for x in range(maxProcess):
        sleep(config.LISTENER_SPAWN_INTERVAL)
        threadsCount[chanel] = 0
        p_context = ListenerContext(
            config = config,
            console= console,
            lock=lockThreadsCount,
            shutdownEvent=shutdownEvent,
            maxThread=threadPerProcess,
            threadsCount=threadsCount,
            messagesCount=messagesCount,
            channel=chanel
        )
        p = Listener(p_context)
        processes.append(p)
        p.start()
        chanel += 1
        if showInfo:
            _showStats()
        
    
    while True:
        try:
            sleep(1)
            leftProcesses = []
            for p in processes:
                if p.is_alive():
                    leftProcesses.append(p)
            processes = leftProcesses
            if showInfo:
                _showStats()
        except KeyboardInterrupt:
            shutdownEvent.set()
            sleep(1)
            shutdown()
            break
        except:
            console.exception()
            break




    
