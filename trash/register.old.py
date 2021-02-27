

from shutil import rmtree
from multiprocessing import current_process
from traceback import format_exc
from src.application.spotify import Spotify
from xvfbwrapper import Xvfb
from boto3 import client
from src.services.console import Console
from json import dumps

def runner(context):  
    driverManager = context['driverManager']
    user = context['user']
    console: Console= context['console']
    playlist = context['playlist']
    queueUrl = context['queueUrl']
    proxy = context['proxy']
    shutdownEvent = context['shutdownEvent']
    pid = current_process().pid
    
    try:
        vdisplay = Xvfb(width=1280, height=1024, colordepth=24, tempdir=None, noreset='+render')
        vdisplay.start() 
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
                    client = client('sqs')
                    client.send_message(
                        QueueUrl=queueUrl,
                        MessageBody=dumps(message),
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
