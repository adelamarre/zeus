
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

    def songPlayed(self, user, playlistUrl: str, playlistName: str, songName: str, artistName: str, playDuration: int, contractId:str):
        self.remoteQueue.sendMessage({
            'serverId': self.serverId,
            'application': self.application,
            'user': user['email'],
            'playlistUrl': playlistUrl,
            'playlistName': playlistName,
            'songName': songName,
            'artistName': artistName,
            'playDuration': playDuration,
            'contractId': contractId,
            'time': time(),
            'ymd': datetime.now().strftime("%Y%m%d")
        })
    