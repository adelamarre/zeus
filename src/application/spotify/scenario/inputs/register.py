from multiprocessing import synchronize
from src.services.clients import ClientManager
import sys
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


class RegisterInputs(Inputs):
    PLAYLIST = 'playlist'
    ACCOUNT_COUNT = 'accountCounts'
    PLAY_CONFIG = 'playConfig'
    CONTRACT_ID = 'contractId'
    MAX_PROCESS = 'maxProcess'

    def __init__(self, console: Console, shutdownEvent: synchronize.Event, config: dict, userDir: str) -> None:
        self.console = console
        self.shutdownEvent = shutdownEvent
        self.lastResponse = self.loadLastResponse(userDir, 'REGISTER')
        self.config = config
        self.userDir: str = userDir
        super().__init__()

    def getInputs(self):

        db = Db(userDir=self.userDir, revisionModule='src.application.db.revision', console=self.console)
        clientManager = ClientManager(db)
        clientChoices = clientManager.getclientsChoices()
        clientNames = list(map(lambda x: x['name'], clientChoices))

        self.questions = [
            {
                'type': 'input',
                'name': RegisterInputs.PLAYLIST,
                'message': 'Which playlist to listen ?',
                'default': str(self._getDefault(RegisterInputs.PLAYLIST, '')),
                'validate': Question.validateUrl
            },
            {
                'type': 'confirm',
                'message': 'Would you play all songs of this playlist ?',
                'name': 'play_all_songs',
                'default': True,
            },
            {
                'when': lambda answer : not answer['play_all_songs'],
                'type': 'checkbox',
                'message': 'Select the songs you want to play',
                'name': 'play_songs',
                'choices': lambda answer : self.getPlaylistSongChoices(playlistUrl=answer['playlist']) 
                    if not answer['play_all_songs'] else {},
                #'validate': lambda data : 'You must select at least one song' if len(data) < 1 else True
                'filter': lambda items: list(map(lambda x: str(x+1), items))
            },
            {
                'type': 'input',
                'name': 'play_count',
                'message': 'How much songs you want to play per session ?',
                'default': lambda answer : str(len(answer['play_songs'])) if 'play_songs' in answer else '1',
                'validate': lambda answer : TrackSelector.validateCounterConfig(answer),
                
            },
            {
                'type': 'input',
                'name': 'account_count',
                'message': 'How much account to create ?',
                'validate': Question.validateInteger,
                'filter': int
            },
            {
                'type': 'input',
                'name': 'max_process',
                'message': 'How much process to start ?',
                'default': str(self.config[RegisterConfig.MAX_PROCESS]),
                'validate': Question.validateInteger,
                'filter': int
            },
            {
                'type': 'list',
                'name': 'clientId',
                'message': 'Which client ?',
                'choices': clientChoices,
                'filter': int
            },
            {
                'when': lambda answers: answers['clientId'] == 0,
                'type': 'input',
                'name': 'newClientName',
                'message': 'New client name ?',
                'validate': lambda answer: True if ((len(answer) > 0) and (answer not in clientNames)) else 
                    'Invalid client name' if len(answer) < 1 else 'This client already exists',
            },
        ]

        answers1 = answers = super().getInputs()
        clientId = answers1['clientId']
        if clientId == 0:
            clientId = clientManager.addClient(answers1['newClientName'])
        contractManager = ContractManager(db)
        contractChoices = contractManager.getContractsChoices(clientId)
        contractIds = list(map(lambda x: x['value'], contractChoices))
        
        
        self.questions = [
            {
                'type': 'list',
                'name': 'contractId',
                'message': 'Which contract ?',
                'choices': contractChoices,
                'filter': int
            },
            {
                'when': lambda answers: answers['contractId'] == 0,
                'type': 'input',
                'name': 'newContractCode',
                'message': 'New contract code ?',
                'validate': lambda answer: True if ((len(answer) > 0) and (answer not in contractIds)) else 
                    'Invalid contract code' if len(answer) < 1 else 'This contract code already exists',
            },
            {
                'when': lambda answers: answers['contractId'] == 0,
                'type': 'input',
                'name': 'newContractCount',
                'message': 'New contract listener count ?',
                'validate': lambda answer: True if int(answer) > 0  else 'The count must greater than 0',
                'filter': int
            },
            {
                'when': lambda answers: answers['contractId'] == 0,
                'type': 'input',
                'name': 'newContractDescription',
                'message': 'New contract description ?',
                'validate': lambda answer: True if len(answer) > 0 else 'Invalid contract description',
            },
            {
                'type': 'confirm',
                'message': 'Ok, please type [enter] or [y] to start or [n] to abort',
                'name': 'continue',
                'default': True,
            },
        ]
        answers2 = super().getInputs()

        answers = dict(list(answers1.items()) + list(answers2.items()))
        if not 'continue' in answers or answers['continue'] == False:
            return None

        contractId = answers['contractId']
        if answers['contractId'] == 0:
            contractId = contractManager.addContract(
                clientId, answers['newContractCode'],
                answers['newContractDescription'],
                answers['newContractCount']
            )
        
        playlist = answers['playlist']
        accountCount = answers['account_count']
        maxProcess = answers['max_process']
        
        playSong = '*'
        if not answers['play_all_songs']:
            if len(answers['play_songs']) < 1:
                sys.exit('You do not select any song to play...')
            playSong = ','.join(answers['play_songs'])
        
        playConfig = playSong + ':' + answers['play_count']
        

        try:
            selector = TrackSelector()
            selector.parse(playConfig, 10000)
            testPlayConfig = selector.getSelection()
        except Exception as e:
            raise Exception('Bad play configuration format: %s' % playConfig)
       
        return {
            RegisterInputs.MAX_PROCESS: maxProcess,
            RegisterInputs.PLAYLIST: playlist,
            RegisterInputs.ACCOUNT_COUNT: accountCount,
            RegisterInputs.PLAY_CONFIG: playConfig,
            RegisterInputs.CONTRACT_ID: contractId
        }

    def getPlaylistSongChoices(self, playlistUrl):
        driver = None
        userDataDir=None
        choices = []
        try:
            proxyManager = ProxyManager(self.userDir, PROXY_FILE_LISTENER)
            driverManager = DriverManager(self.console, shutdownEvent=self.shutdownEvent)
            driver, userDataDir = driverManager.getDriver('chrome', 1, {}, proxyManager.getRandomProxy(), headless=True)
            spotify = Spotify.Adapter(driver=driver, console=self.console, shutdownEvent=self.shutdownEvent)
            playlist = TrackList(spotify, playlistUrl)
            playlist.load()
            tracks = playlist.getTracks()
            choice = []
            index = 0
            for track in tracks:
                choice.append({
                    'name': track.getName(),
                    'value': index
                })
                index +=1
        except:
            self.console.exception()
        
        if driver:
            try:
                driver.quit()
                del driver
            except:
                pass
        if userDataDir:
            try:
                removedirs(userDataDir)
            except:
                pass
        return choices
