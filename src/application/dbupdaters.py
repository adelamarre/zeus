
from sqlite3.dbapi2 import Cursor
from src.services.db import AbstractDbUpdater

class Init(AbstractDbUpdater):
    def update(cursor: Cursor):
        cursor.execute('CREATE TABLE version')