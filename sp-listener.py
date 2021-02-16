# https://pythonspeed.com/articles/python-multiprocessing/ !!!top
from multiprocessing import Process, Event
import sys

import psutil
from src.services.console import Console
from src.services.drivers import DriverManager
from src.application.spotify.listener import ListenerContext, runner
import boto3
from src.services.config import Config
from json import loads
from time import sleep
from os import environ, get_terminal_size, stat, terminal_size
from traceback import format_exc

from colorama import Fore, Back, Style
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
    
    

    maxProcess = config.LISTENER_MAX_PROCESS
    if maxProcess < 0:
        maxProcess = psutil.cpu_count(logical=True)
    threadPerProcess = round(config.LISTENER_MAX_THREAD / maxProcess)

    for x in range(maxProcess):
        p_context = ListenerContext(
            config = config,
        

        )


    while True:
        sleep(1)
        try:
            if len(processes) < maxProcess:
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




    
