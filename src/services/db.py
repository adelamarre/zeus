import json
import os
import sqlite3
from sqlite3.dbapi2 import Cursor


class AbstractDbUpdater:
    def update(cursor: Cursor):
        pass

class Db:
    def __init__(self, userDir: str, upddaterNamespace: str) -> None:
        self.dbfile = userDir + '/venom.db'
        if not os.path.exists(self.dbfile):
            self.init()

    def init(self):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        version = cur.execute('SELECT * FROM version;')


    def addContract(self, id: str, description: str):
        if id in self.contracts:
            raise Exception(f'The contract "{id}" already exists')
        self.contracts[id] = {
            'id': id,
            'description': description
        }
        self.writeContracts()

    def getContract(self, id:str):
        return self.contracts.get(id, None)

    def updateContract(self, id: str, description: str):
        if id in self.contracts:
            self.contracts[id]['description']
            self.writeContracts()
    
    def writeContracts(self):
        with open(self.contractFile, 'w') as f:
            json.dump(self.contracts, f)
    
    def loadContracts(self):
        if not os.path.exists(self.contractFile):
             self.writeContracts()
        else:
            with open(self.contractFile, 'w') as f:
                json.dump(self.contracts, f)
