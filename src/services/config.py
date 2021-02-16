
import json
import os

class Config(object):
    def __init__(self, configFilePath = (os.path.dirname(__file__) or '.') + '/../../config.json'):
        self.SQS_URL = '',
        self.LISTENER_OVERIDE_PLAYLIST = None
        self.LISTENER_OVERIDE_PROXY = False
        self.LISTENER_MAX_PROCESS = -1
        self.LISTENER_MAX_THREAD = 100
        self.LISTENER_SPAWN_INTERVAL = 1
        self.REGISTER_BATCH_COUNT = 1000
        self.REGISTER_MAX_PROCESS = 100
        print('Config file: %s' % configFilePath)
        with open(configFilePath, 'r') as f:
            self.__dict__ = json.load(f)