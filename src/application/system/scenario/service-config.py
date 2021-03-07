
import os, subprocess
from src.application.scenario import AbstractScenario


class Scenario(AbstractScenario):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def start(self):
        os.makedirs(self.userDir, exist_ok=True)
        cmd = os.environ.get('EDITOR', 'vi') + ' ' + self.userDir + '/config.service.ini'
        subprocess.call(cmd, shell=True)