# https://pythonspeed.com/articles/python-multiprocessing/ !!!top
from multiprocessing import Lock, current_process, Process, Event
from src.services.stats import Stats
from src.services.console import Console
from src.services.drivers import DriverManager
from src.services.users import UserManager
from src.services.userAgents import UserAgentManager
from src.services.proxies import PROXY_FILE_LISTENER, PROXY_FILE_REGISTER, ProxyManager
from src.application.spotify.register import runner
import boto3
from src.services.config import Config
from os import get_terminal_size
from time import sleep
from xvfbwrapper import Xvfb
from colorama import Fore, Back, Style
from sys import stdout
from time import time
from datetime import timedelta
from gc import collect

def showStats(data, stats: Stats):
    width, height = get_terminal_size()
    console.clearScreen()
    separator = '_' * width
    lines = []
    lines.append(Fore.YELLOW + 'ZEUS LISTENER SERVICE STATS')
    lines.append(Fore.WHITE + 'Browser: ' + Fore.GREEN + data['browser'])
    lines.append(Fore.WHITE + 'Driver : ' + Fore.GREEN + data['driver'])
    lines.append('')
    lines += stats.getConsoleLines(width)
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
    driverVersion = driverManager.getDriverVersion('chrome')
    browserVersion = driverManager.getBrowserVersion('chrome')
    client = boto3.client('sqs')
    userManager = UserManager(console)
    userAgentManager = UserAgentManager()
    proxyManagerListener = ProxyManager(proxyFile=PROXY_FILE_LISTENER)
    proxyManagerRegister = ProxyManager(proxyFile=PROXY_FILE_REGISTER)
    lock = Lock()
    stats = Stats()

    users = []

    for index in range(config.REGISTER_BATCH_COUNT):
        users.append(userManager.createRandomUser(
            proxy=proxyManagerListener.getRandomProxy(),
            userAgent=userAgentManager.getRandomUserAgent(),
            application='SP'
        ))
    shutdownEvent = Event()
    client = boto3.client('sqs')
    lastQueuePolling = 0.0
    while len(users) or len(processes):
        try:
            sleep(0.5)
            if len(users) and (len(processes) < config.REGISTER_MAX_PROCESS):
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
                else:
                    del p2
                    
            processes = leftProcesses
            del leftProcesses

            if (not lastQueuePolling or ((time() - lastQueuePolling) > 2.0)): 
                response = client.get_queue_attributes(
                    QueueUrl= config.SQS_ENDPOINT,
                    AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
                )

            showStats({
                    'totalProcess': len(processes),
                    'queueAttributes': response['Attributes'],
                    'queueUrl': config.SQS_ENDPOINT,
                    'startTime': startTime,
                    'elapsedTime': str(timedelta(seconds=round(time() - startTime))),
                    'browser': browserVersion,
                    'driver': driverVersion,
                }, stats)
            collect()
        except KeyboardInterrupt:
            shutdown()
            break
        except:
            console.exception()
            break
    driverManager.purge()





    
