


from multiprocessing import synchronize


class AbstractScenario:
    def __init__(self, args, userDir: str, shutdownEvent: synchronize.Event):
        self.args = args
        self.userDir = userDir
        self.shutdownEvent = shutdownEvent
        

    def start(self):
        pass