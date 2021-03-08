
from src.services.config import Config
from configparser import ConfigParser
from os import cpu_count, path
from src.services.questions import Question
import sys

class ListenerConfig(Config):
    def __init__(self, configFile: str) -> None:
        super().__init__(configFile, 'LISTENER')

    SERVER_ID = 'server_id'
    ACCOUNT_SQS_ENDPOINT = 'account_sqs_endpoint'
    COLLECTOR_SQS_ENDPOINT = 'collector_sqs_endpoint'
    MAX_PROCESS= 'max_process'
    SPAWN_INTERVAL = 'spawn_interval'
    SECRET = 'secret'

    
    def _parse(self, configData):
        return {
            ListenerConfig.SERVER_ID:               configData[ListenerConfig.SERVER_ID].strip(),
            ListenerConfig.ACCOUNT_SQS_ENDPOINT:    configData[ListenerConfig.ACCOUNT_SQS_ENDPOINT].strip(),
            ListenerConfig.COLLECTOR_SQS_ENDPOINT:  configData[ListenerConfig.COLLECTOR_SQS_ENDPOINT].strip(),
            ListenerConfig.MAX_PROCESS:             int(configData[ListenerConfig.MAX_PROCESS]),
            ListenerConfig.SPAWN_INTERVAL:          float(configData[ListenerConfig.SPAWN_INTERVAL]),
            ListenerConfig.SECRET:                  configData[ListenerConfig.SECRET],
        }

    def check(self, data):
        if data is None:
            sys.exit('I can not continue without configuraton')
        for key in [
           ListenerConfig.ACCOUNT_SQS_ENDPOINT, 
           ListenerConfig.COLLECTOR_SQS_ENDPOINT, 
           ListenerConfig.SERVER_ID, 
           ListenerConfig.SECRET
        ]:
            self.assertNotEmpty(data, key)
        return data

    def createConfiguration(self, default: dict):
        if Question.yesNo('Listener configuration is missing. You want to create it now ?'):
            answer = Question.list([
                {
                    'type': 'input',
                    'name': ListenerConfig.SERVER_ID,
                    'message': 'What is the name of this server ?',
                    'default': default.get(ListenerConfig.SERVER_ID, ''),
                    'validate': Question.validateString
                },
                {
                    'type': 'input',
                    'name': ListenerConfig.ACCOUNT_SQS_ENDPOINT,
                    'message': 'Accounts Queue url ?',
                    'default': default.get(ListenerConfig.ACCOUNT_SQS_ENDPOINT, ''),
                    'validate': Question.validateUrl
                },
                {
                    'type': 'input',
                    'name': ListenerConfig.COLLECTOR_SQS_ENDPOINT,
                    'message': 'Statistics Queue url ?',
                    'default': default.get(ListenerConfig.COLLECTOR_SQS_ENDPOINT, ''),
                    'validate': Question.validateUrl
                },
                {
                    'type': 'input',
                    'name': ListenerConfig.MAX_PROCESS,
                    'message': 'Default process count ?',
                    'default': str(default.get(ListenerConfig.MAX_PROCESS, cpu_count())),
                    'filter': int,
                    'validate': Question.validateInteger
                },
                {
                    'type': 'input',
                    'name': ListenerConfig.SPAWN_INTERVAL,
                    'message': 'Default spawn interval ?',
                    'default': str(default.get(ListenerConfig.SPAWN_INTERVAL, 0.5)),
                    'filter': float,
                    'validate': Question.validateFloat
                },
                {
                    'type': 'password',
                    'name': ListenerConfig.SECRET,
                    'message': 'Set the password for stats server',
                    'filter': Question.filterMd5,
                },
                
            ])
            if not answer:
                return False
            if answer[ListenerConfig.SECRET] is None or len(answer[ListenerConfig.SECRET]) == 0:
                answer[ListenerConfig.SECRET] = default.get(ListenerConfig.SECRET, '')
            
            self.writeConfiguration({self.section: answer})
            return True

        return False
    