from sys import stdout
from os import get_terminal_size
from colorama import Fore, Style
import re 

class Terminal:

    def __init__(self, charSeparator: str) -> None:
        self.lines = []
        self.charSeparator = charSeparator
        self.width, self.height = get_terminal_size()
        self.separator = charSeparator * self.width

    def clear(self):
        self.append('\u001b[2J', 0)

    def appendHeader(self, version, color = Fore.BLUE):
        self.append('''%s
 __     __                           ____        _   
 \ \   / /__ _ __   ___  _ __ ___   | __ )  ___ | |_ 
  \ \ / / _ \ '_ \ / _ \| '_ ` _ \  |  _ \ / _ \| __|
   \ V /  __/ | | | (_) | | | | | | | |_) | (_) | |_ 
    \_/ \___|_| |_|\___/|_| |_| |_| |____/ \___/ \__|
                                       %sversion: %s%s
''' % (color, Fore.WHITE, version, Fore.RESET), forward=8)

    def newPage(self):
        self.lines = []  
        self.width, self.height = get_terminal_size()
        self.separator = self.charSeparator * self.width
        self.clear()

    def append(self, text: str = '', forward=1):
        self.lines.append((text, forward))
    
    def appendTemplate(self, template: str, data, valueColor: str =  Fore.CYAN, textColor: str = Fore.LIGHTWHITE_EX + Style.DIM, valueColors: dict = None):
        template = re.sub(r'(\{.*?\})', Fore.RESET + Style.RESET_ALL + valueColor + '\\1' + textColor, template, re.LOCALE)
        if valueColors:
            for valueName in valueColors:
                template = re.sub(r'(\{%s.*?\})' % valueName, Fore.RESET + Style.RESET_ALL + valueColors[valueName] + '\\1' + textColor, template, re.LOCALE)
        self.append((textColor + template + Fore.RESET + Style.RESET_ALL).format(**data))

    def appendSeparator(self, color: str = Fore.BLUE):
        self.append(color + self.separator)

    def flush(self):
        index = 1
        for line in self.lines:
            text, forward = line
            stdout.write( "%s%s" % ('\u001b[%d;%df' % (index,1), text))
            index += forward
        stdout.write('\n')
        stdout.flush() 
        