


from src.services.db import Db, DbTable

class ClientTable(DbTable):
    def __init__(self, db: Db) -> None:
        super().__init__(db, 'client')
    
    def addClient(self, name: str) -> int:
        return self.db.insert(f"INSERT into {self.name} (name) values ('{name:s}');")

    def findByName(self, name: str):
        return self.findBy({'name': name})

