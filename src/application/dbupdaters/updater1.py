
from sqlite3.dbapi2 import Cursor
from src.services.db import AbstractDbUpdater

class Updater(AbstractDbUpdater):
    def __init__(self) -> None:
        super().__init__('init')

    def update(self, cursor: Cursor):
        cursor.executescript("""
CREATE TABLE client (
    name TEXT,
    date TEXT
);

CREATE TABLE contract (
    client_id INTEGER,
    code TEXT,
    description TEXT,
    date TEXT
);

CREATE TABLE application (
    name TEXT
);

CREATE TABLE playlist (
    name TEXT,
    url TEXT
);

CREATE TABLE server (
    name TEXT,
    ip TEXT
);

CREATE TABLE artist (
    name TEXT
);

CREATE TABLE statistics (
    application_id INTEGER,
    playlist_id INTEGER,
    server_id INTEGER,
    artist_id TEXT,
    track TEXT,
    listener_count INTEGER,
    ymd INTEGER
);
"""
)