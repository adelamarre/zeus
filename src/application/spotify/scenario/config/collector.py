
from src.services.config import Config
from configparser import ConfigParser
from os import cpu_count, path
from src.services.questions import Question
import sys

class CollectorConfig(Config):
    def __init__(self, configFile: str) -> None:
        super().__init__(configFile, 'COLLECTOR')

    
    COLLECTOR_SQS_ENDPOINT = 'collector_sqs_endpoint'
    
    
    def _parse(self, configData):
        return {
            CollectorConfig.COLLECTOR_SQS_ENDPOINT:  configData[CollectorConfig.COLLECTOR_SQS_ENDPOINT].strip(),
        }

    def check(self, data):
        if data is None:
            sys.exit('I can not continue without configuraton')
        for key in [
           CollectorConfig.COLLECTOR_SQS_ENDPOINT, 
        ]:
            self.assertNotEmpty(data, key)
        return data

    def createConfiguration(self, default: dict):
        if Question.yesNo('Listener configuration is missing. You want to create it now ?'):
            answer = Question.list([
                {
                    'type': 'input',
                    'name': CollectorConfig.COLLECTOR_SQS_ENDPOINT,
                    'message': 'Statistics Queue url ?',
                    'default': default.get(CollectorConfig.COLLECTOR_SQS_ENDPOINT, ''),
                    'validate': Question.validateUrl
                },
            ])
            if not answer:
                return False
            self.writeConfiguration({self.section: answer})
            return True

        return False
    