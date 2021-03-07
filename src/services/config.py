
from src.services.questions import Question
from configparser import ConfigParser
from os import cpu_count, path
from src.services.questions import Question

class Config:
    # Config Section
    SECTION_MONITOR = 'MONITOR'
    SECTION_REGISTER = 'REGISTER'
    SECTION_LISTENER = 'LISTENER'
    SECTION_SERVICE = 'SERVICE'

    # Config key
    ACCOUNT_SQS_ENDPOINT = 'account_sqs_endpoint'
    COLLECTOR_SQS_ENDPOINT = 'collector_sqs_endpoint'
    MAX_PROCESS= 'max_process'
    SERVER_ID = 'server_id'
    SPAWN_INTERVAL = 'spawn_interval'
    POLL_INTERVAL = 'poll_interval'
    SERVERS = 'servers'
    SECRET = 'secret'

    def getRegisterConfig(configFile, default: dict = {
        MAX_PROCESS: cpu_count(),
        SPAWN_INTERVAL: 0.5
    }):
        if not path.exists(configFile):
            if not Config.createRegisterConfiguration(configFile, default):
                return 
        parser = ConfigParser()
        parser.read(configFile)
        try:
            configData = parser[Config.SECTION_REGISTER]
            return {
                Config.SERVER_ID:               configData[Config.SERVER_ID].strip(),
                Config.ACCOUNT_SQS_ENDPOINT:    configData[Config.ACCOUNT_SQS_ENDPOINT].strip(),
                Config.COLLECTOR_SQS_ENDPOINT:  configData[Config.COLLECTOR_SQS_ENDPOINT].strip(),
                Config.MAX_PROCESS:             int(configData[Config.MAX_PROCESS]),
                Config.SPAWN_INTERVAL:          float(configData[Config.SPAWN_INTERVAL])
            }
        except:
            if Config.SECTION_REGISTER in parser.sections():
                default = {**default, **parser[Config.SECTION_REGISTER]}
            if Config.createRegisterConfiguration(configFile, default):
                return Config.getRegisterConfig(configFile, default)
  
    def getListenerConfig(configFile, default: dict = {
        MAX_PROCESS: cpu_count(),
        SPAWN_INTERVAL: 0.5
    }):
        if not path.exists(configFile):
            if not Config.createListenerConfiguration(configFile, default):
                return 
        parser = ConfigParser()
        parser.read(configFile)
        try:
            configData = parser['LISTENER']
            return {
                Config.SERVER_ID:               configData[Config.SERVER_ID].strip(),
                Config.ACCOUNT_SQS_ENDPOINT:    configData[Config.ACCOUNT_SQS_ENDPOINT].strip(),
                Config.COLLECTOR_SQS_ENDPOINT:  configData[Config.COLLECTOR_SQS_ENDPOINT].strip(),
                Config.MAX_PROCESS:             int(configData[Config.MAX_PROCESS]),
                Config.SPAWN_INTERVAL:          float(configData[Config.SPAWN_INTERVAL]),
                Config.SECRET:                  configData[Config.SECRET],
            }
        except:
            if 'LISTENER' in parser.sections():
                default = {**default, **parser['LISTENER']}
            if Config.createListenerConfiguration(configFile, default):
                return Config.getListenerConfig(configFile, default)
    
    def getMonitorConfig(configFile, default: dict = {
        POLL_INTERVAL: 2.0
    }):
        if not path.exists(configFile):
            if not Config.createMonitorConfiguration(configFile, default):
                return 
        parser = ConfigParser()
        parser.read(configFile)
        try:
            configData = parser[Config.SECTION_MONITOR]
            if not configData[Config.SECRET]:
                raise Exception('Missing secret')
            return {
                Config.ACCOUNT_SQS_ENDPOINT:    configData[Config.ACCOUNT_SQS_ENDPOINT].strip(),
                Config.COLLECTOR_SQS_ENDPOINT:  configData[Config.COLLECTOR_SQS_ENDPOINT].strip(),
                Config.SERVERS:                 configData[Config.SERVERS],
                Config.SECRET:                  configData[Config.SECRET],
                Config.POLL_INTERVAL:           float(configData[Config.POLL_INTERVAL])
            }
            
        except:
            if Config.SECTION_MONITOR in parser.sections():
                default = {**default, **parser[Config.SECTION_MONITOR]}
            if Config.createMonitorConfiguration(configFile, default):
                return Config.getMonitorConfig(configFile, default)
    
    def createRegisterConfiguration(configFile, default: dict):
        if Question.yesNo('Register configuration is missing. You want to create it now ?'):
            answer = Question.list([
                {
                    'type': 'input',
                    'name': Config.SERVER_ID,
                    'message': 'What is the name of this server ?',
                    'default': default.get(Config.SERVER_ID, ''),
                    'validate': Question.validateString
                },
                {
                    'type': 'input',
                    'name': Config.ACCOUNT_SQS_ENDPOINT,
                    'message': 'Accounts Queue url ?',
                    'default': default.get(Config.ACCOUNT_SQS_ENDPOINT, ''),
                    'validate': Question.validateUrl
                },
                {
                    'type': 'input',
                    'name': Config.MAX_PROCESS,
                    'message': 'Default process count ?',
                    'default': str(default.get(Config.MAX_PROCESS, cpu_count())),
                    'filter': int,
                    'validate': Question.validateInteger
                },
                {
                    'type': 'input',
                    'name': Config.SPAWN_INTERVAL,
                    'message': 'Default spawn interval ?',
                    'default': str(default.get(Config.SPAWN_INTERVAL, 0.5)),
                    'filter': float,
                    'validate': Question.validateFloat
                },
            ])
            if not answer:
                return False

            Config.writeConfiguration(configFile, {Config.SECTION_REGISTER: answer})
            return True

        return False
    
    def createListenerConfiguration(configFile, default: dict):
        if Question.yesNo('Listener configuration is missing. You want to create it now ?'):
            answer = Question.list([
                {
                    'type': 'input',
                    'name': Config.SERVER_ID,
                    'message': 'What is the name of this server ?',
                    'default': default.get(Config.SERVER_ID, ''),
                    'validate': Question.validateString
                },
                {
                    'type': 'input',
                    'name': Config.ACCOUNT_SQS_ENDPOINT,
                    'message': 'Accounts Queue url ?',
                    'default': default.get(Config.ACCOUNT_SQS_ENDPOINT, ''),
                    'validate': Question.validateUrl
                },
                {
                    'type': 'input',
                    'name': Config.COLLECTOR_SQS_ENDPOINT,
                    'message': 'Statistics Queue url ?',
                    'default': default.get(Config.COLLECTOR_SQS_ENDPOINT, ''),
                    'validate': Question.validateUrl
                },
                {
                    'type': 'input',
                    'name': Config.MAX_PROCESS,
                    'message': 'Default process count ?',
                    'default': str(default.get(Config.MAX_PROCESS, cpu_count())),
                    'filter': int,
                    'validate': Question.validateInteger
                },
                {
                    'type': 'input',
                    'name': Config.SPAWN_INTERVAL,
                    'message': 'Default spawn interval ?',
                    'default': str(default.get(Config.SPAWN_INTERVAL, 0.5)),
                    'filter': float,
                    'validate': Question.validateFloat
                },
                {
                    'type': 'password',
                    'name': Config.SECRET,
                    'message': 'Set the password for stats server',
                    'filter': Question.filterMd5,
                },
                
            ])
            if not answer:
                return False
            if answer[Config.SECRET] is None or len(answer[Config.SECRET]) == 0:
                answer[Config.SECRET] = default.get(Config.SECRET, '')
            
            Config.writeConfiguration(configFile, {Config.SECTION_LISTENER: answer})
            return True

        return False
    
    def createMonitorConfiguration(configFile, default: dict):
        if Question.yesNo('Monitor configuration is missing. You want to create it now ?'):
            answer = Question.list([
                {
                    'type': 'input',
                    'name': Config.ACCOUNT_SQS_ENDPOINT,
                    'message': 'Account queue url ?',
                    'default': default.get(Config.ACCOUNT_SQS_ENDPOINT, ''),
                    'validate': Question.validateUrl
                },
                {
                    'type': 'input',
                    'name': Config.COLLECTOR_SQS_ENDPOINT,
                    'message': 'Collector queue url ?',
                    'default': default.get(Config.COLLECTOR_SQS_ENDPOINT, ''),
                    'validate': Question.validateUrl
                },
                {
                    'type': 'input',
                    'name': Config.POLL_INTERVAL,
                    'message': 'Polling interval ?',
                    'default': str(default.get(Config.POLL_INTERVAL, 2.0)),
                    'filter': float,
                    'validate': Question.validateFloat
                },
                {
                    'type': 'password',
                    'name': Config.SECRET,
                    'message': 'Set the password for stats server',
                    'filter': Question.filterMd5,
                },
                {
                    'type': 'input',
                    'name': Config.SERVERS,
                    'message': 'Set servers (coma separated list)',
                    'default': default.get(Config.SERVERS, '')
                },
            ])
            if not answer:
                return False

            if answer[Config.SECRET] is None or len(answer[Config.SECRET]) == 0:
                answer[Config.SECRET] = default.get(Config.SECRET, '')
            
            Config.writeConfiguration(configFile, {Config.SECTION_MONITOR: answer})
            return True
        return False
    
    def writeConfiguration(configFile, config):
        parser = ConfigParser()
        parser.read(configFile)
        parser.update(config)
        with open(configFile, 'w') as f:    # save
            parser.write(f,space_around_delimiters=False)
        