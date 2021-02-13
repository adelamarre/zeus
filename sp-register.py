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

def runner(user, playlist, proxyListener):

    
    
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
            user['proxy'] = proxyListener
            message = {
                'user': user,
                'playlist': playlist
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
    
    for index in range(config.REGISTER_BATCH_COUNT):
        try:
            sleep(1)
            if len(processes) < config.MAX_REGISTER_PROCESS:
                user = userManager.createRandomUser(
                    proxies=proxyManagerRegister.getRandomProxy(),
                    userAgent=userAgentManager.getRandomUserAgent(),
                    application='SP'
                )
                p = Process(target=runner, args=(user, config.PLAYLIST, proxyManagerListener.getRandomProxy()))
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





    
