import json
from multiprocessing import Queue, synchronize
from random import choice, randint

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from src.application.adapters import AbstractAdapter
from src.application.spotify.parser.playlist import TrackList, TrackSelector
from src.application.spotify.stats import ListenerStat
from src.application.statscollector import StatsCollector
from src.services.console import Console

WEBPLAYER_URL = 'https://open.spotify.com/'
LOGIN_URL = 'https://accounts.spotify.com/en/login'
SIGNUP_URL = 'https://www.spotify.com/fr/signup'

class Adapter(AbstractAdapter):
    def __init__(self, driver, console: Console, shutdownEvent: synchronize.Event):
        AbstractAdapter.__init__(self,driver=driver, shutdownEvent=shutdownEvent)
        self.console = console
        
    def getClientInfo(self, mirrorServerUrl):
        self.driver.get(mirrorServerUrl)
        result = {}
        try:
            json_str = self.driver.execute_script("return document.body.outerHTML;").replace('<body>', '').replace('</body>', '').replace('</address>', '') 
            result = json.loads(json_str)
        except:
            return {'raw': json_str}
        return result
    
    def login(self, email, password):
        self.driver.get(LOGIN_URL)
        
        #Username (email)
        if self.sleep(2): return
        username_field = self.getElementByXpath('//input[@name="username"]')
        username_field.send_keys(email)

        #Password
        if self.sleep(2): return
        password_field = self.getElementByXpath('//input[@name="password"]')
        password_field.send_keys(password)

        #Press login button
        if self.sleep(2): return
        self.clickElementByXpath('//button[@id="login-button"]')
        
        if self.sleep(10): return

        maxTry = 20
        while True:
            if self.shutdownEvent.is_set():
                return
            errorElements = self.getElementsByClass('alert', maxTry=1, raiseException=False)
            if errorElements:
                raise Exception('Login failed')
            loggedInElements = self.getElementById('account-settings-link', maxTry=1, raiseException=False)
            if loggedInElements:
                break
            maxTry -=1
            if maxTry == 0:
                raise Exception('Login timeout')
        
    def play(self, user: dict, playlistUrl: str, playConfig: str, statsCollector: StatsCollector, statsQueue: Queue = None, contractId:str=None):
        
        playlist = TrackList(self, playlistUrl)
        playlist.load()
        playlistName = playlist.getName()
        songs = playlist.getTracks()
        totalSongs = len(songs)

        if totalSongs == 0:
            raise Exception('No song were found in playlist %s' % playlistName)
    
        selector = TrackSelector()
        selector.parse(config=playConfig, totalTracks=totalSongs)
        selection = selector.getSelection()
        self.console.log(f'Play config: {playConfig:s}')
        self.console.log(selection)

        for index in selection:
            song = songs[index]
            artistName = song.getArtist()
            songName = song.getName()
            self.console.log(f'Start Playing {songName} from {artistName}')
            playDuration = song.play(80, 100)
            self.console.log(f'Played {songName} {playDuration:d} seconds' )
            if statsQueue:
                statsQueue.put((ListenerStat.PLAYED, +1))
            if statsCollector:
                self.console.log(f'Send statistics to collector')
                
                statsCollector.songPlayed(
                    user=user,
                    playlistUrl=playlistUrl,
                    playlistName=playlistName,
                    trackName=songName,
                    artistName=artistName,
                    playDuration=playDuration,
                    contractId=contractId
                )
        self.console.log(f'Click next...' )
        playlist.next()
        self.sleep(randint(3, 4))

    def clickCookieBanner(self):
        cookieBannerButton = self.getElementById('onetrust-accept-btn-handler', 30, 1, element= None, raiseException = False)
        if cookieBannerButton:
            try:
                cookieBannerButton.click()
            except:
                pass
    
    def fillingOutSubscriptionForm(self, user, day_value = randint(1, 28), month_value = randint(1, 12), year_value = randint(1970, 2005), gender = choice(['male', 'female'])):
        
        
        #Navigate to the signup page
        self.driver.get( SIGNUP_URL )
        if self.sleep(3): return
        self.driver.maximize_window()
        
        #Email
        if self.sleep(1): return
        email_field = self.getElementById( "email" )
        email_field.send_keys(user['email'])
        
        #Email confirmation
        if self.sleep(1): return
        confirm_field = self.driver.find_element_by_id( "confirm" )
        confirm_field.send_keys(user['email'])

        #Password
        if self.sleep(1): return
        password_field = self.driver.find_element_by_id( "password" )
        password_field.send_keys(user['password'])
        
        #Display name
        if self.sleep(1): return
        username_field = self.driver.find_element_by_id( "displayname" )
        username_field.send_keys(user['displayName'])
        
        #Day
        if self.sleep(1): return
        birth_day_field = self.driver.find_element_by_id( "day" )
        birth_day_field.send_keys(day_value )
        
        #Month
        if self.sleep(1): return
        birth_month_field = Select(self.driver.find_element_by_id( "month" ))
        birth_month_field.select_by_index( month_value)
        
        #Year
        if self.sleep(1): return
        birth_year_field = self.driver.find_element_by_id( "year" )
        birth_year_field.send_keys(year_value)
        
        # scroll
        html = self.driver.find_element_by_tag_name('html')
        html.send_keys(Keys.END)
        if self.sleep(2): return

        #Gender
        if self.sleep(1): return
        gender_list = [
        '//*[@id="__next"]/main/div[2]/form/div[6]/div[2]/label[1]/span[2]',
        '//*[@id="__next"]/main/div[2]/form/div[6]/div[2]/label[2]/span[2]',
        '//*[@id="__next"]/main/div[2]/form/div[6]/div[2]/label[3]/span[2]',
        ]
        selector = randint(1,100)
        if selector <= 49: #49% male, #49% female, 2% no binary
            selector = 0 
        elif selector <= 98:
            selector = 1
        else:               
            selector = 2
        span = self.getElementByXpath(gender_list[selector])
        span.click()
        
        #Third party
        if self.sleep(1): return
        third_party = self.driver.find_elements_by_xpath('//span[@class="LinkContainer-sc-1t58wcv-0 iqOoUm"]')[0].click()
        
        
        # Bypass captcha
        if self.sleep(1): return
        cp = self.getElementByXpath('//input[@data-testid="recaptcha-input-test"]')
        self.driver.execute_script("arguments[0].hidden = arguments[1]", cp, "")
        cp.send_keys(1)
        
        # scroll
        if self.sleep(1): return
        html = self.getElementByTagName('html')
        html.send_keys(Keys.END)
        
        if self.sleep(1): return
        third_party = self.getElementById('onetrust-accept-btn-handler', maxTry = 10, raiseException = False)
        if third_party:
            third_party.click()
        
    def submitSubscriptionForm(self):
        # submit
        if self.sleep(1): return
        submit = self.getElementByXpath('//button[@class="Button-oyfj48-0 fivrVz SignupButton___StyledButtonPrimary-cjcq5h-1 gzFCtx"]',
            maxTry=10, waitPerTry=2
        )
        submit.click()
        
        maxTry = 40
        while True:
            if self.sleep(2): return
            ############################
            # ACCOUNT ERROR ELEMENTS
            ###########################
            errorElements = self.getElementsByClass('InputErrorMessage__Container-tliowl-0', maxTry=1, raiseException=False)
            if errorElements:
                raise Exception('Account creation failed')
            ############################
            # ACCOUNT VALID ELEMENTS
            ###########################
            # Welcome page
            loggedInElements = self.getElementsByClass('mh-header-primary', maxTry=1, raiseException=False)
            if loggedInElements:
                break
            # User menu button
            loggedInElements = self.getElementsByCssSelector('button[data-testid="user-widget-link"', maxTry=1, raiseException=False)
            if loggedInElements:
                break
            # Drm error page
            loggedInElements = self.getElementsByClass('ErrorPage', maxTry=1, raiseException=False)
            if loggedInElements:
                #Drm error page show up but we considere the account valid anyway
                break
            maxTry -=1
            if maxTry == 0:
                raise Exception('Account creation timeout')

    