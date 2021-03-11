from sqlite3.dbapi2 import Cursor
from src.services.db import Db, AbstractDbUpdater

class Updater(AbstractDbUpdater):
    def __init__(self) -> None:
        super().__init__('add contract status')

    def update(self, cursor: Cursor):
        cursor.execute('ALTER TABLE contract ADD COLUMN status TEXT;')