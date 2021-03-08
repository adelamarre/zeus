import sys
from src.services.config import Config
from configparser import ConfigParser
from os import cpu_count, path
from src.services.questions import Question


class MonitorConfig(Config):
    def __init__(self, configFile: str) -> None:
        super().__init__(configFile, 'MONITOR')
    
    ACCOUNT_SQS_ENDPOINT = 'account_sqs_endpoint'
    COLLECTOR_SQS_ENDPOINT = 'collector_sqs_endpoint'
    POLL_INTERVAL = 'poll_interval'
    SERVERS = 'servers'
    SECRET = 'secret'
    

    def _parse(self, configData):
        return {
            MonitorConfig.ACCOUNT_SQS_ENDPOINT:    configData[MonitorConfig.ACCOUNT_SQS_ENDPOINT].strip(),
            MonitorConfig.COLLECTOR_SQS_ENDPOINT:  configData[MonitorConfig.COLLECTOR_SQS_ENDPOINT].strip(),
            MonitorConfig.SERVERS:                 configData[MonitorConfig.SERVERS],
            MonitorConfig.SECRET:                  configData[MonitorConfig.SECRET],
            MonitorConfig.POLL_INTERVAL:           float(configData[MonitorConfig.POLL_INTERVAL])
        }
    
    def createConfiguration(self, default: dict):
        if Question.yesNo('Monitor configuration is missing. You want to create it now ?'):
            answer = Question.list([
                {
                    'type': 'input',
                    'name': MonitorConfig.ACCOUNT_SQS_ENDPOINT,
                    'message': 'Account queue url ?',
                    'default': default.get(MonitorConfig.ACCOUNT_SQS_ENDPOINT, ''),
                    'validate': Question.validateUrl
                },
                {
                    'type': 'input',
                    'name': MonitorConfig.COLLECTOR_SQS_ENDPOINT,
                    'message': 'Collector queue url ?',
                    'default': default.get(MonitorConfig.COLLECTOR_SQS_ENDPOINT, ''),
                    'validate': Question.validateUrl
                },
                {
                    'type': 'input',
                    'name': MonitorConfig.POLL_INTERVAL,
                    'message': 'Polling interval ?',
                    'default': str(default.get(MonitorConfig.POLL_INTERVAL, 2.0)),
                    'filter': float,
                    'validate': Question.validateFloat
                },
                {
                    'type': 'password',
                    'name': MonitorConfig.SECRET,
                    'message': 'Set the password for stats server',
                    'filter': Question.filterMd5,
                },
                {
                    'type': 'input',
                    'name': MonitorConfig.SERVERS,
                    'message': 'Set servers (coma separated list)',
                    'default': default.get(MonitorConfig.SERVERS, '')
                },
            ])
            if not answer:
                return False

            if answer[MonitorConfig.SECRET] is None or len(answer[MonitorConfig.SECRET]) == 0:
                answer[MonitorConfig.SECRET] = default.get(MonitorConfig.SECRET, '')
            
            self.writeConfiguration({self.section: answer})
            return True
        return False
    
    def check(self, data):
        if data is None:
            sys.exit('I can not continue without configuraton')
        for key in [
            MonitorConfig.ACCOUNT_SQS_ENDPOINT,
            MonitorConfig.SERVERS,
            MonitorConfig.SECRET
        ]:
            self.assertNotEmpty(data, key)
        return super().check(data)