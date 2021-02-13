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
from os import environ
from traceback import format_exc
from shutil import rmtree

def runner(context):

    
    environ["DISPLAY"] = ":0"
    driverManager = context['driverManager']
    user = context['user']
    console = context['console']
    playlist = context['playlist']
    queueUrl = context['queueUrl']
    receiptHandle = context['receiptHandle']
    shutdownEvent = context['shutdownEvent']
    
    pid = current_process().pid
    
    try: 
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

    config = Config()
    processes = []
    console = Console()
    driverManager = DriverManager(console)
    client = boto3.client('sqs')
    shutdownEvent = Event()
    lock = Event()
    while True:
        try:
            sleep(2)
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
                        sleep(2)

            leftProcesses = []
            for p in processes:
                if p.is_alive():
                    leftProcesses.append(p)
            processes = leftProcesses
        except KeyboardInterrupt:
            shutdown()
            break
        except:
            print(format_exc())
            break




    
