# https://pythonspeed.com/articles/python-multiprocessing/ !!!top
from multiprocessing import Array, Event, Lock
import sys
import psutil
from src.services.console import Console
from src.services.drivers import DriverManager
from src.application.spotify.register import Register, RegisterContext
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

def showStats():
    totalThreads = 0
    totalAccounts = 0
    for count in threadsCount:
        totalThreads += count
    
    for count in accountsCount:
        totalAccounts += count
    
    elapsedTime = str(timedelta(seconds=round(time() - startTime)))

    width, height = get_terminal_size()
    console.clearScreen()
    separator = '_' * width
    lines = []
    lines.append(Fore.YELLOW + 'ZEUS LISTENER SERVICE STATS')
    lines.append(Fore.WHITE + 'Browser: ' + Fore.GREEN + browserVersion)
    lines.append(Fore.WHITE + 'Driver : ' + Fore.GREEN + driverVersion)
    lines.append('')
    lines += stats.getConsoleLines(width)
    lines.append(Fore.CYAN + 'Queue: %s:' % config.SQS_ENDPOINT)
    lines.append(Fore.BLUE + separator)
    lines.append(Fore.WHITE + 'Elapsed time    : %s' % (Fore.GREEN + elapsedTime))
    lines.append(Fore.WHITE + 'Total process   : %7d, threads: %7d' % (len(processes), totalThreads))
    lines.append(Fore.WHITE + 'Account created : %7d' % totalAccounts)
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
                    console.printAt(c*step, l+index, '#%d T:%d M:%d' % (tc, threadsCount[tc], accountsCount[tc]))
                tc+=1

    stdout.write('\n')
    stdout.flush()  

if __name__ == '__main__':
    startTime = time()
    showInfo = False
    noOutput = False
    for arg in argv:
        if arg == '--info':
            showInfo = True
        if arg == '--nooutput':
            noOutput = True
    
    config = Config()
    processes = []
    console = Console(ouput= not noOutput)
    driverManager = DriverManager(console)
    driverVersion = driverManager.getDriverVersion('chrome')
    browserVersion = driverManager.getBrowserVersion('chrome')
    client = boto3.client('sqs')
    shutdownEvent = Event()
    
    
    stats = Stats()
    messages = []
    lastProcessStart = 0
    lockThreadsCount = Lock()
    
    

    maxProcess = config.REGISTER_MAX_PROCESS
    if maxProcess < 0:
        maxProcess = psutil.cpu_count(logical=True)
    
    threadPerProcess = round(config.REGISTER_MAX_THREAD / maxProcess)
    
    threadsCount = Array('i', maxProcess)
    accountsCount = Array('i', maxProcess)

    try:
        totalAccountCount = int(input('How much account to create ?'))
    except:
        sys.exit(1)

    accountToCreate = round(totalAccountCount / maxProcess)

    vnc = False
    if (totalAccountCount == 1):
        response = input('Would you like to activate virtual screen [Y/n] ?')
        if response == '' or response == 'y' or response == 'Y':
            vnc = True

    chanel = 0
    for x in range(maxProcess):
        sleep(config.REGISTER_SPAWN_INTERVAL)
        threadsCount[chanel] = 0
        p_context = RegisterContext(
            config = config,
            console= console,
            lock=lockThreadsCount,
            shutdownEvent=shutdownEvent,
            maxThread=threadPerProcess,
            threadsCount=threadsCount,
            accountsCount=accountsCount,
            channel=chanel,
            accountToCreate= accountToCreate,
            playlist=config.PLAYLIST,
            vnc=vnc
        )

        p = Register(p_context)
        processes.append(p)
        p.start()
        chanel += 1
        if showInfo:
            showStats()
        
    
    while True:
        try:
            sleep(1)
            leftProcesses = []
            for p in processes:
                if p.is_alive():
                    leftProcesses.append(p)
            processes = leftProcesses
            if showInfo:
                showStats()
            if len(processes) == 0:
                break
        except KeyboardInterrupt:
            shutdownEvent.set()
            sleep(1)
            shutdown()
            break
        except:
            console.exception()
            break




    
