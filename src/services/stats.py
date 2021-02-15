from threading import Thread
from colorama import Fore
from psutil import cpu_count
import psutil


class Stats:
    def __init__(self) -> None:
        self.cpuCountP = cpu_count(logical=False)
        self.cpuCountL = cpu_count(logical=True)
        self.bTog = 1024*1024*1024

    def couldStartProcess(self):
        memstat = psutil.virtual_memory()
        stats = [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]
        return (stats[0] < 95.0) and (memstat.percent < 90.0)

    def getConsoleLines(self, width):
        lines = []
        memstat = psutil.virtual_memory()
        #cpustat = psutil.cpu_freq()
        separator = '_' * width
        
        memtotal = memstat.total/ self.bTog
        memavailable = memstat.available/self.bTog
        load = stats = [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]
        #memactive = memstat.active/self.bTog
        memactive = memstat.percent
        def floatValue(value):
            return Fore.GREEN + '%3.2f' % value + Fore.RESET
        def intValue(value):
            return Fore.GREEN + '%3d' % value + Fore.RESET
        def loadValue(value):
            if value > 100.0:
                return Fore.RED + '%3.2f' % value + Fore.RESET
            else:
                return Fore.GREEN + '%3.2f' % value + Fore.RESET
            

        title = 'System' + ('-' * (width - 7))
        separator = '_' * width
        lines.append(Fore.BLUE + 'System')
        lines.append(Fore.BLUE + separator)
        lines.append(Fore.WHITE + 'Cpu    : Count %s/%s, load %s%%' % (intValue(self.cpuCountP), intValue(self.cpuCountL), loadValue(load[0])))
        lines.append(Fore.WHITE + 'Memory : Total    %s Go,  Available %s Go, Used %s%%' % (floatValue(memtotal), floatValue(memavailable), floatValue(memactive)))
        lines.append('\n')
        return lines
