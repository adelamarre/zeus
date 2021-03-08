from datetime import datetime
from src.services.db import Db



class ClientManager:
    def __init__(self, db: Db ) -> None:
        self.db = db

    def getclientsChoices(self):
        clientChoices = []
        for client in self.getClients():
            clientChoices.append({
                'name': '%s' % (client['name']),
                'value': int(client['rowid'])
            })
        clientChoices.append({
            'name': 'Create a new client',
            'value': 0
        })
        return clientChoices

    def getClients(self):
        ##contracts = []
        return self.db.select("SELECT rowid, * FROM client;").fetchall()
        
    def addClient(self, name: str) -> int:
        return self.db.insert("INSERT INTO client \
            (name, date) \
            VALUES ('%s', '%s')" % 
            (name, str(datetime.now()))
        )
        
        