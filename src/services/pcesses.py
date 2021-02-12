



class ProcessManager:
    def __init__(self) -> None:
        pass

    def addTask(self, runner, timeout, **arguments):
        self.tasks.put({
            'id': self.taskCount,
            'runner': runner,
            'arguments': arguments,
            'timeout': timeout
        })
        self.taskCount += 1