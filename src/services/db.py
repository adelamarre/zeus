import importlib
import json
import os
import sqlite3
from sqlite3.dbapi2 import Cursor, OperationalError
from src.services.console import Console

class AbstractDbUpdater:
    def __init__(self, name: str) -> None:
        self.name = name
    
    def update(self, cursor: Cursor):
        pass

class Db:
    def __init__(self, userDir: str, updaterNamespace: str, console: Console) -> None:
        self.dbfile = userDir + '/venom.db'
        self.updaterNamespace = updaterNamespace
        self.con = None
        self.console = console

        try:
            result = self.getCursor().execute('SELECT update_id FROM revision ORDER BY update_id DESC LIMIT 1;')
        except OperationalError as e:
            self.init()
        self.update()

    def init(self):
        self.getCursor().execute('CREATE TABLE revision (update_id INTEGER, name TEXT);')
        self.commit()

    def update(self):
        cur = self.getCursor()
        revisionIndex = 0
        result = cur.execute("SELECT update_id FROM revision ORDER BY update_id DESC LIMIT 1;")
        if result:
            revisionEntity = result.fetchone()
            if revisionEntity:
                revisionIndex = revisionEntity['update_id']
        
        while True:
            try:
                revisionIndex += 1
                module = importlib.import_module('%s.%s' % (self.updaterNamespace, 'updater%d' % revisionIndex))
                updater: AbstractDbUpdater = module.Updater()
                updater.update(cur)
                cur.execute("INSERT INTO revision (update_id, name) VALUES(%d,'%s');" % (revisionIndex, updater.name))
                
                self.commit()
            except ModuleNotFoundError:
                break
            except:
                self.console.exception()
                break
                
    def getConnexion(self):
        if self.con is None:
            self.con = sqlite3.connect(self.dbfile, isolation_level=None)
            self.con.row_factory = sqlite3.Row
        return self.con

    def getCursor(self) -> Cursor:
        return self.getConnexion().cursor()
    
    def commit(self):
        if self.con:
            self.con.commit()

    def select(self, sql:str) -> Cursor:
        return self.getCursor().execute(sql)

    def insert(self, sql: str):
        cur = self.getCursor()
        cur.execute(sql)
        return cur.lastrowid

    def execute(self, sql:str) -> Cursor:
        self.getCursor().execute(sql)

    def _dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

class DbTable:
    def __init__(self, db: Db, name: str) -> None:
        self.db = db
        self.name = name
    
    def findById(self, rowid):
        self.db.con.row_factory = self.rowFactory
        rows = self.db.select('select * from {self.name:s} where rowid={rowid:d}')
        rows.row_factory
        
    
