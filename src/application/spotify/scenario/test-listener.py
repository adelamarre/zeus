import os, sys
from src.services.aws import RemoteQueue
from datetime import datetime
from psutil import cpu_count
from src.services.config import Config
from src.services.console import Console 
from src.services.questions import Question
from src.application.scenario import AbstractScenario
from src.application.spotify.scenario.listener import ListenerProcessProvider
from src.application.spotify.utils import getPlaylistSongChoices
from src.application.spotify.parser.playlist import TrackSelector
from requests import get

class Scenario(AbstractScenario):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.configFile = self.userDir + '/config.ini' 
        
    def start(self):
        logDir = None
        screenshotDir = None
        logfile = None
        
        if self.args.nolog == False:
            logDir = self.userDir + '/test-listener/' + datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
            logfile = logDir + '/session.log'
            os.makedirs(logDir, exist_ok=True)
            if self.args.screenshot:
                screenshotDir = logDir + '/screenshot'
                os.makedirs(screenshotDir, exist_ok=True)
        
        #print('Configuration file: %s' % configFile)

        defautlConfig = {
            'account_sqs_endpoint': '',
            'stats_sqs_endpoint': '',
            'secret': '',
            'max_process': cpu_count(),
            'spawn_interval': 0.5
        }
        
        listenerConfig = Config.getListenerConfig(self.configFile, defautlConfig)

        if not listenerConfig:
            sys.exit('I can not continue without configuraton')
        
        #https://sqs.eu-west-3.amazonaws.com/884650520697/18e66ed8d655f1747c9afbc572955f46
        
        if self.args.verbose:
            verbose = 3
        else:
            verbose = 1

        console = Console(verbose=verbose, ouput=self.args.verbose, logfile=logfile, logToFile=not self.args.nolog)
        console.log('Start scenario Spotify listener')

        if not listenerConfig['account_sqs_endpoint']:
            sys.exit('you need to set the account_sqs_endpoint in the config file.')

        if not listenerConfig['collector_sqs_endpoint']:
            sys.exit('you need to set the stats_sqs_endpoint in the config file.')

        if not listenerConfig['server_id']:
            sys.exit('you need to set the server_id in the config file.')

        if not listenerConfig['secret']:
            sys.exit('You need to provide the server stats password')


        lastResponse = Question.loadLastResponse(self.userDir)
        default = lastResponse['TEST-LISTENER'] if 'TEST-LISTENER' in lastResponse else {}

        questions = [
            {
                'type': 'input',
                'name': 'playlist',
                'message': 'Playlist url ?',
                'default': default.get('playlist', ''),
                'validate': Question.validateUrl,
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
                'choices': lambda answer : getPlaylistSongChoices(
                    playlistUrl=answer['playlist'], 
                    console=console,
                    userDir=self.userDir,
                    shutdownEvent=self.shutdownEvent
                ) if not answer['play_all_songs'] else {},
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
            'type': 'confirm',
            'message': 'Ok, please type [enter] to start or [n] to abort',
            'name': 'continue',
            'default': True,
            },
        ]
        answers = Question.list(questions)
        if not answers.get('continue', False): sys.exit('ok, see you soon.')

        lastResponse.update({
            'TEST-LISTENER':
            {
                'playlist': answers.get('playlist',default.get('playlist',''))
            }
        })
        Question.saveLastResponse(self.userDir, lastResponse)

        playlist = answers.get('playlist', None)
        if playlist is None:
            sys.exit('You give a playlist url')

        playSong = '*'
        if not answers.get('play_all_songs', True):
            if len(answers['play_songs']) < 1:
                sys.exit('You do not select any song to play...')
            playSong = ','.join(answers['play_songs'])
        
        playConfig = playSong + ':' + answers['play_count']
        
        accountRemoteQueue = RemoteQueue(listenerConfig['account_sqs_endpoint'])

        pp = ListenerProcessProvider(
            appArgs=self.args,
            accountRemoteQueue=accountRemoteQueue,
            statsCollector=None,
            shutdownEvent=self.shutdownEvent,
            console= console,
            headless=False,
            vnc= True,
            screenshotDir=screenshotDir,
            overridePlaylist=playlist,
            overridePlayConfig=playConfig
        )

        p = pp.getNewProcess(1)
        if p:
            p.start()
            ip = get('https://api.ipify.org').text
            print(f'Vnc address vnc://{ip}:5900')
            p.join()
        else:
            print('There is no account in the queue')
        
        
        