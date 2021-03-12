
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
            revisionTable = RevisionTable(db)
            oldRevision = revisionTable.getLastRevsision()
            db.migrate('src.application.db.revision')
            newRevision = revisionTable.getLastRevsision()
            console.log('Database migration ok: revision %d => %d' % (oldRevision['update_id'], newRevision['update_id']))
        except BaseException as e:
            console.exception()
        