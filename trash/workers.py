

import multiprocessing
import threading
from ctypes import c_char_p

from src.services.drivers import DriverManager
from src.services.console import Console
from .queue import TasksQueue
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


# @see https://www.cloudcity.io/blog/2019/02/27/things-i-wish-they-told-me-about-multiprocessing-in-python/
# @see https://pymotw.com/2/multiprocessing/communication.html
# @see https://github.com/PamelaM/mptools


class Worker(multiprocessing.Process):
    EMPTY = -1
    NOT_CREATED = 0
    RUNNING = 1
    WORKING = 2
    IDLE = 3
    ERROR = 4
    STOPPED = 5

    def __init__(self, workerId: int, tasks: TasksQueue, shutdownEvent: multiprocessing.Event, console: Console, states, stats, dryRun: bool):
        super(Worker, self).__init__()
        self.id = workerId
        self.tasks = tasks
        self.shutdownEvent = shutdownEvent
        self.lock = lock
        self.console = console
        self.states = states
        self.setState(Worker.RUNNING, 'Started')
        self.dryRun = dryRun
        self.stats = stats
        self.taskCount = 0
        self.taskDuration = 0
        self.timeoutCount = 0
        self.errorCount = 0
        self.driverManager = DriverManager()
        self.locks = {
            'tasks': Lock(),
            'stats': Lock(),
            'states': Lock(),
            'accounts': Lock(),
        }

    def run(self):
        context = TaskContext(self.lock, self.console, self.setTaskState, self.dryRun, self.shutdownEvent, self.driverManager)
        
        while not self.shutdownEvent.is_set():
            try:
                self.setState(Worker.IDLE, 'Looking for Task...')
                task = self.tasks.get(block=True, timeout=0.05)
                taskId = task['id']
                
                self.console.log('Worker #%d start process task #%d...' % (self.id, taskId), True, True)
            except queue.Empty:
                self.setState(Worker.RUNNING, 'No more tasks, terminate')
                break
            except:
                self.console.warning('Worker #%d Error:' % self.id, sys.exc_info())
                break
            else:
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
                    p = Process(target=runner, args=(taskId, context), kwargs=(arguments))
                    startTime = time.time()
                    try:
                        p.start()
                        startTime = time.time()
                        self.setState(Worker.WORKING, 'Start task #%d' % taskId)
                        while True:
                            sleep(0.5)
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
                            #else:
                            #    log('Task #%d is alive since %02d sec, timeout is %02d' % (taskId,  (time.time() - startTime), timeout), True)
                        
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
            #self.tasks.task_done()
        
        self.console.log('Worker #%d finish. Tasks processed : %d' % (self.id, self.stats[self.id]['taskCount']))
        self.setState(Worker.STOPPED, 'Terminated')
        return True
    
    def updateStats(self):
        self.lock.acquire()
        self.stats[self.id] = {
            'taskDuration': self.taskDuration,
            'taskCount': self.taskCount,
            'errorCount': self.errorCount,
            'timeoutCount': self.timeoutCount
        }
        self.lock.release()

    def setTaskState(self, message):
        self.console.log('Task state change: %s' % message)
        self.setState(Worker.WORKING, message)

    def setState(self, state, message = ''):
        self.states[self.id] = {
            'state': state,
            'message': message,
        }

class WorkerManager:
    def __init__(self, shutDownEvent, lock, console: Console, nbrProcess=0, processStartInterval=3, dryRun=False):
        self.shutdownEvent = shutDownEvent
        self.processStartInterval = processStartInterval
        self.console = console
        self.lock = lock
        procCount = multiprocessing.cpu_count()
        if nbrProcess == 0:
            nbrProcess = procCount
        self.tasks = TasksQueue()
        self.nbrProcess = nbrProcess
        self.taskCount = 0
        self.processes = []
        manager = multiprocessing.Manager()
        self.states = manager.dict()
        self.stats = manager.dict()
        self.dryRun = dryRun
        self.startTime = 0.0
        
        console.log('Worker manager found %d cores' % procCount, True, True)
        
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
            self.stats[s] = {
                'taskCount': 0,
                'taskDuration': 0,
                'timeoutCount': 0,
                'errorCount': 0,
            }
            self.states[s] = {
                'state': Worker.NOT_CREATED,
                'message': 'Not created'
            }

        self.startTime = time.time()
        lastStatUpdate = time.time()
        for w in range(self.nbrProcess):
            if self.shutdownEvent.is_set():
                break

            sleep(self.processStartInterval)

            p = Worker(processId, self.tasks, self.shutdownEvent, self.console, self.states, self.stats, self.dryRun)
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
                            p.terminate()
                        else:
                            leftProcess.append(p)
                except:
                    self.console.warning('Main process error: %s\n' % traceback.print_exc())
                    pass        
            
            self.processes =  leftProcess
            self.showStats()


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
            self.lock.acquire()
            for s in range(self.nbrProcess):
                stat = self.stats[s]
                totaltask += stat['taskCount']
                totalTimeout += stat['timeoutCount']
                totalError += stat['errorCount']
                totalTime += stat['taskDuration']
            self.lock.release()

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
            self.lock.acquire()
            for r in range(nbrRow):
                for c in range(nbrCol):
                    pid = (r * nbrCol) + c
                    x = (c * colWidth)
                    if pid in self.states :
                        state = self.states[pid]
                    else:
                        state = {
                            'state': Worker.EMPTY,
                            'message': '_'
                        }

                    self.console.printAt(x, r + startWorkerList, "[%3d] %s%s" % (pid, stateColor.get(state['state'], Fore.BLUE), state['message']))
            sys.stdout.flush()   
            self.lock.release()

        except:
            self.console.warning(traceback.print_exc())
        #for p in self.processes:
        #    p.join()
