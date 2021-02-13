# https://pythonspeed.com/articles/python-multiprocessing/ !!!top
from multiprocessing import Lock, set_start_method, current_process, Process
import multiprocessing
from platform import win32_edition
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
import os
import json
from time import sleep


def runner(context):
    os.environ["DISPLAY"] = ":0"
    driverManager = context['driverManager']
    user = context['user']
    console = context['console']
    playlist = context['playlist']
    queueUrl = context['queueUrl']

    pid = current_process().pid
    try: 
        print('Start runner %s' % pid)
        driver = driverManager.getDriver(
            type='chrome',
            uid=pid,
            user=user
        )
        if not driver:
            return
    except:
        console.error('Unavailale webdriver: %s' % format_exc())
    else:
        try:
            spotify = Spotify.Adapter(driver, console)
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


def shutdown(processes):
    print('Shutdown, please wait...')
    for p in processes:
        if p.is_alive():
            p.join()
    driverManager.purge()


if __name__ == '__main__':
    #mp = multiprocessing.get_context(method="spawn")
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

    while len(users) or len(processes):
        try:
            sleep(1)
            if len(users) and (len(processes) < config.MAX_REGISTER_PROCESS):
                user = users.pop()
                context = {
                    'driverManager': driverManager,
                    'console': console,
                    'user': user,
                    'playlist': config.PLAYLIST,
                    'lock': lock,
                    'queueUrl': config.SQS_URL
                }
                p = Process(target=runner, args=(context,))
                processes.append(p)
                p.start()

            leftProcesses = []
            for p2 in processes:
                if p2.is_alive():
                    leftProcesses.append(p2)
            processes = leftProcesses
        except KeyboardInterrupt:
            shutdown(processes)
            break
        except:
            print(traceback.format_exc())
            break





    
