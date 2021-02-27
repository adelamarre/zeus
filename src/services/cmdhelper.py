
from colorama import Fore
def showHeader(version, color = Fore.BLUE):
    print ('''\u001b[2J\u001b[1;1f%s
 __     __                           ____        _   
 \ \   / /__ _ __   ___  _ __ ___   | __ )  ___ | |_ 
  \ \ / / _ \ '_ \ / _ \| '_ ` _ \  |  _ \ / _ \| __|
   \ V /  __/ | | | (_) | | | | | | | |_) | (_) | |_ 
    \_/ \___|_| |_|\___/|_| |_| |_| |____/ \___/ \__|
                                       %sversion: %s%s
''' % (color, Fore.WHITE, version, Fore.RESET))