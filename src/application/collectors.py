

from src.services.console import Console
from src.services.db import Db



class StatsCollector:
    
    def __init__(self, userDir: str, console: Console) -> None:
        self.db = Db(userDir=userDir, updaterNamespace='src.application.dbupdaters', console=console)
        pass

    def collect(message: dict):
        """
        "serverId": "Hetzner dev #1",
        "application": "spotify",
        "user": "sadibou.manesh902@libero.it",
        "playlistUrl": "https://open.spotify.com/playlist/4m1WfnLtWhosgfI0NWVAWf",
        "playlistName": "Calabrese",
        "songName": "Passage",
        "artistName": "SKORP",
        "playDuration": 88,
        "time": 1615075285.790404,
        "ymd": "20210307"
        """

        