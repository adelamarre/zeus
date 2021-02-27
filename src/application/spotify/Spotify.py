from multiprocessing import Event, synchronize
from src.application.AbstractAdapter import AbstractAdapter
import time
from selenium.common.exceptions import NoSuchElementException
from random import randint, choice
from time import sleep
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
import json
from requests import post
from src.services.console import Console

WEBPLAYER_URL = 'https://open.spotify.com/'
LOGIN_URL = 'https://accounts.spotify.com/en/login'
SIGNUP_URL = 'https://www.spotify.com/fr/signup'

class Adapter(AbstractAdapter):
    def __init__(self, driver, console: Console, shutdownEvent: synchronize.Event):
        AbstractAdapter.__init__(self,driver=driver, shutdownEvent=shutdownEvent)
        self.console = console
        
    def getMyIp(self):
        #self.driver.get('https://api.myip.com/')
        #self.driver.get('https://ipapi.co/json/')
        self.driver.get('https://ip.lafibre.info/')
        try:
            #json_str = self.driver.execute_script("return document.body.outerText")
            
            ip_v4 = self.driver.find_element_by_xpath('/html/body/ul[1]/li[1]/span/strong[2]').text
            ip_v6 =  self.driver.find_element_by_xpath('/html/body/ul[1]/li[3]/span/strong[2]').text
            return 'ip v4: %s, ip v6: %s' % (ip_v4, ip_v6)
            #self.console.log(json_str)
            #result = json.loads(json_str)
            #if 'ip' in result:
            #    return result['ip']
            #else:
            #    return 'unknown'
        except Exception as e:
            self.saveScreenshot(str(e))
            self.console.exception()
        
    def getClientInfo(self, mirrorServerUrl):
        self.driver.get(mirrorServerUrl)
        result = {}
        try:
            json_str = self.driver.execute_script("return document.body.outerHTML;").replace('<body>', '').replace('</body>', '').replace('</address>', '') 
            result = json.loads(json_str)
        except:
            return {'raw': json_str}
        return result
    
    def navigate(self, url):
        self.driver.get(url)
        ''' for request in self.driver.requests:
            if request.url == url:
                if request.response:
                    statusCode = int(request.response.response_status_code)
                    if statusCode > 399:
                        self.console.error('Response status code : %d' %  statusCode)
                        return False
                else:
                    self.console.error('Empty response from : %s' %  url)
                    return False '''
        return True
    
    # returns the status of the account's login
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
            
        #
        ##account-settings-link
        #
        #
        #<p class="alert alert-warning" role="status" aria-live="polite">
        #  <!-- ngIf: !response.error -->
        #  <!-- ngIf: response.error --><span ng-if="response.error" ng-bind-html="response.error | localize:responseArguments" class="ng-binding ng-scope">Nom d'utilisateur ou mot de passe incorrect.</span><!-- end ngIf: response.error -->
        #</p>
        # check whether or not the login was successful
        #self.getElementById('mh-usericon-title')
        

    def logout(self):
        self.driver.get('https://www.spotify.com/logout')
        time.sleep(5)

    def playPlaylist(self, playlist_url, shutDownEvent: Event, min_listening_time = 70, max_listening_time = 110):
        
        #Navigate to the play list
        self.driver.get(playlist_url)
        
        # Cookie banner
        if self.sleep(5): return
        cookieBannerButton = self.getElementById('onetrust-accept-btn-handler', 5, 1, element= None, raiseException = False)
        if cookieBannerButton:
            try:
                cookieBannerButton.click()
            except:
                pass

        #Press Play button
        if self.sleep(3): return
        self.clickElementByXpath('//*[@id="main"]/div/div[2]/div[3]/main/div[2]/div[2]/div/div/div[2]/section/div[2]/div[2]/div/button[1]')
        
        #Wait music play
        listenTime = randint(min_listening_time, max_listening_time)
        if self.sleep(listenTime): return
        
        # Cookie banner
        if self.sleep(5): return
        cookieBannerButton = self.getElementById('onetrust-accept-btn-handler', 5, 1, element= None, raiseException = False)
        if cookieBannerButton:
            try:
                cookieBannerButton.click()
            except:
                pass

        #Press next button
        bnextContainer = self.getElementByXpath('//*[@class="player-controls__buttons"]', 1, 2)
        bnext = self.getElementByXpath('//button[@aria-label="Next"]', 1, 2, bnextContainer)
        bnext.click()
        
        #Wait after next button pressed before quit
        self.sleep(randint(5, 8))
        
         

    
    def savePlaylist(self):
        # click the like button
        try:
            like_button = self.driver.find_element_by_xpath(
                '//div[@class="spoticon-heart-32"]/..')
            like_button.click()
            time.sleep(self.wait_increment)
        except NoSuchElementException:
            pass

    def follow(self, url):
        self.driver.get(url)
        time.sleep(self.wait_increment)

        # click the follow button
        try:
            follow_btn = self.driver.find_element_by_xpath(
                '//button[@class="ff6a86a966a265b5a51cf8e30c6c52f4-scss"]')
            follow_btn.click()
            time.sleep(self.wait_increment)
        except NoSuchElementException:
            print(f"Already following artist at {url}")

    def close(self):
        self.driver.quit()

    def register(self, user, day_value = randint(1, 28), month_value = randint(1, 12), year_value = randint(1970, 2005), gender = choice(['male', 'female'])):
        
        
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
    
        # submit
        if self.sleep(1): return
        submit = self.driver.find_element_by_xpath('//button[@class="Button-oyfj48-0 fivrVz SignupButton___StyledButtonPrimary-cjcq5h-1 gzFCtx"]')
        submit.click()
        sleep(10)
        
        # Error class = LinkContainer-sc-1t58wcv-0
        # InputErrorMessage__Container-tliowl-0
        # InputErrorMessage__Container-tliowl-0


    def registerApi(self, user, day_value = randint(1, 28), month_value = randint(1, 12), year_value = randint(1970, 2005), gender = choice(['male', 'female'])):

        headers = {'User-agent': 'S4A/2.0.15 (com.spotify.s4a; build:201500080; iOS 13.4.0) Alamofire/4.9.0', 'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8', 'Accept': 'application/json, text/plain;q=0.2, */*;q=0.1', 'App-Platform': 'IOS', 'Spotify-App': 'S4A', 'Accept-Language': 'en-TZ;q=1.0', 'Accept-Encoding': 'gzip;q=1.0, compress;q=0.5', 'Spotify-App-Version': '2.0.15'}
        data = 'creation_point=lite_7e7cf598605d47caba394c628e2735a2&password_repeat=%s&platform=Android-ARM&iagree=true&password=%s&gender=%s&key=a2d4b979dc624757b4fb47de483f3505&birth_day=%s&birth_month=%s&email=%s&birth_year=%s' % (user['password'], user['password'], gender, day_value, month_value, user['email'], year_value)
        
        proxy = user['proxy']
        if proxy:
            if 'password' in proxy:
                proxies = { 'https' : 'http://%s:%s@%s:%s' % (proxy['username'], proxy['password'], proxy['host'], proxy['port']) } 
            else:
                proxies = { 'https' : 'http://%s:%s' % (proxy['host'], proxy['port']) } 
        else:
            proxies = {}

        try:
            create = post('https://spclient.wg.spotify.com/signup/public/v1/account', data = data, headers = headers, proxies = proxies, timeout = 5)
            result = create.json()
            if result['status'] == 1:
                username = result['username']
                if username != '':
                    self.console.log( "Account created for %s" % user['email'] )
                    return True
        except:
            self.console.exception()

        return False
