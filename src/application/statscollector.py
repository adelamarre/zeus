
from src.application.collectors import CollectorMessage
from typing import Collection
from src.services.aws import RemoteQueue
from boto3 import client
from src import VERSION
from time import time
from datetime import datetime


class StatsCollector:
    def __init__(self, sqsEndpoint: str, application: str, serverId: str) -> None:
        self.remoteQueue: RemoteQueue = RemoteQueue(sqsEndpoint)
        self.sqsEndpoint = sqsEndpoint
        self.application = application
        self.serverId = serverId

    def songPlayed(self, user, playlistUrl: str, playlistName: str, trackName: str, artistName: str, playDuration: int, contractId:str):
        self.remoteQueue.sendMessage({
            CollectorMessage.SERVER_ID      : self.serverId,
            CollectorMessage.APPLICATION    : self.application,
            CollectorMessage.USER           : user['email'],
            CollectorMessage.PLAYLIST_URL   : playlistUrl,
            CollectorMessage.PLAYLIST_NAME  : playlistName,
            CollectorMessage.TRACK_NAME     : trackName,
            CollectorMessage.ARTIST_NAME    : artistName,
            CollectorMessage.PLAY_DURATION  : playDuration,
            CollectorMessage.CONTRACT_ID    : contractId,
            CollectorMessage.TIME           : time(),
        })
    