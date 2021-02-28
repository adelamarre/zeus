
from multiprocessing import Array, Event, Lock
from src.services.config import Config
from src.services.console import Console
from src.application.spotify.listener import Listener, ListenerContext, TaskContext
from src.services.drivers import DriverManager
from src.services.proxies import ProxyManager, PROXY_FILE_LISTENER
from time import sleep
from sp-listener import runner



if __name__ == '__main__':
    threadsCount = Array('i', 1)
    messagesCount = Array('i', 1)
    console = Console()
    config = Config()
    dm = DriverManager(console, Event())
    lock = Lock()
    config.LISTENER_MAX_PROCESS = 1
    config.LISTENER_MAX_THREAD = 1
    config.LISTENER_SPAWN_INTERVAL = 1
    shutdownEvent = Event()

    lpc = ListenerContext(
        messagesCount=messagesCount,
        threadsCount=threadsCount,
        channel=0,
        config = config,
        maxThread=1,
        shutdownEvent=shutdownEvent,
        console=console,
        lock=lock,
        vnc=True,
        headless=False,
        batchId= 1
    )

    lp = Listener(lpc)
    lp.start()
    
    while lp.is_alive():
        try:
            sleep(1)
        except KeyboardInterrupt:
            shutdownEvent.set()
        except:
            console.exception()
