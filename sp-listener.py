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
from os import environ, get_terminal_size
from traceback import format_exc
from shutil import rmtree
from colorama import Fore, Back, Style
from sys import stdout
from xvfbwrapper import Xvfb

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
        vdisplay = Xvfb(width=1280, height=1024)
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

def showStats(data, queueUrl):
    width, height = get_terminal_size()
    console.clearScreen()
    separator = '_' * width
    lines = []
    lines.append(Fore.YELLOW + 'ZEUS LISTENER SERVICE STATS')
    lines.append('\n')
    lines.append(Fore.CYAN + 'Queue: %s:' % queueUrl)
    lines.append(Fore.BLUE + separator)
    lines.append(Fore.WHITE + 'Total process : %6d' % int(data['totalProcess']))
    lines.append(Fore.WHITE + 'Message read  : %6d' % int(data['totalMessageReceived']))
    lines.append(Fore.BLUE + separator)
    index = 1
    for line in lines:
        console.printAt(1, index, line)
        index += 1

    stdout.write('\n')
    stdout.flush()  


if __name__ == '__main__':

    config = Config()
    processes = []
    console = Console()
    driverManager = DriverManager(console)
    client = boto3.client('sqs')
    shutdownEvent = Event()
    lock = Event()
    totalMessageReceived = 0
    while True:
        try:
            sleep(0.5)
            if len(processes) < config.MAX_LISTENER_PROCESS:
                freeProcess = config.MAX_LISTENER_PROCESS - len(processes)
                if freeProcess > 10:
                    freeProcess = 10
                response = client.receive_message(
                    QueueUrl=config.SQS_URL,
                    MaxNumberOfMessages=freeProcess,
                    VisibilityTimeout=600,
                    WaitTimeSeconds=2,
                )
                messages = []
                if 'Messages' in response:
                    messages = response['Messages']
                totalMessageReceived += len(messages)
                if len(messages):
                    for message in messages:
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
                        p = Process(target=runner, args=(context,))
                        processes.append(p)
                        p.start()
                        showStats({
                            'totalProcess': len(processes),
                            'totalMessageReceived': totalMessageReceived
                        }, config.SQS_URL)
                        sleep(0.5)

            leftProcesses = []
            for p in processes:
                if p.is_alive():
                    leftProcesses.append(p)
            processes = leftProcesses
            showStats({
                'totalProcess': len(processes),
                'totalMessageReceived': totalMessageReceived
            }, config.SQS_URL)
        except KeyboardInterrupt:
            shutdown()
            break
        except:
            print(format_exc())
            break




    
