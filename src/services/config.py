
import json
import os

class Config(object):
    def __init__(self, configFilePath = None):
        self.SQS_URL = '',
        self.SQS_ENDPOINT = '',
        self.LISTENER_OVERIDE_PLAYLIST = None
        self.LISTENER_OVERIDE_PROXY = False
        self.LISTENER_MAX_PROCESS = -1
        self.LISTENER_MAX_THREAD = 100
        self.LISTENER_SPAWN_INTERVAL = 1
        self.REGISTER_BATCH_COUNT = 1000
        self.REGISTER_MAX_PROCESS = -1
        self.REGISTER_MAX_THREAD = 16 * 10
        
        if configFilePath:
            try:
                with open(configFilePath, 'r') as f:
                    self.__dict__ = json.load(f)
            except:
                pass