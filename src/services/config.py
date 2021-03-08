
from src.services.questions import Question
from configparser import ConfigParser
from os import cpu_count, path
from src.services.questions import Question
import sys

class Config:
    def __init__(self, configFile: str, section: str) -> None:
        self.configFile = configFile
        self.section = section
    
    def getConfig(self, default: dict = {}):
        if not path.exists(self.configFile):
            if self.createConfiguration(default):
                return self.check(self.getConfig(default))
            return self.check(None)
        parser = ConfigParser()
        parser.read(self.configFile)
        try:
            configData = parser[self.section]
            return self.check(self._parse(configData))
        except Exception as e:
            if self.section in parser.sections():
                default = {**default, **parser[self.section]}
            if self.createConfiguration( default):
                return self.check(self.getConfig(default))
            return self.check(None)

    def writeConfiguration(self, config):
        parser = ConfigParser()
        parser.read(self.configFile)
        parser.update(config)
        with open(self.configFile, 'w') as f:    # save
            parser.write(f,space_around_delimiters=False)
    
    def _parse(self, data):
        return data

    def createConfiguration(self, data):
        self.writeConfiguration({self.section: data})
        return True

    def check(self, data):
        return data
    
    def assertNotEmpty(self, data: dict, key: str):
        if not key in data or data[key] == '':
            sys.exit('you need to set the {key} value in the config file.')
