


from src.services.db import Db, DbTable

class RevisionTable(DbTable):
    def __init__(self, db: Db) -> None:
        super().__init__(db, 'revision')
    
    def getLastRevsision(self):
        revision = self.findBy(orderby={'rowid': 'desc'}, limit=1)
        return revision
