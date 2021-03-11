


from src.services.db import Db, DbTable

class ServerTable(DbTable):
    def __init__(self, db: Db) -> None:
        super().__init__(db, 'server')
    
    def addServer(self, name: str, ip: str = ''):
        return self.db.insert(f"INSERT into {self.name} (name, ip) values ('{name:s}', '{ip:s}');")

    def findByName(self, name: str):
        return self.findBy({'name': name})

