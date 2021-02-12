

from threading import Event, Lock, Thread
from src.services.console import Console
from .queue import TasksQueue
from .drivers import DriverManager
from time import sleep
from colorama import Fore, Back, Style
import time
import queue # imported for using queue.Empty exception
import sys
import random
import os
import traceback
import math
import datetime
from .config import Config
from .tasks import TaskContext


# @see https://www.cloudcity.io/blog/2019/02/27/things-i-wish-they-told-me-about-multiprocessing-in-python/
# @see https://pymotw.com/2/multiprocessing/communication.html
# @see https://github.com/PamelaM/mptools


class Worker(Thread):
    EMPTY = -1
    NOT_CREATED = 0
    RUNNING = 1
    WORKING = 2
    IDLE = 3
    ERROR = 4
    STOPPED = 5

    def __init__(self, workerId: int, config: Config, tasks: TasksQueue, shutdownEvent: Event, locks, console: Console, states, stats, driverManager: DriverManager):
        super(Worker, self).__init__()
        self.id = workerId
        self.tasks = tasks
        self.shutdownEvent = shutdownEvent
        self.locks = locks
        self.console = console
        self.states = states
        self.config = config
        self.setState(Worker.RUNNING, 'Started')
        
        self.stats = stats
        self.taskCount = 0
        self.taskDuration = 0
        self.timeoutCount = 0
        self.errorCount = 0
        self.driverManager = driverManager

    def run(self):
        context = TaskContext(self.locks, self.console, self.config, self.setTaskState, self.shutdownEvent, self.driverManager)
        
        while not self.shutdownEvent.is_set():
            try:
                self.setState(Worker.IDLE, 'Looking for Task...')
                with self.locks['tasks']:
                    task = self.tasks.get(block=True, timeout=0.05)
                taskId = task['id']
                
                self.console.log('Worker #%d start process task #%d...' % (self.id, taskId), True, True)
                try:
                    sleep(0.5)
                    self.setState(Worker.WORKING, 'Prepare Task #%d' % taskId)
                    self.console.log('Running task #%d' % taskId)
                    if 'timeout' in task:
                        timeout = task['timeout']
                    else:
                        timeout = 180

                    runner = task['runner']
                    arguments = task['arguments']
                    p = Thread(target=runner, args=(taskId, context), kwargs=(arguments))
                    startTime = time.time()
                    try:
                        p.start()
                        startTime = time.time()
                        self.setState(Worker.WORKING, 'Start task #%d' % taskId)
                        while True:
                            sleep(1)
                            if self.shutdownEvent.is_set():
                                self.console.notice('Worker #%d shutdown...' % (self.id))
                                try: 
                                    p.terminate()
                                except:
                                    pass
                                break
                            if p.is_alive() == False:
                                try:
                                    p.close()
                                except:
                                    pass
                                self.console.success('Worker #%d Task #%d succeded.' % (self.id, taskId))
                                break
                            if (time.time() - startTime) > timeout:
                                self.timeoutCount += 1
                                self.console.notice('Worker #%d Task #%d timeout...' % (self.id, taskId))
                                try: 
                                    p.terminate()
                                except:
                                    pass
                                break
                    except:
                        self.errorCount += 1
                        self.console.warning('Worker #%d Task #%d error: %s' % (self.id, taskId, traceback.format_exc()))
                    
                    self.taskCount += 1
                    self.taskDuration += time.time() - startTime
                    self.updateStats()
                    self.console.log('Task #%d Finished' % task['id'])
                except:
                    self.setState(Worker.ERROR, 'Exception while running task #%d' % taskId)
                    self.console.notice('Worker #%d exception: %s' % (self.id, traceback.format_exc()))
            except queue.Empty:
                self.setState(Worker.RUNNING, 'No more tasks, terminate')
                break
            except:
                self.console.warning('Worker #%d Error:' % self.id, sys.exc_info())
                break
           
                
            #self.tasks.task_done()
        
        self.console.log('Worker #%d finish. Tasks processed : %d' % (self.id, self.stats[self.id]['taskCount']))
        self.setState(Worker.STOPPED, 'Terminated')
        return True
    
    def updateStats(self):
        with self.locks['stats']:
            self.stats[self.id] = {
                'taskDuration': self.taskDuration,
                'taskCount': self.taskCount,
                'errorCount': self.errorCount,
                'timeoutCount': self.timeoutCount
            }

    def setTaskState(self, message):
        self.console.log('Task state change: %s' % message)
        self.setState(Worker.WORKING, message)

    def setState(self, state, message = ''):
        with self.locks['states']:
            self.states[self.id] = {
                'state': state,
                'message': message,
            }

