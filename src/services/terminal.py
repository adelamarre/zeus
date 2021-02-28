from sys import stdout
from os import get_terminal_size
from colorama import Fore, Style
import re 
import urllib3
urllib3.disable_warnings()

class Terminal:

    def __init__(self, charSeparator: str) -> None:
        self.lines = []
        self.charSeparator = charSeparator
        self.width, self.height = get_terminal_size()
        self.separator = charSeparator * self.width

    def newPage(self):
        self.lines = []  
        self.width, self.height = get_terminal_size()
        self.separator = self.charSeparator * self.width

    def append(self, text: str = ''):
        self.lines.append(text)
    
    def appendTemplate(self, template: str, data, valueColor: str =  Fore.CYAN, textColor: str = Fore.LIGHTWHITE_EX + Style.DIM, valueColors: dict = None):
        template = re.sub(r'(\{.*?\})', Fore.RESET + Style.RESET_ALL + valueColor + '\\1' + textColor, template, re.LOCALE)
        if valueColors:
            for valueName in valueColors:
                template = re.sub(r'(\{%s.*?\})' % valueName, Fore.RESET + Style.RESET_ALL + valueColors[valueName] + '\\1' + textColor, template, re.LOCALE)
        
            
        self.append((textColor + template + Fore.RESET + Style.RESET_ALL).format(**data))

    def appendSeparator(self, color: str = Fore.BLUE):
        self.append(color + self.separator)

    def flush(self):
        stdout.write('\u001b[2J')
        index = 1
        for line in self.lines:
            stdout.write( "%s%s" % ('\u001b[%d;%df' % (index,1), line))
            index += 1
        stdout.write('\n')
        stdout.flush() 
        