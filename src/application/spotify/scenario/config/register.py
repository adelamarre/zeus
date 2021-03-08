

import sys
from src.services.config import Config
from configparser import ConfigParser
from os import cpu_count, path
from src.services.questions import Question


class RegisterConfig(Config):
    def __init__(self, configFile: str) -> None:
        super().__init__(configFile, 'REGISTER')
    
    ACCOUNT_SQS_ENDPOINT = 'account_sqs_endpoint'
    COLLECTOR_SQS_ENDPOINT = 'collector_sqs_endpoint'
    MAX_PROCESS= 'max_process'
    SERVER_ID = 'server_id'
    SPAWN_INTERVAL = 'spawn_interval'
    


    def _parse(self, configData):
        return {
            RegisterConfig.SERVER_ID:               configData[RegisterConfig.SERVER_ID].strip(),
            RegisterConfig.ACCOUNT_SQS_ENDPOINT:    configData[RegisterConfig.ACCOUNT_SQS_ENDPOINT].strip(),
            RegisterConfig.COLLECTOR_SQS_ENDPOINT:  configData[RegisterConfig.COLLECTOR_SQS_ENDPOINT].strip(),
            RegisterConfig.MAX_PROCESS:             int(configData[RegisterConfig.MAX_PROCESS]),
            RegisterConfig.SPAWN_INTERVAL:          float(configData[RegisterConfig.SPAWN_INTERVAL])
        }

    def check(self, data):
        if not data:
            sys.exit('I can not continue without configuraton')
        
        for key in [
           RegisterConfig.ACCOUNT_SQS_ENDPOINT, 
           RegisterConfig.SERVER_ID, 
        ]:
            self.assertNotEmpty(data, key)
        return data
        

    def createConfiguration(self, default: dict):
        if Question.yesNo('Register configuration is missing. You want to create it now ?'):
            answer = Question.list([
                {
                    'type': 'input',
                    'name': RegisterConfig.SERVER_ID,
                    'message': 'What is the name of this server ?',
                    'default': default.get(RegisterConfig.SERVER_ID, ''),
                    'validate': Question.validateString
                },
                {
                    'type': 'input',
                    'name': RegisterConfig.ACCOUNT_SQS_ENDPOINT,
                    'message': 'Accounts Queue url ?',
                    'default': default.get(RegisterConfig.ACCOUNT_SQS_ENDPOINT, ''),
                    'validate': Question.validateUrl
                },
                {
                    'type': 'input',
                    'name': RegisterConfig.MAX_PROCESS,
                    'message': 'Default process count ?',
                    'default': str(default.get(RegisterConfig.MAX_PROCESS, cpu_count())),
                    'filter': int,
                    'validate': Question.validateInteger
                },
                {
                    'type': 'input',
                    'name': RegisterConfig.SPAWN_INTERVAL,
                    'message': 'Default spawn interval ?',
                    'default': str(default.get(RegisterConfig.SPAWN_INTERVAL, 0.5)),
                    'filter': float,
                    'validate': Question.validateFloat
                },
            ])
            if not answer:
                return False

            self.writeConfiguration({self.section: answer})
            return True

        return False