class WorkerManager:
    def __init__(self, shutDownEvent, console: Console, config: Config):
        self.shutdownEvent = shutDownEvent
        self.config = config
        self.console = console
        
        #procCount = multiprocessing.cpu_count()
        
        self.tasks = TasksQueue()
        self.nbrProcess = config.PROCESS_COUNT
        self.taskCount = 0
        self.processes = []
        
        self.states = []
        self.stats = []
        
        self.startTime = 0.0
        self.locks = {
            'tasks': Lock(),
            'stats': Lock(),
            'states': Lock(),
            'accounts': Lock(),
        }
        
        
    def addTask(self, runner, timeout, **arguments):
        self.tasks.put({
            'id': self.taskCount,
            'runner': runner,
            'arguments': arguments,
            'timeout': timeout
        })
        self.taskCount += 1

    
    def start(self):
        
        processId = 0

        if self.taskCount < self.nbrProcess:
            self.nbrProcess = self.taskCount
        
        for s in range(self.nbrProcess):
            self.stats.append({
                'taskCount': 0,
                'taskDuration': 0,
                'timeoutCount': 0,
                'errorCount': 0,
            })
            self.states.append({
                'state': Worker.NOT_CREATED,
                'message': 'Not created'
            })

        self.startTime = time.time()
        lastStatUpdate = time.time()

        
        driverManager = DriverManager(self.console)
        
        for w in range(self.nbrProcess):
            if self.shutdownEvent.is_set():
                break

            sleep(self.config.PROCESS_START_INTERVAL)

            p = Worker(processId, self.config, self.tasks, self.shutdownEvent, self.locks, self.console, self.states, self.stats, driverManager)
            self.processes.append(p)
            p.start()
            processId += 1

            if (time.time() - lastStatUpdate) > 1:
                lastStatUpdate = time.time()        
                self.showStats()
        
        while self.processes:
            leftProcess = []
            sleep(5)
            for p in self.processes:
                try:
                    if p.is_alive():
                        if self.shutdownEvent.is_set():
                            #p.terminate()
                            pass
                        else:
                            leftProcess.append(p)
                except:
                    self.console.warning('Main process error: %s\n' % traceback.format_exc())
                    pass        
            
            self.processes =  leftProcess
            self.showStats()
        driverManager.purge()


    def showStats(self):
      
        if self.shutdownEvent.is_set():
            return
            
        self.console.clearScreen()
        width, height = os.get_terminal_size()           
        
        try:
            startWorkerList = 5
            nbrCol = math.ceil(self.nbrProcess / (height-startWorkerList))
            nbrRow = math.ceil(self.nbrProcess / nbrCol)
            colWidth = round(width/nbrCol)
            currentProcessCount = len(self.processes)
            currentTaskRemaining = self.tasks.qsize()

            startedSince = str(datetime.timedelta(seconds=round(time.time() - self.startTime)))
            totaltask = 0
            totalTimeout = 0
            totalError = 0
            totalTime = 0
            
            for s in range(self.nbrProcess):
                with self.locks['stats']:
                    stat = self.stats[s]
                totaltask += stat['taskCount']
                totalTimeout += stat['timeoutCount']
                totalError += stat['errorCount']
                totalTime += stat['taskDuration']
            

            if totaltask > 0:
                averageTaskDuration = str(datetime.timedelta(seconds=round(totalTime / totaltask)))
            else:
                averageTaskDuration = 'n/a'

            separator = '_' * width
            self.console.printAt(1 ,1, Fore.BLUE + separator)
            self.console.printAt(1, 2, Fore.WHITE + 'Started since: %s,  Average task duration: %s' % (startedSince, averageTaskDuration))   
            self.console.printAt(1, 3, Fore.WHITE + 'Alive process: %d,  Tasks remaining: %d' % (currentProcessCount, currentTaskRemaining))   
            self.console.printAt(1, 3, Fore.WHITE + 'Total completed tasks: %d,  (timeout: %d, error: %d)' % (totaltask, totalTimeout, totalError))   
            self.console.printAt(1 ,4, Fore.BLUE + separator)
            
            stateColor = {
                Worker.EMPTY: Fore.WHITE,
                Worker.NOT_CREATED: Fore.WHITE,
                Worker.RUNNING: Fore.GREEN,
                Worker.WORKING: Fore.CYAN,
                Worker.IDLE: Fore.YELLOW,
                Worker.ERROR: Fore.RED,
                Worker.STOPPED: Fore.WHITE,

            }
            
            for r in range(nbrRow):
                for c in range(nbrCol):
                    pid = (r * nbrCol) + c
                    x = (c * colWidth) + 1
                    try:
                        with self.locks['states']:
                            state = self.states[pid]
                    except:
                        state = {
                            'state': Worker.EMPTY,
                            'message': '_'
                        }

                    self.console.printAt(x, r + startWorkerList, "[%3d] %s%s" % (pid, stateColor.get(state['state'], Fore.BLUE), state['message']))
            sys.stdout.write('\n')
            sys.stdout.flush()   
            

        except:
            self.console.warning(traceback.print_exc())
        #for p in self.processes:
        #    p.join()
