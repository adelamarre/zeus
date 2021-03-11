import importlib
import sys
import os
import sqlite3
from sqlite3.dbapi2 import Cursor, OperationalError
from src.services.console import Console
import shutil

class AbstractDbUpdater:
    def __init__(self, name: str) -> None:
        self.name = name
    
    def update(self, cursor: Cursor):
        pass

class Db:
    def __init__(self, userDir: str, console: Console) -> None:
        self.dbfile = userDir + '/venom.db'
        self.backupDir = userDir + '/backup'
        
        self.con = None
        self.console = console

        #try:
        #    result = self.getCursor().execute('SELECT update_id FROM revision ORDER BY update_id DESC LIMIT 1;')
        #except OperationalError as e:
        #    self.init()
        #self.migrate()

    def _row_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    
    def init(self):
        self.getCursor().execute('CREATE TABLE revision (update_id INTEGER, name TEXT);')
        self.commit()

    def close(self):
        if self.con:
            self.con.close()
            self.con = None

    def backup(self):
        os.makedirs(self.backupDir, exist_ok=True)
        tmpbackupFile = self.backupDir + '/db.bkp.tmp'
        if os.path.exists(tmpbackupFile):
            os.remove(tmpbackupFile)
        self.close()
        shutil.copyfile(self.dbfile, tmpbackupFile)
        return tmpbackupFile

    def restore(self, backupFileToRestore):
        self.close()
        if not os.path.exists(backupFileToRestore):
            sys.exit("Backup file %s not found. Restoration cancelled.")
        if os.path.exists(self.dbfile):
            os.remove(self.dbfile)
        shutil.copyfile(backupFileToRestore, self.dbfile)

    def migrate(self, revisionModule: str):
        tmpBackupFile = self.backup()
        
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
                module = importlib.import_module('%s.%s' % (revisionModule, 'revision-%3d' % revisionIndex))
                updater: AbstractDbUpdater = module.Updater()
                updater.update(cur)
                cur.execute("INSERT INTO revision (update_id, name) VALUES(%d,'%s');" % (revisionIndex, updater.name))
                self.commit()
            except ModuleNotFoundError:
                break
            except:
                self.restore(tmpBackupFile)
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
    
    def findById(self, rowid: int):
        return self.db.select(f'select rowid, * from {self.name:s} where rowid={rowid:d}')
        
    
    def findBy(self, where: dict):
        constraints = self._constraintsToSql(where)
        return self.db.select(f'select rowid, * from {self.name:s}{constraints:s};').fetchone()

    def findAllBy(self, where: dict):
        constraints = self._constraintsToSql(where)
        return self.db.select(f'select rowid, * from {self.name:s}{constraints:s};').fetchall()


    def _constraintsToSql(self, constraints: dict) -> str:
        if len(constraints.keys()):
            c = []
            for key in constraints:
                value = constraints[key]
                if isinstance(value, str):
                    c.append("%s='%s'" % (key, value))
                elif isinstance(value, int):
                    c.append("%s=%d" % (key, value))
                elif  isinstance(value, float):
                    c.append("%s=%f" % (key, value))
                else:
                    valueStr = str(value)
                    raise Exception('Could not use {strValue:s} in constraint')
            return ' where ' + ' and '.join(c)
        return ''