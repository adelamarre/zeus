
import os
import random
import sys
from ...services.workers import TaskContext 
from time import sleep




def runner(uid, context: TaskContext):
    #log('Runner %d start...' % uid)
    s = random.randint(5, 13)
    context.setTaskState('Sleeping %d sec' % s)
    #log('Runner will wait %d sec' % s)
    sleep(s)
    #log('Runner %d finish...' % uid)

class Scenario:
    def __init__(self, console):
        self.console = console

    def init(self):
        try:
            self.nbrTests = int(input('How much test would you like to do ?'))
        except:
            return False
        return True

    def getTasks(self):
        tasks = []    
        for index in range(self.nbrTests):
            tasks.append({
                'timeout': 10
            })
        return tasks
        
    def getRunner(self):
        return runner
    
    def finish(self):
        self.console.success('Scenario finish gracefully')
        pass

