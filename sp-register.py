# https://pythonspeed.com/articles/python-multiprocessing/ !!!top
from multiprocessing import Lock, current_process, Process, Event
import traceback
from src.services.console import Console
from src.services.drivers import DriverManager
from src.services.users import UserManager
from src.services.userAgents import UserAgentManager
from src.services.proxies import PROXY_FILE_LISTENER, PROXY_FILE_REGISTER, ProxyManager
from src.application.spotify import Spotify
import boto3
from traceback import format_exc
from src.services.config import Config
from os import get_terminal_size
import json
from time import sleep
from shutil import rmtree
from xvfbwrapper import Xvfb
from colorama import Fore, Back, Style
from sys import stdout
from time import time
from datetime import timedelta

def showStats(data):
    width, height = get_terminal_size()
    console.clearScreen()
    separator = '_' * width
    lines = []
    lines.append(Fore.YELLOW + 'ZEUS LISTENER SERVICE STATS')
    lines.append('\n')
    lines.append(Fore.CYAN + 'Queue: %s:' % data['queueUrl'])
    lines.append(Fore.BLUE + separator)
    lines.append(Fore.WHITE + 'Elapsed time     : %s' % (Fore.GREEN + data['elapsedTime']))
    lines.append(Fore.WHITE + 'Total process    : %6d' % int(data['totalProcess']))
    lines.append(Fore.WHITE + 'Message in queue : %6d/%6d' % (
        int(data['queueAttributes']['ApproximateNumberOfMessages']),
        int(data['queueAttributes']['ApproximateNumberOfMessagesNotVisible'])
    ))
    lines.append(Fore.BLUE + separator)
    index = 1
    for line in lines:
        console.printAt(1, index, line)
        index += 1

    stdout.write('\n')
    stdout.flush()

def runner(context):  
    driverManager = context['driverManager']
    user = context['user']
    console = context['console']
    playlist = context['playlist']
    queueUrl = context['queueUrl']
    proxy = context['proxy']
    shutdownEvent = context['shutdownEvent']
    totalMessageReceived = 0
    pid = current_process().pid
    
    try:
        vdisplay = Xvfb(width=1280, height=1024)
        vdisplay.start() 
        print('Start runner %s' % pid)
        driverData = driverManager.getDriver(
            type='chrome',
            uid=pid,
            user=user,
            proxy=proxy
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
        try:
            spotify = Spotify.Adapter(driver, console, shutdownEvent)
            if not shutdownEvent.is_set():
                if spotify.register(user):
                    message = {
                        'user': user,
                        'playlist': playlist
                    }
                    client = boto3.client('sqs')
                    client.send_message(
                        QueueUrl=queueUrl,
                        MessageBody=json.dumps(message),
                        DelaySeconds=1,
                    )
        except:
            console.exception()
    
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


if __name__ == '__main__':
    startTime = time()
    config = Config()
    processes = []
    
    console = Console()
    driverManager = DriverManager(console)
    client = boto3.client('sqs')
    userManager = UserManager(console)
    userAgentManager = UserAgentManager()
    proxyManagerListener = ProxyManager(proxyFile=PROXY_FILE_LISTENER)
    proxyManagerRegister = ProxyManager(proxyFile=PROXY_FILE_REGISTER)
    lock = Lock()

    users = []

    for index in range(config.REGISTER_BATCH_COUNT):
        users.append(userManager.createRandomUser(
            proxy=proxyManagerListener.getRandomProxy(),
            userAgent=userAgentManager.getRandomUserAgent(),
            application='SP'
        ))
    shutdownEvent = Event()
    client = boto3.client('sqs')
    while len(users) or len(processes):
        try:
            sleep(2)
            if len(users) and (len(processes) < config.MAX_REGISTER_PROCESS):
                user = users.pop()
                context = {
                    'driverManager': driverManager,
                    'console': console,
                    'user': user,
                    'playlist': config.PLAYLIST,
                    'lock': lock,
                    'queueUrl': config.SQS_ENDPOINT,
                    'proxy': proxyManagerRegister.getRandomProxy(),
                    'shutdownEvent': shutdownEvent
                }
                p = Process(target=runner, args=(context,))
                processes.append(p)
                p.start()
                
            leftProcesses = []
            for p2 in processes:
                if p2.is_alive():
                    leftProcesses.append(p2)
            processes = leftProcesses

            response = client.get_queue_attributes(
                QueueUrl= config.SQS_ENDPOINT,
                AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
            )
            showStats({
                    'totalProcess': len(processes),
                    'queueAttributes': response['Attributes'],
                    'queueUrl': config.SQS_ENDPOINT,
                    'startTime': startTime,
                    'elapsedTime': str(timedelta(seconds=round(time() - startTime)))
                })
    
        except KeyboardInterrupt:
            shutdown()
            break
        except:
            print(traceback.format_exc())
            break





    
