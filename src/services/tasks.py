from .config import Config
from .console import Console
from multiprocessing import Event
from .drivers import DriverManager

class TaskContext:
    def __init__(self, locks, console: Console, config: Config, setTaskState, shutdownEvent: Event, driverManager: DriverManager):
        self.locks = locks
        self.console = console
        self.setTaskState = setTaskState
        self.shutdownEvent = shutdownEvent
        self.driverManager = driverManager
        self.config = config
