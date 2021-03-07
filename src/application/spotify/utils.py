from multiprocessing import Event
from src.services.proxies import ProxyManager, PROXY_FILE_LISTENER
from src.services.console import Console
from src.services.drivers import DriverManager
from src.application.spotify import Spotify
from src.application.spotify.parser.playlist import TrackList
from os import removedirs

def getPlaylistSongChoices(playlistUrl, console: Console, userDir: str, shutdownEvent: Event):
        proxyManager = ProxyManager(userDir, PROXY_FILE_LISTENER)
        driverManager = DriverManager(console, shutdownEvent=shutdownEvent)
        driverData = driverManager.getDriver('chrome', 1, {}, proxyManager.getRandomProxy(), headless=True)
        spotify = Spotify.Adapter(driver=driverData['driver'], console=console, shutdownEvent=shutdownEvent)
        playlist = TrackList(spotify, playlistUrl)
        playlist.load()
        songs = playlist.getTracks()
        choice = []
        index = 0
        for song in songs:
            choice.append({
                'name': song.getName(),
                'value': index
            })
            index +=1
        driverData['driver'].quit()
        try:
            removedirs(driverData['userDataDir'])
        except:
            pass
        return choice