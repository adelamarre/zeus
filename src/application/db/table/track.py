


from src.services.db import Db, DbTable

class TrackTable(DbTable):
    def __init__(self, db: Db) -> None:
        super().__init__(db, 'track')
    
    def addTrack(self, artistId: str, name: str) -> int:
        return self.db.insert(f"INSERT into {self.name} (artist_id, name) values ({artistId:d}, '{name:s}');")

    def findByName(self, artistId: str, name: str):
        return self.findBy({'artist_id': artistId, 'name': name})

