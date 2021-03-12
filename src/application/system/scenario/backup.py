
import os, subprocess
from src.application.db.table.revision import RevisionTable
from src.services.console import Console
from src.services.db import Db
from src.application.scenario import AbstractScenario


class Scenario(AbstractScenario):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def start(self):
        os.makedirs(self.userDir, exist_ok=True)
        logfile = self.userDir + '/venom.log'
        verbose = 3 if self.args.verbose else 1
        console = Console(verbose=verbose, ouput=self.args.verbose, logfile=logfile, logToFile=not self.args.nolog)
        try:
            db = Db(userDir=self.userDir, console=console)
            backupfile = db.backup()
            console.log('Database backup ok, file  %s' % backupfile)
        except BaseException as e:
            console.exception()
        