# https://pythonspeed.com/articles/python-multiprocessing/ !!!top
from multiprocessing import set_start_method, current_process, Process
from src.services.console import Console
from src.services.drivers import DriverManager
from src.application.spotify import Spotify
import boto3
from traceback import format_exc
from src.services.config import Config
set_start_method("spawn")
import json
from time import sleep

console = Console()
driverManager = DriverManager()
client = boto3.client('sqs')

def runner(message):

    body = message = json.loads(message.body)
    user = body.user
    playlist = body.playlist
    try: 
        driver = driverManager.getDriver(
            type='chrome',
            uid=current_process(),
            user=user
        )
    except:
        console.error('Unavailale webdriver: %s' % format_exc())
    else:
        spotify = Spotify.Adapter(driver, console)
        if spotify.login(user['email'], user['password']):
            if spotify.playPlaylist(playlist, 90, 110):
                client.delete_message(
                    QueueUrl=config.SQS_URL,
                    ReceiptHandle=message.ReceiptHandle
                )


if __name__ == '__main__':

    config = Config()
    processes = []
    
    while True:
        sleep(1)
        if len(processes) < config.MAX_LISTENER_PROCESS:
            freeProcess = config.MAX_PROCESS - len(processes)
            response = client.receive_message(
                QueueUrl=config.SQS_URL,
                MaxNumberOfMessages=freeProcess,
                VisibilityTimeout=600,
                WaitTimeSeconds=2,
            )
            if len(response.Messages):
                for message in response.Messages:
                    p = Process(target=runner, args=(message))
                    processes.append(p)
                    p.start()

        leftProcesses = []
        for p in processes:
            if p.is_alive():
                leftProcesses.append(p)
        processes = leftProcesses





    
