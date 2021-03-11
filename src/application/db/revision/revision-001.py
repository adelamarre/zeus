
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
CREATE UNIQUE INDEX client_idx ON client(name);

CREATE TABLE contract (
    client_id INTEGER,
    code TEXT,
    count INTEGER,
    description TEXT,
    date TEXT
);
CREATE UNIQUE INDEX contract_idx ON contract(client_id, code);

CREATE TABLE application (
    name TEXT
);
CREATE UNIQUE INDEX application_idx ON application(name);

CREATE TABLE playlist (
    name TEXT,
    url TEXT
);
CREATE UNIQUE INDEX playlist_idx ON playlist(url);

CREATE TABLE server (
    name TEXT,
    ip TEXT
);
CREATE UNIQUE INDEX server_idx ON server(name);

CREATE TABLE artist (
    name TEXT
);
CREATE UNIQUE INDEX artist_idx ON artist(name);

CREATE TABLE track (
    artist_id INTEGER,
    name TEXT
);
CREATE UNIQUE INDEX track_idx ON track(artist_id, name);

CREATE TABLE statistic (
    application_id INTEGER,
    playlist_id INTEGER,
    server_id INTEGER,
    contract_id INTEGER,
    track_id INTEGER,
    play_duration INTEGER DEFAULT 0,
    count INTEGER DEFAULT 0,
    ymdh INTEGER
);
CREATE UNIQUE INDEX statistic_idx ON statistic(application_id, playlist_id, server_id, contract_id, ymdh);
"""
)