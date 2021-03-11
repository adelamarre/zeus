

from datetime import datetime
from src.application.db.table.contract import ContractTable
from src.application.db.table.client import ClientTable
from src.application.db.table.statistic import StatisticTable
from src.application.db.table.track import TrackTable
from src.application.db.table.artist import ArtistTable
from src.application.db.table.playlist import PlaylistTable
from src.application.db.table.application import ApplicationTable
from src.application.db.table.server import ServerTable
from src.services.console import Console
from src.services.db import Db
from json import loads


class CollectorMessage:
    SERVER_ID = "serverId"
    APPLICATION = "application"
    USER = "user"
    CONTRACT_ID = 'contractId'
    PLAYLIST_URL = "playlistUrl"
    PLAYLIST_NAME = "playlistName"
    PLAY_DURATION = 'playDuration'
    TRACK_NAME = "songName"
    ARTIST_NAME = "artistName"
    PLAY_DURATION = "playDuration"
    TIME = "time"
    YMD = "ymd"
    
class StatsCollector:
    CACHE_APPLICATION = 'application'
    CACHE_PLAYLIST = 'playalist'
    CACHE_SERVER = 'server'
    CACHE_ARTIST = 'artist'
    CACHE_TRACK = 'track'
    CACHE_CLIENT = 'track'

    def __init__(self, userDir: str, console: Console) -> None:
        self.db = Db(userDir=userDir, console=console)
        self.console = console
        self.applicationTable = ApplicationTable(self.db)
        self.playlistTable = PlaylistTable(self.db)
        self.artistTable = ArtistTable(self.db)
        self.tractTable = TrackTable(self.db)
        self.serverTable = ServerTable(self.db)
        self.statisticTable = StatisticTable(self.db)
        self.contractTable = ContractTable(self.db)
        self.clientTable = ClientTable(self.db)
        self.cache = {
            StatsCollector.CACHE_APPLICATION: {},
            StatsCollector.CACHE_PLAYLIST: {},
            StatsCollector.CACHE_SERVER: {},
            StatsCollector.CACHE_ARTIST: {},
            StatsCollector.CACHE_TRACK: {},
            StatsCollector.CACHE_CLIENT: {},
        }
        self.defaultContractId = self.getDefaultContractId()
        
    def collect(self, message: dict):
        if 'Body' not in message:
            self.console.warning('Bad message received')
        else:
            message = loads(message['Body'])

        self.statisticTable.addCount(
            applicationId   = self.getApplicationId(message),
            playlistId      = self.getPlaylistId(message),
            contractId      = self.getContractId(message),
            play_duration   = int(message[CollectorMessage.PLAY_DURATION]),
            serverId        = self.getServerId(message),
            trackId         = self.getTrackId(message),
            ymdh            = int(datetime.fromtimestamp(message[CollectorMessage.TIME]).strftime('%Y%m%d%H'))
        )


    def getDefaultContractId(self):
        clientId = self.getClientId('default')
        contract = self.contractTable.findByCode(clientId, 'default')
        if contract is None:
            return self.contractTable.addContract(clientId, 'default', 'fallback contract', 0, 'closed')
        else:
            return contract['rowid']

    def getContractId(self, message: dict):
        contractId = self.defaultContractId
        if CollectorMessage.CONTRACT_ID in message and message[CollectorMessage.CONTRACT_ID]:
            try:
                contractId = int(message[CollectorMessage.CONTRACT_ID])
            except:
                #self.console.warning('Bad contract id %s' % str(message[CollectorMessage.CONTRACT_ID]))
                pass
        return contractId

    def getClientId(self, name):
        if name not in self.cache[StatsCollector.CACHE_CLIENT]:
            entity = self.clientTable.findByName(name)
            if entity:
                self.cache[StatsCollector.CACHE_CLIENT][name] = entity['rowid']
            else:
                self.cache[StatsCollector.CACHE_CLIENT][name] = self.clientTable.addClient(name)
        return self.cache[StatsCollector.CACHE_CLIENT][name]

    def getApplicationId(self, message):
        name = message[CollectorMessage.APPLICATION]
        cacheKey = StatsCollector.CACHE_APPLICATION
        if name not in self.cache[cacheKey]:
            application = self.applicationTable.findByName(name)
            if application:
                self.cache[cacheKey][name] = application['rowid']
            else:
                self.cache[cacheKey][name] = self.applicationTable.addApplication(name)

        return self.cache[cacheKey][name]
    
    def getPlaylistId(self, message):
        url = message[CollectorMessage.PLAYLIST_URL]
        cacheKey = StatsCollector.CACHE_PLAYLIST
        if url not in self.cache[cacheKey]:
            playlist = self.playlistTable.findByUrl(url)
            if playlist:
                self.cache[cacheKey][url] = playlist['rowid']
            else:
                self.cache[cacheKey][url] = self.playlistTable.addPlaylist(url, message[CollectorMessage.PLAYLIST_NAME])
                
        return self.cache[cacheKey][url]
    
    def getServerId(self, message):
        name = message[CollectorMessage.SERVER_ID]
        cacheKey = StatsCollector.CACHE_SERVER
        if name not in self.cache[cacheKey]:
            playlist = self.serverTable.findByName(name)
            if playlist:
                self.cache[cacheKey][name] = playlist['rowid']
            else:
                self.cache[cacheKey][name] = self.serverTable.addServer(name)
                
        return self.cache[cacheKey][name]

    def getArtistId(self, message):
        name = message[CollectorMessage.ARTIST_NAME]
        cacheKey = StatsCollector.CACHE_ARTIST
        
        if name not in self.cache[cacheKey]:
            entity = self.artistTable.findByName(name)
            if entity:
                self.cache[cacheKey][name] = entity['rowid']
            else:
                self.cache[cacheKey][name] = self.artistTable.addArtist(name)
                
        return self.cache[cacheKey][name]




    def getTrackId(self, message):
        artistId = self.getArtistId(message)
        name = message[CollectorMessage.TRACK_NAME]
        cacheKey = StatsCollector.CACHE_TRACK
        if name not in self.cache[cacheKey]:
            entity = self.tractTable.findByName(artistId, name)
            if entity:
                self.cache[cacheKey][name] = entity['rowid']
            else:
                self.cache[cacheKey][name] = self.tractTable.addTrack(artistId, name)
                
        return self.cache[cacheKey][name]