



from src.services.questions import Question
from configparser import ConfigParser
import os

class Inputs:
    def __init__(self) -> None:
        self.questions = []
        self.lastResponse = {}
    def _getQuestions(self):
        return self.questions

    def getInputs(self):
        return Question.list(self._getQuestions())

    def _getDefault(self, key, default):
        return self.lastResponse.get(key, self.config.get(key, default))

    def loadLastResponse(self, userDir: str, section):
        dataFile = userDir + '/questions.tmp'
        parser = ConfigParser()
        if os.path.exists(dataFile):
            parser.read(dataFile)
        if section in parser:
            return parser[section]
        return {}
    
    def saveLastResponse(self, userDir: str, section, answers):
        dataFile = userDir + '/questions.tmp'
        parser = ConfigParser()
        if os.path.exists(dataFile):
            parser.read(dataFile)
        parser.update({section: answers})  
        with open(dataFile, 'w') as f:    # save
            parser.write(f,space_around_delimiters=False)