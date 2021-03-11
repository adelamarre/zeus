


from src.services.db import Db, DbTable

class PlaylistTable(DbTable):
    def __init__(self, db: Db) -> None:
        super().__init__(db, 'playlist')
    
    def addPlaylist(self, url: str, name: str):
        return self.db.insert(f"INSERT into {self.name} (name, url) values ('{name:s}', '{url:s}');")

    def findByUrl(self, url):
        return self.findBy({'url': url})

