
from src.services.questions import Question
from configparser import ConfigParser
from os import cpu_count, path
from src.services.questions import Question

class Config:
    
    """def __init__(self, configFilePath = None):
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
    """
     

    def getRegisterConfig(configFile, default: dict = {
        'max_process': cpu_count(),
        'spawn_interval': 0.5
    }):
        if not path.exists(configFile):
            if not Config.createRegisterConfiguration(configFile, default):
                return 
        parser = ConfigParser()
        parser.read(configFile)
        try:
            configData = parser['REGISTER']
            return {
                'server_id':     configData['server_id'].strip(),
                'sqs_endpoint':  configData['sqs_endpoint'].strip(),
                'max_process':   int(configData['max_process']),
                'spawn_interval':float(configData['spawn_interval'])
            }
        except:
            if 'REGISTER' in parser.sections():
                default = {**default, **parser['REGISTER']}
            if Config.createRegisterConfiguration(configFile, default):
                return Config.getRegisterConfig(configFile, default)
  
    def getListenerConfig(configFile, default: dict = {
        'max_process': cpu_count(),
        'spawn_interval': 0.5
    }):
        if not path.exists(configFile):
            if not Config.createListenerConfiguration(configFile, default):
                return 
        parser = ConfigParser()
        parser.read(configFile)
        try:
            configData = parser['REGISTER']
            return {
                'server_id':     configData['server_id'].strip(),
                'sqs_endpoint':  configData['sqs_endpoint'].strip(),
                'max_process':   int(configData['max_process']),
                'spawn_interval':float(configData['spawn_interval'])
            }
        except:
            if 'LISTENER' in parser.sections():
                default = {**default, **parser['LISTENER']}
            if Config.createListenerConfiguration(configFile, default):
                return Config.getListenerConfig(configFile, default)
    
    def createRegisterConfiguration(configFile, default: dict):
        if Question.yesNo('Register configuration is missing. You want to create it now ?'):
            answer = Question.list([
                {
                    'type': 'input',
                    'name': 'server_id',
                    'message': 'What is the name of this server ?',
                    'default': default.get('server_id', ''),
                    'validate': Question.validateString
                },
                {
                    'type': 'input',
                    'name': 'sqs_endpoint',
                    'message': 'Queue url ?',
                    'default': default.get('sqs_endpoint', ''),
                    'validate': Question.validateUrl
                },
                {
                    'type': 'input',
                    'name': 'max_process',
                    'message': 'Default process count ?',
                    'default': str(default.get('max_process', cpu_count())),
                    'filter': int,
                    'validate': Question.validateInteger
                },
                {
                    'type': 'input',
                    'name': 'spawn_interval',
                    'message': 'Default spawn interval ?',
                    'default': str(default.get('spawn_interval', 0.5)),
                    'filter': float,
                    'validate': Question.validateFloat
                },
            ])
            if not answer:
                return False

            Config.writeConfiguration(configFile, {'REGISTER': answer})
            #cmd = os.environ.get('EDITOR', 'vi') + ' ' + configFile
            #subprocess.call(cmd, shell=True)
            return True

        return False
    
    def createListenerConfiguration(configFile, default: dict):
        if Question.yesNo('Listener configuration is missing. You want to create it now ?'):
            answer = Question.list([
                {
                    'type': 'input',
                    'name': 'server_id',
                    'message': 'What is the name of this server ?',
                    'default': default.get('server_id', ''),
                    'validate': Question.validateString
                },
                {
                    'type': 'input',
                    'name': 'sqs_endpoint',
                    'message': 'Queue url ?',
                    'default': default.get('sqs_endpoint', ''),
                    'validate': Question.validateUrl
                },
                {
                    'type': 'input',
                    'name': 'max_process',
                    'message': 'Default process count ?',
                    'default': str(default.get('max_process', cpu_count())),
                    'filter': int,
                    'validate': Question.validateInteger
                },
                {
                    'type': 'input',
                    'name': 'spawn_interval',
                    'message': 'Default spawn interval ?',
                    'default': str(default.get('spawn_interval', 0.5)),
                    'filter': float,
                    'validate': Question.validateFloat
                },
            ])
            if not answer:
                return False

            Config.writeConfiguration(configFile, {'LISTENER': answer})
            #cmd = os.environ.get('EDITOR', 'vi') + ' ' + configFile
            #subprocess.call(cmd, shell=True)
            return True

        return False
    
    def writeConfiguration(configFile, config):
        parser = ConfigParser()
        parser.read(configFile)
        parser.update(config)
        with open(configFile, 'w') as f:    # save
            parser.write(f,space_around_delimiters=False)
        