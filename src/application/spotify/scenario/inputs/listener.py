from multiprocessing import synchronize
import sys
from typing import List
from src.application.spotify.scenario.config.register import RegisterConfig
from src.services.contracts import ContractManager
from src.services.db import Db
from src.services.proxies import PROXY_FILE_REGISTER, ProxyManager, PROXY_FILE_LISTENER
from src.services.console import Console
from src.services.drivers import DriverManager
from src.application.spotify import Spotify
from src.application.spotify.parser.playlist import TrackList, TrackSelector
from os import removedirs
from src.services.questions import Question
from src.application.inputs import Inputs
from src.application.spotify.scenario.config.listener import ListenerConfig

class ListenerInputs(Inputs):
    PLAYLIST = 'playlist'
    MAX_PROCESS = 'max_process'
    STATS_SERVER = 'stats_server'

    def __init__(self, console: Console, shutdownEvent: synchronize.Event, config: dict, userDir: str) -> None:
        self.console = console
        self.shutdownEvent = shutdownEvent
        self.config = config
        self.userDir: str = userDir
        super().__init__()

    def getInputs(self):
        
        self.questions = [
            {
                'type': 'input',
                'name': ListenerInputs.MAX_PROCESS,
                'message': 'How much process to start ?',
                'default': str(self.config[ListenerConfig.MAX_PROCESS]),
                'validate': Question.validateInteger,
                'filter': int
            },
            {
                'type': 'confirm',
                'name': 'override_playlist',
                'message': 'Would you override the playlist to listen ?',
                'default': False
            },
            {
                'type': 'input',
                'name': ListenerInputs.PLAYLIST,
                'message': 'Playlist url ?',
                'default': '',
                'validate': Question.validateUrl,
                'when': lambda answers : answers['override_playlist']
            },
            {
                'type': 'confirm',
                'name': ListenerInputs.STATS_SERVER,
                'message': 'Would you start the statistics web server ?',
                'default': True
            },
            {
                'type': 'confirm',
                'message': 'Ok, please type [enter] to start or [n] to abort',
                'name': 'continue',
                'default': True,
            },
        ]
        answers = super().getInputs()

        if not 'continue' in answers or answers['continue'] == False:
            return None

        return {
            ListenerInputs.MAX_PROCESS: answers[ListenerInputs.MAX_PROCESS],
            ListenerInputs.PLAYLIST: answers.get(ListenerInputs.MAX_PROCESS, None),
            ListenerInputs.STATS_SERVER: answers[ListenerInputs.STATS_SERVER], 
        }
