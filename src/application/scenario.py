


from multiprocessing import synchronize


class AbstractScenario:
    def __init__(self, args, userDir: str, shutdownEvent: synchronize.Event, configFile: str):
        self.args = args
        self.userDir = userDir
        self.shutdownEvent = shutdownEvent
        self.configFile = configFile
        

    def start(self):
        pass