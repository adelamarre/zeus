
from multiprocessing import Event
from random import choice, randint, sample
from selenium.webdriver.remote.webelement import WebElement
from src.application.parsers import AbstractParser
from src.application.adapters import AbstractAdapter
from selenium.webdriver.common.keys import Keys
from typing import AbstractSet, List
from time import sleep, time
from selenium.webdriver.common.action_chains import ActionChains

class TrackSelector:
    def __init__(self) -> None:
        self.indexes = []
        self.counters = []
        self.songAsked = 0

    def parse(self, config: str, totalTracks):
        
        self.indexes = []
        self.counters = []

        configParts = config.split(':')

        selectionConfig = configParts[0]
        counterConfig = configParts[1]
        indexes = []
        if selectionConfig == '':
            self.indexes = [0]
            self.counters = [1]
            return
        elif selectionConfig == '*':
            indexes = list(range(totalTracks))
        else:
            for selection in selectionConfig.split(','):
                indexRange = selection.split('-')
                if len(indexRange) == 1:
                    min = int(indexRange[0])
                    if min < 1:
                        raise Exception('Song index could not be 0. Index Start at 1.')
                    indexes += [min-1]
                elif len(indexRange) >= 2:
                    min = int(indexRange[0])
                    if min < 1:
                        raise Exception('Song index could not be 0. Index Start at 1.')
                    max = int(indexRange[1])
                    if max > totalTracks:
                        max = totalTracks
                    if min > max:
                        min = max
                    indexes += list(range(min-1, max))
        
        #Remove duplicate     
        for index in indexes:
            if index not in self.indexes:
                self.indexes.append(index)

        availableSongs = len(self.indexes)
        if counterConfig == '':
            self.counters = [1]
        else:
            counterRange = counterConfig.split('-')
            if len(counterRange) == 1:
                min = int(counterRange[0])
                if min > availableSongs:
                    min = availableSongs
                self.counters = [min]
            elif len(counterRange) >= 2:
                min = int(counterRange[0])
                max = int(counterRange[1])
                if max > availableSongs:
                    max = availableSongs
                if min > max:
                    min = max
                self.counters = list(range(min, max+1))
        self.count = choice(self.counters)

    def getSelection(self):
        return sample(population=self.indexes, k=choice(self.counters))

    def validateCounterConfig(value):
        try:
            parts = value.split('-')
            if len(parts) == 1:
                if int(parts[0]) < 1:
                    return 'You must at least listen one song...'
            elif len(parts) >= 2:
                min = int(parts[0])
                max = int(parts[1])
                if int(min) < 1:
                    return 'Invalid value: number must be greater than 0'
                if min > max:
                    return 'Min value must be lower than max value'
            return True
        except Exception as e:
            return 'Invalid format: <minimum>[-<maximum>]' 

class Player(AbstractParser):
    def __init__(self, adapter: AbstractAdapter) -> None:
        super().__init__(adapter)
        self.positionElement: WebElement = None
        self.durationElement: WebElement = None


    def getDuration(self):
        if self.durationElement is None:
            durations = self.adapter.getElementsByCssSelector('div[data-testid="playback-duration"]')
            if len(durations) > 0:
                self.durationElement = durations[0]
        if self.durationElement:
            try:
                [m,s] = self.durationElement.text.strip().split(':')
                return int(m)*60 + int(s)
            except:
                return -1
        return -1

    def getPosition(self):
        if self.positionElement is None:
            positions = self.adapter.getElementsByCssSelector('div[data-testid="playback-position"]')
            if len(positions) > 0:
                self.positionElement = positions[0]
        
        if self.positionElement:
            try:
                [m,s] = self.positionElement.text.strip().split(':')
                return int(m)*60 + int(s)
            except:
                return -1
        return -1

class Track:
    def __init__(self, rowElement: WebElement, player: Player) -> None:
        self.rowElement = rowElement
        self.player = player
        self.cells: List[WebElement]= None
        pass

    def getCells(self):
        if self.cells is None:
            self.cells = self.rowElement.find_elements_by_css_selector('div[role="gridcell"]')
        return self.cells

    def getName(self):
        cells = self.getCells()
        if len(cells):
            cell = cells[1].find_element_by_xpath('div/div/span/span')
            if cell:
                return cell.text
        return 'unknown'
    def getArtist(self):
        cells = self.getCells()
        if len(cells):
            cell = cells[1].find_element_by_xpath('div/span/a/span/span')
            if cell:
                return cell.text
        return 'unknown'

    def play(self, min:int, max:int):
        cell = self.getCells()[0]
        if not cell:
            raise Exception('Could not find gridcell 0 in playlist row')
        
        playButton: WebElement = cell.find_element_by_tag_name('button')
        if not playButton:
            raise Exception('Could not find button in gridcell 0 in playlist row')
        label = playButton.get_attribute("aria-label")

        if label != 'Pause':
            hover = ActionChains(self.player.adapter.driver).move_to_element(self.rowElement)
            hover.perform()
            if self.player.adapter.sleep(1): return -1
            playButton.click()
            if self.player.adapter.sleep(1): return -1

        playTime = randint(min, max)
        startTime = time()
        while not self.player.adapter.sleep(2):
            currentPosition = int(time() - startTime)
            if currentPosition >= playTime:
                return currentPosition
        
class TrackList(AbstractParser):
    def __init__(self, adapter: AbstractAdapter, playlistUrl: str, playConfig: str = '1:1') -> None:
        super().__init__(adapter)
        self.playlistUrl = playlistUrl
        self.player = Player(self.adapter)
        self.name = None
        self.tracks: List[Track] = None
        
    def load(self):
        self.adapter.driver.get(self.playlistUrl)
        if self.adapter.sleep(3): return True
        coockieBanner = self.adapter.getElementById('onetrust-accept-btn-handler', 10, 2, element= None, raiseException = False)
        if coockieBanner:
            if self.adapter.sleep(5): return
            coockieBanner.click()
        
    def getName(self):
        if self.name is None:
            titles = self.adapter.getElementsByTagName('h1')
            if len(titles) == 2:
                self.name = titles[1].text
        return self.name

    def getTracks(self) -> List[Track]:
        if self.tracks is None:
            rows = self.adapter.getElementsByCssSelector('div[data-testid="tracklist-row"]')
            if rows:
                self.tracks = []
                for row in rows:
                    self.tracks.append(Track(row, self.player))
                    
        return self.tracks

    def next(self):
         #Press next button
        bnextContainer = self.adapter.getElementByXpath('//*[@class="player-controls__buttons"]', 1, 2)
        bnext = self.adapter.getElementByXpath('//button[@aria-label="Next"]', 1, 2, bnextContainer)
        bnext.click()
        
        
        
