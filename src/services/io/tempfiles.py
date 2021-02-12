import os
import shutil
import tempfile

class TemporaryFile:
    def __init__(self, basepath=(os.path.dirname(__file__) or '.')):
        self.basepath = basepath
        self.files = []

    def addFile(self, file):
        self.files.append(file)
    
    def purge(self):
        for file in self.files:
            os.remove(file)

class TemporaryFolder:
    def __init__(self, basepath=(os.path.dirname(__file__) or '.')):
        self.basepath = basepath
        self.folders = []

    def addFile(self, file):
        self.folders.append(file)
    
    def purge(self):
        for folder in self.folders:
            shutil.rmtree(folder, ignore_errors=True)