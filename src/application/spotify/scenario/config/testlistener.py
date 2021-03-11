

from src.services.config import Config
from configparser import ConfigParser

from src.services.questions import Question
import sys



class TestListenerConfig(Config):
    def __init__(self, configFile: str) -> None:
        super().__init__(configFile, 'TEST-LISTENER')

    SERVER_ID = 'server_id'
    ACCOUNT_SQS_ENDPOINT = 'account_sqs_endpoint'
    COLLECTOR_SQS_ENDPOINT = 'collector_sqs_endpoint'
    MAX_PROCESS= 'max_process'
    SPAWN_INTERVAL = 'spawn_interval'
    SECRET = 'secret'

    
    def _parse(self, configData):
        return {
            TestListenerConfig.SERVER_ID:               configData[TestListenerConfig.SERVER_ID].strip(),
            TestListenerConfig.ACCOUNT_SQS_ENDPOINT:    configData[TestListenerConfig.ACCOUNT_SQS_ENDPOINT].strip(),
            TestListenerConfig.COLLECTOR_SQS_ENDPOINT:  configData[TestListenerConfig.COLLECTOR_SQS_ENDPOINT].strip(),
            TestListenerConfig.MAX_PROCESS:             int(configData[TestListenerConfig.MAX_PROCESS]),
            TestListenerConfig.SPAWN_INTERVAL:          float(configData[TestListenerConfig.SPAWN_INTERVAL]),
            TestListenerConfig.SECRET:                  configData[TestListenerConfig.SECRET],
        }

    def check(self, data):
        if data is None:
            sys.exit('I can not continue without configuraton')
        for key in [
           TestListenerConfig.ACCOUNT_SQS_ENDPOINT, 
           TestListenerConfig.COLLECTOR_SQS_ENDPOINT, 
           TestListenerConfig.SERVER_ID, 
           TestListenerConfig.SECRET
        ]:
            self.assertNotEmpty(data, key)
        return data