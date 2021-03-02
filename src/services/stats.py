from src.services.httpserver import StatsProvider
from threading import Thread
from colorama import Fore
from psutil import cpu_count
import psutil


class Stats(StatsProvider):
    def __init__(self) -> None:
        StatsProvider.__init__(self, 'system')
        self.cpuCountP = cpu_count(logical=False)
        self.cpuCountL = cpu_count(logical=True)
        self.bTog = 1024*1024*1024

    def couldStartProcess(self):
        memstat = psutil.virtual_memory()
        stats = [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]
        return (stats[0] < 95.0) and (memstat.percent < 90.0)
    
    def getStats(self):
        memstat = psutil.virtual_memory()
        percents = psutil.cpu_percent(interval=None)
        
        return {
            'memTotal': memstat.total/ self.bTog,
            'memAvailable': memstat.available/self.bTog,
            'memActive': memstat.percent,
            'cpuCountP': self.cpuCountP,
            'cpuCountL': self.cpuCountL,
            'cpuPercentAvg': percents,
        }

    def getConsoleLines(self, width, height):
        lines = []
        memstat = psutil.virtual_memory()
        memtotal = memstat.total/ self.bTog
        memavailable = memstat.available/self.bTog
        load = psutil.cpu_percent(interval=None)
        memactive = memstat.percent
        def floatValue(value):
            return Fore.GREEN + '%3.2f' % value + Fore.RESET
        def intValue(value):
            return Fore.GREEN + '%3d' % value + Fore.RESET
        def loadValue(value):
            if value > 96.0:
                return Fore.RED + '%3.2f' % value + Fore.RESET
            elif value > 70.0:
                return Fore.YELLOW + '%3.2f' % value + Fore.RESET
            else:
                return Fore.GREEN + '%3.2f' % value + Fore.RESET
        
        lines.append(Fore.WHITE + 'Cpu    : Count %s/%s, load %s%%' % (intValue(self.cpuCountP), intValue(self.cpuCountL), loadValue(load)))
        lines.append(Fore.WHITE + 'Memory : Total    %s Go,  Available %s Go, Used %s%%' % (floatValue(memtotal), floatValue(memavailable), floatValue(memactive)))
        return lines
