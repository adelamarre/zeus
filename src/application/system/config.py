
import os, subprocess
from src.application.scenario import AbstractScenario


class Scenario(AbstractScenario):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def start(self):
        cmd = os.environ.get('EDITOR', 'vi') + ' ' + self.configFile
        subprocess.call(cmd, shell=True)
