


from src.services.db import Db, DbTable

class ApplicationTable(DbTable):
    def __init__(self, db: Db) -> None:
        super().__init__(db, 'application')
    
    def addApplication(self, name: str):
        return self.db.insert(f"INSERT into {self.name} (name) values ('{name:s}');")

    def findByName(self, name):
        return self.findBy({'name': name})
    
