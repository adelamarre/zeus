# https://pythonspeed.com/articles/python-multiprocessing/ !!!top
from multiprocessing import set_start_method, current_process, Process
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
set_start_method("spawn")
import json
from time import sleep

console = Console()
driverManager = DriverManager()
client = boto3.client('sqs')
userManager = UserManager()
userAgentManager = UserAgentManager()
proxyManagerListener = ProxyManager(proxyFile=PROXY_FILE_LISTENER)
proxyManagerRegister = ProxyManager(proxyFile=PROXY_FILE_REGISTER)

def runner():

    
    user = userManager.createRandomUser(
        proxy=proxyManagerRegister.getRandomProxy(),
        userAgent=userAgentManager.getRandomUserAgent(),
        application='SP'
    )
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
        if spotify.register(user):
            message = {
                'user': user,
                'playlist': config.PLAY_LIST
            }
            client.send_message(
                QueueUrl=config.SQS_URL,
                MessageBody=json.dumps(message),
                DelaySeconds=1,
            )


def shutdown(processes):
    print('Shutdown, please wait...')
    for p in processes:
        if p.is_alive():
            p.join()
    driverManager.purge()


if __name__ == '__main__':

    config = Config()
    processes = []
    
    while True:
        try:
            sleep(1)
            if len(processes) < config.MAX_REGISTER_PROCESS:
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
        except KeyboardInterrupt:
            shutdown(processes)
            break
        except:
            print(traceback.format_exc())





    
