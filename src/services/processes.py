
from src.services.httpserver import StatsProvider
from psutil import Process
from time import sleep
from src.services.console import Console
from src.services.observer import Subject
from multiprocessing import Array, Event, synchronize
from os import get_terminal_size
from sys import stdout
from time import time
from datetime import timedelta, datetime
from colorama import Fore

VENOM_VERSION = '1.0.7'

class ProcessProvider:
    def getStats(self) -> Array:
        pass

    def getNewProcess(self, freeSlot: int) -> Process:
        pass
    
    def getConsoleLines(self, width:int, height:int):
        pass


class ProcessManager(Subject, StatsProvider):
    EVENT_TIC = 'tic'
    STAT_PROCESS_COUNT = 0
    def __init__(self,
        serverId: str,
        userDir: str,
        console: Console, 
        processProvider: ProcessProvider,
        maxProcess: int,
        spawnInterval = 0.5,
        showInfo = False,
        shutdownEvent: synchronize.Event = Event(),
        stopWhenNoProcess: bool = False
    ) -> None:
        Subject.__init__(self)
        StatsProvider.__init__(self, 'manager')
        self.serverId = serverId
        self.userDir = userDir
        self.console = console
        self.maxProcess = maxProcess
        self.spawnInterval = spawnInterval
        self.processProvider: ProcessProvider = processProvider
        self.shutdownEvent = shutdownEvent
        self.startTime = time()
        self.processes = []
        self.terminalInfo = showInfo 
        self.stopWhenNoProcess = stopWhenNoProcess
        self.stats = Array('i', 1)
        self.stats[ProcessManager.STAT_PROCESS_COUNT] = 0
    

    def showInfo(self):
        width, height = get_terminal_size()
        elapsedTime = str(timedelta(seconds=round(time() - self.startTime)))
        lines = []
        separator = '-' * width
        lines.append(Fore.YELLOW + 'Venom v' + VENOM_VERSION)
        lines.append(Fore.BLUE + separator)
        lines.append(Fore.WHITE + 'Elapsed time  : %s' % (Fore.GREEN + elapsedTime))
        lines.append(Fore.WHITE + 'Total process : %3d / %3d     spawn: %.1fs' % (len(self.processes), self.maxProcess, self.spawnInterval))
        lines.append(Fore.BLUE + separator)
        lines += self.systemStats.getConsoleLines(width, height)
        lines.append(Fore.BLUE + separator)
        lines += self.processProvider.getConsoleLines(width, height)
        lines.append(Fore.BLUE + separator)
        self.console.clearScreen()
        index = 1
        for line in lines:
            self.console.printAt(1, index, line)
            index += 1
        stdout.write('\n')
        stdout.flush()  
    
    def getStats(self):
        return {
            'serverId': self.serverId,
            'maxProcess': self.maxProcess,
            'processCount': self.stats[ProcessManager.STAT_PROCESS_COUNT],
            'spawnInterval': self.spawnInterval,
            'startTime': str(datetime.fromtimestamp(self.startTime)),
            'elapsedTime': str(timedelta(seconds=round(time() - self.startTime)))
        }

    def stop(self):
        self.shutdownEvent.set()

    def start(self):
        waitStartProcess = 0
        
        while True:
            try:
                sleep(self.spawnInterval)
                freeslot = self.maxProcess - len(self.processes)

                if freeslot and (not self.shutdownEvent.is_set()) and waitStartProcess < time():
                    waitStartProcess = 0
                    try:
                        p = self.processProvider.getNewProcess(freeSlot=freeslot)
                        if p:
                            p.start()
                            self.processes.append(p)
                        else:
                            #Here we wait 10 sec before asking for a new process
                            waitStartProcess = time() + 10
                    except:
                        self.console.exception()    
                
                leftProcesses = []
                for p in self.processes:
                    if p.is_alive():
                        leftProcesses.append(p)
                    else:
                        p.join()
                self.processes = leftProcesses
                self.stats[ProcessManager.STAT_PROCESS_COUNT] = len(self.processes)
                if (len(self.processes) == 0):
                    if self.shutdownEvent.is_set():
                        break
                    if self.stopWhenNoProcess:
                        break        
                self.trigger(ProcessManager.EVENT_TIC)
                if self.terminalInfo:
                    self.showInfo()
            except:
                self.console.exception()

        