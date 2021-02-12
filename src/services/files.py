import os
import sys
import json

class FileManager:
    def __init__(self, basePath=(os.path.dirname(__file__) or '.')):
        self.basePath = basePath

    def loadTextFile(self, filename):
        path = self.basePath + '/' + filename
        result = []
        try:    
            with open(path, 'r') as lines:
                for line in lines:
                    l = line.strip()
                    if l :
                        result.append(line.strip()) 
        except FileNotFoundError:
            print('Error: File %s not found' % path)
        except:
            print("Error during file loading : ", sys.exc_info()[0])
        finally:
            return result
    
    def loadJsonFile(self, filename):
        result = []
        path = self.basePath + '/' + filename
        try:    
            
            with open(path, 'r') as lines:
                result = json.load(lines)
        except FileNotFoundError:
            print('Error: File %s not found' % path)
        except:
            print("Error during file loading : ", sys.exc_info()[0])
        finally:
            return result
    
       