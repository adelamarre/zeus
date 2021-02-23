from multiprocessing import Event
from threading import current_thread

import os

import time
from selenium.common.exceptions import JavascriptException, NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from random import randint, choice
from selenium.webdriver.common.by import By
from time import sleep
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
import json
from requests import post
from ...services.tasks import TaskContext
import traceback
from src.services.console import Console
from seleniumwire import webdriver
from os import path
WEBPLAYER_URL = 'https://open.spotify.com/'
LOGIN_URL = 'https://accounts.spotify.com/en/login'
SIGNUP_URL = 'https://www.spotify.com/fr/signup'

class Adapter:
    def __init__(self, driver, console: Console, shutdownEvent: Event, batchId: int  = 0):
        self.driver: WebDriver = driver
        self.console = console
        self.shutdownEvent = shutdownEvent
        self.screenshotDir = (path.dirname(__file__) or '.') + ('/../../../temp/%d/' % batchId)
        os.makedirs(self.screenshotDir, exist_ok=True)
        
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
        try:
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
        except:
            self.console.exception()
            return False


    # returns the status of the account's login
    def login(self, email, password):
        if not self.navigate(LOGIN_URL):
            return False
        self.wait_increment = 5
        time.sleep(self.wait_increment)

        try:
            username_field = self.driver.find_element_by_xpath('//input[@name="username"]')
        except NoSuchElementException:
            try:
                _ = self.driver.find_element_by_xpath(
                    '//a[@id="account-settings-link"]')
                print(f"{email} already logged in")
                return True
            except NoSuchElementException:
                print(f"Issue in browser opened with {email}")
                return False

        username_field.send_keys(email)
        sleep(3)
        password_field = self.driver.find_element_by_xpath('//input[@name="password"]')
        password_field.send_keys(password)

        login_button = self.driver.find_element_by_xpath(
            '//button[@id="login-button"]')
        login_button.click()
        time.sleep(self.wait_increment)

        # check whether or not the login was successful
        success = True
        try:
            _ = self.driver.find_element_by_xpath('//p[@role="status"]')
            success = False
        except NoSuchElementException:
            pass

        return success

    def logout(self):
        self.driver.get('https://www.spotify.com/logout')
        time.sleep(5)

    def playPlaylist(self, playlist_url, shutDownEvent: Event, min_listening_time = 70, max_listening_time = 110):
        try:
            if not self.navigate(playlist_url):
                return False
            
            # play it!!!
            # Cookie banner
            sleep(2)
            try:
                self.clickElementById('onetrust-accept-btn-handler')
                #element = WebDriverWait(self.driver, 30).until(
                #    EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler"))
                #)
                #sleep(2)
                #js_script = "document.getElementById( 'onetrust-accept-btn-handler' ).click();"
                #self.driver.execute_script( js_script )
            except:
                pass
            if shutDownEvent.is_set():
                return False
            sleep(3)
            
            #Press Play button
            if not self.pressPlayButton():
                return False
            
            listenTime = randint(min_listening_time, max_listening_time)
            startListen = time.time()

            #Listen music
            while not shutDownEvent.is_set():
                time.sleep(1)
                since = (time.time()-startListen)
                if self.shutdownEvent.is_set():
                    return False
                if since > listenTime:
                    break

            if shutDownEvent.is_set():
                return False

            if not self.pressNextButton():
                return False

            if shutDownEvent.is_set():
                return False
            sleep(randint(5, 8))
            return True
        except Exception as e:
            self.saveScreenshot(str(e))
            self.console.exception()
        return False


    def clickByXpath(self, path, maxTry=30, waitPerTry=1):
        while True: #not self.context.shutdownEvent.is_set():
            sleep(waitPerTry)
            try:
                self.driver.find_element_by_xpath(path).click()
                break
            except:
                pass
            if maxTry:
                maxTry -= 1
            else:
                return False    
        return True

    def getElementByXpath(self, path, maxTry=30, waitPerTry=1):
        while True: #not self.context.shutdownEvent.is_set():
            sleep(waitPerTry)
            try:
                element = self.driver.find_element_by_xpath(path)
                return element
            except:
                pass
            if maxTry:
                maxTry -= 1
            else:
                return False    
        return True

    def getElementByTagName(self, tagname, element=None, maxTry=30, waitPerTry=1):
        while True: #not self.context.shutdownEvent.is_set():
            sleep(waitPerTry)
            try:
                if element:
                    result = element.find_element_by_tag_name(tagname)
                else:
                    result = self.driver.find_element_by_tag_name(tagname)
                break
            except:
                pass
            if maxTry:
                maxTry -= 1
            else:
                return False    
        return True

    def clickElementById(self, id, maxTry=30, waitPerTry=2):
        while True: #not self.context.shutdownEvent.is_set():
            sleep(waitPerTry)
            try:
                element = self.driver.find_element_by_id(id)
                element.click()
                return True
            except:
                pass
            if maxTry:
                maxTry -= 1
            else:
                return False    
        

    def pressPlayButton(self):
        #dataGaAction =  self.getElementByXpath('//a[@data-ga-action="play"]')
        #if dataGaAction:
        #    dataGaAction.click()
        #    dataTestId = self.getElementByXpath('//button[@data-testid="play-button"]')
        #    if dataTestId:
        #        svg = self.getElementByTagName('svg', dataTestId)
        #        if svg:
        dataTestId = self.getElementByXpath('//*[@id="main"]/div/div[2]/div[3]/main/div[2]/div[2]/div/div/div[2]/section/div[2]/div[2]/div/button[1]')
        if dataTestId:
            #title = dataTestId.get_attribute('title')
            #if 'Play' == title:
            dataTestId.click()
            return True
        return False    

    

    def pressNextButton(self):
        #dataGaAction =  self.getElementByXpath('//a[@data-ga-action="play"]')
        #if dataGaAction:
        #    dataGaAction.click()
        #    dataTestId = self.getElementByXpath('//button[@data-testid="play-button"]')
        #    if dataTestId:
        #        svg = self.getElementByTagName('svg', dataTestId)
        #        if svg:
        while True:
            if self.shutdownEvent.is_set():
                return False
            sleep(1)
            bnext = self.driver.find_element_by_xpath('//*[@class="player-controls__buttons"]')
            bnext.find_element_by_xpath('//button[@aria-label="Next"]').click() # aria-label="Previous"

            try:
                self.driver.find_element_by_xpath('//button[@data-testid="control-button-pause"]')
                #self.context.console.log('Click next!')
                break
            except:
                pass
        return True

        #dataTestId = self.getElementByXpath('//*[@id="main"]/div/div[2]/div[2]/footer/div/div[2]/div/div[1]/button[4]')
        #if dataTestId:
            #title = dataTestId.get_attribute('title')
            #if 'Play' == title:
        #    dataTestId.click()
        #    return True
        #return False

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
        #print("\r" + "Task : {}".format(str(os.getpid()))) 
        try:
            if self.shutdownEvent.is_set():
                return False
            self.driver.get( SIGNUP_URL )
            self.driver.maximize_window()
            if self.shutdownEvent.is_set():
                return False
            sleep(3)
            email_field = self.driver.find_element_by_id( "email" )
            email_field.send_keys(user['email'])
            
            confirm_field = self.driver.find_element_by_id( "confirm" )
            confirm_field.send_keys(user['email'])
            #sleep(2)
            password_field = self.driver.find_element_by_id( "password" )
            password_field.send_keys(user['password'])
            #sleep(2)
            username_field = self.driver.find_element_by_id( "displayname" )
            username_field.send_keys(user['displayName'])
            #sleep(2)
            birth_day_field = self.driver.find_element_by_id( "day" )
            birth_day_field.send_keys(day_value )
            
            birth_month_field = Select(self.driver.find_element_by_id( "month" ))
            birth_month_field.select_by_index( month_value)
            
            birth_year_field = self.driver.find_element_by_id( "year" )
            birth_year_field.send_keys(year_value)
            
            # scroll
            html = self.driver.find_element_by_tag_name('html')
            html.send_keys(Keys.END)
            sleep(2)
            if self.shutdownEvent.is_set():
                return False
            gender_list = ["Male", "Femal", "Non-binary"]
            gender_field = self.driver.find_element_by_name("gender")
            gender_field = self.driver.find_element_by_xpath('//*[@id="__next"]/main/div[2]/form/div[6]/div[2]/label[1]')
            gender_field.send_keys(gender_list[randint(0, 2)])
            gender_field.click()
            
            third_party = self.driver.find_elements_by_xpath('//span[@class="LinkContainer-sc-1t58wcv-0 iqOoUm"]')[0].click()
            sleep(1)
            if self.shutdownEvent.is_set():
                return False
            # Bypass captcha
            cp = self.driver.find_element_by_xpath('//input[@data-testid="recaptcha-input-test"]')
            self.driver.execute_script("arguments[0].hidden = arguments[1]", cp, "")
            cp.send_keys(1)
            if self.shutdownEvent.is_set():
                return False
            # scroll
            html = self.driver.find_element_by_tag_name('html')
            html.send_keys(Keys.END)
            sleep(2)
            if self.shutdownEvent.is_set():
                return False
            # Cookie banner
            try:
                #third_party = self.driver.find_elements_by_xpath('//button[@class="onetrust-close-btn-handler onetrust-close-btn-ui banner-close-button onetrust-lg ot-close-icon"]')[0].click()
                third_party = self.driver.find_elements_by_xpath('//button[@id="onetrust-accept-btn-handler"]')[0].click()
            except:
                pass
            sleep(2)
            if self.shutdownEvent.is_set():
                return False
            # submit
            submit = self.driver.find_element_by_xpath('//button[@class="Button-oyfj48-0 fivrVz SignupButton___StyledButtonPrimary-cjcq5h-1 gzFCtx"]').click()
            sleep(10)
            
            return True
        except Exception as e:
            self.saveScreenshot(str(e))
            self.console.exception()
            

        return False

    def saveScreenshot(self, message = None):
        try:
            id = randint(10000, 99999)
            if message:
                with open(self.screenshotDir + ('%d-error.log' % id), 'w') as f:
                    f.write(message)
            self.driver.save_screenshot(self.screenshotDir  + ('%d-screenshot.png' % id))
        except:
            self.console.exception()


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
