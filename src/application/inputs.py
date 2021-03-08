



from src.services.questions import Question


class Inputs:
    def __init__(self) -> None:
        self.questions = []

    def _getQuestions(self):
        return self.questions

    def getInputs(self):
        return Question.list(self._getQuestions())