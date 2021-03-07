

from logging import fatal
from multiprocessing import Event, synchronize
from selenium.webdriver.remote.webdriver import WebDriver
from time import sleep, time

from selenium.webdriver.remote.webelement import WebElement

class AbstractAdapter:
    def __init__(self, driver: WebDriver, shutdownEvent: synchronize.Event) -> None:
        self.driver = driver
        self.shutdownEvent = shutdownEvent

    def sleep(self, secondes: int) -> bool:
        startSleep = time()
        while True:
            sleep(1)
            if self.shutdownEvent.is_set():
                return True
            if (time() - startSleep) > secondes:
                break
        return False

    def clickElementByXpath(self, path, maxTry=30, waitPerTry=1):
        exit = False
        while not exit: #not self.context.shutdownEvent.is_set():
            try:
                self.driver.find_element_by_xpath(path).click()
                break
            except Exception as e:
                if maxTry:
                    maxTry -= 1
                else:
                    raise e
            exit = sleep(waitPerTry)

    def getElementsByCssSelector(self, selector, maxTry=30, waitPerTry=1, raiseException: bool = True):
        exit = False
        while not exit: #not self.context.shutdownEvent.is_set():
            try:
                element = self.driver.find_elements_by_css_selector(selector)
                return element
            except Exception as e:
                maxTry -= 1
                if maxTry == 0:
                    if raiseException:
                        raise e
                    else:
                        break
            exit = self.sleep(waitPerTry)
        return None

    
    def getElementsByClass(self, classname, maxTry=30, waitPerTry=1, raiseException: bool = True) -> WebElement:
        exit = False
        while not exit: #not self.context.shutdownEvent.is_set():
            try:
                element = self.driver.find_elements_by_class_name(classname)
                return element
            except Exception as e:
                maxTry -= 1
                if maxTry == 0:
                    if raiseException:
                        raise e
                    else:
                        break
            exit = self.sleep(waitPerTry)
        return None

    def getElementByXpath(self, path, maxTry=30, waitPerTry=1, container: WebElement = None, raiseException: bool = True) -> WebElement:
        exit = False
        while not exit: #not self.context.shutdownEvent.is_set():
            try:
                if container:
                    element = container.find_element_by_xpath(path)
                else:
                    element = self.driver.find_element_by_xpath(path)
                return element
            except Exception as e: 
                maxTry -= 1
                if maxTry == 0:
                    if raiseException:
                        raise e
                    else:
                        break
            exit = self.sleep(waitPerTry)
        return None

    def getElementByTagName(self, tagname, element: WebElement=None, maxTry=30, waitPerTry=1, raiseException: bool = True):
        exit = False
        while not exit: #not self.context.shutdownEvent.is_set():
            try:
                if element:
                    result = element.find_element_by_tag_name(tagname)
                else:
                    result = self.driver.find_element_by_tag_name(tagname)
                return result
            except Exception as e:
                maxTry -= 1
                if maxTry == 0:
                    if raiseException:
                        raise e
                    else:
                        break
            exit = self.sleep(waitPerTry)

    def getElementsByTagName(self, tagname, element: WebElement=None, maxTry=30, waitPerTry=1, raiseException: bool = True):
        exit = False
        while not exit: #not self.context.shutdownEvent.is_set():
            try:
                if element:
                    result = element.find_elements_by_tag_name(tagname)
                else:
                    result = self.driver.find_elements_by_tag_name(tagname)
                return result
            except Exception as e:
                maxTry -= 1
                if maxTry == 0:
                    if raiseException:
                        raise e
                    else:
                        break
            exit = self.sleep(waitPerTry)

    def getElementById(self, id: str, maxTry: int = 30, waitPerTry: int = 2, element: WebElement = None, raiseException = True) -> WebElement:
        exit = False
        while not exit:
            try:
                if element:
                    result = element.find_element_by_id(id)
                else:
                    result = self.driver.find_element_by_id(id)
                return result
            except Exception as e:
                maxTry -= 1
                if maxTry == 0:
                    if raiseException:
                        raise e
                    else:
                        break
            exit = self.sleep(waitPerTry)
    
    def clickElementById(self, id, maxTry=30, waitPerTry=2):
        exit = False
        while not exit:
            try:
                element = self.driver.find_element_by_id(id)
                element.click()
                break
            except Exception as e:
                if maxTry:
                    maxTry -= 1
                else:
                    raise e
            exit = self.sleep(waitPerTry)