
import json
import os
from src.services.questions import Question
from configparser import ConfigParser
from os import path
from src.services.questions import Question
import os, subprocess, tempfile





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

    def getRegisterConfig(configFile, default: dict = {
        'maxProcess': 100,
        'spawnInterval': 0.5
    }):
        if not path.exists(configFile):
            if not Config.createRegisterConfiguration(configFile, default):
                return 
        config = ConfigParser()
        config.read(configFile)
        if 'REGISTER' in config.sections():
            configData = config['REGISTER']
            config = {
                'serverId':     configData.get('server_id', '').strip(),
                'sqsEndpoint':  configData.get('sqs_endpoint', '').strip(),
                'maxProcess':   configData.getint('max_process', default['maxProcess']),
                'spawnInterval':configData.getfloat('spawn_interval', default['spawnInterval'])
            }
            return config
        else:
            print('Bad configuration file format. Please check the file %s' % configFile)
  
    
    def createRegisterConfiguration(configFile, default: dict):
        if Question.yesNo('Config file is missing. You want to create it now ?'):
            answer = Question.list([
                {
                    'type': 'input',
                    'name': 'serverId',
                    'message': 'What is the name of this server ?',
                    'validate': Question.validateString
                },
                {
                    'type': 'input',
                    'name': 'sqsEndpoint',
                    'message': 'Queue url ?',
                    'validate': Question.validateUrl
                },
                {
                    'type': 'input',
                    'name': 'maxProcess',
                    'message': 'Default process count ?',
                    'default': str(default['maxProcess']),
                    'filter': int,
                    'validate': Question.validateInteger
                },
                {
                    'type': 'input',
                    'name': 'spawnInterval',
                    'message': 'Default spawn interval ?',
                    'default': str(default['spawnInterval']),
                    'filter': float,
                    'validate': Question.validateFloat
                },
            ])
            if not answer:
                return

            with open(configFile, 'w') as f:
                f.write(
"""
[REGISTER]
server_id=%s
sqs_endpoint=%s
max_process=%d
spawn_interval=%f
""" % (answer['serverId'],answer['sqsEndpoint'],answer['maxProcess'], answer['spawnInterval']))
            #cmd = os.environ.get('EDITOR', 'vi') + ' ' + configFile
            #subprocess.call(cmd, shell=True)
            return True

        return False