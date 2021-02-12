
import json
import os

class Config(object):
    def __init__(self, configFilePath = (os.path.dirname(__file__) or '.') + '/../../config.json'):
        self.SQS_URL = ''
        print('Config file: %s' % configFilePath)
        with open(configFilePath, 'r') as f:
            self.__dict__ = json.load(f)