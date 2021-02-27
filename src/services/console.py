from multiprocessing import Lock
# class Style:
#     Black = '\u001b[30m'
#     Red = '\u001b[31m'
#     Green = '\u001b[32m'
#     Yellow = '\u001b[33m'
#     Blue = '\u001b[34m'
#     Magenta = '\u001b[35m'
#     Cyan = '\u001b[36m'
#     White = '\u001b[37m'
#     BrightBlack = '\u001b[30;1m'
#     BrightRed = '\u001b[31;1m'
#     BrightGreen = '\u001b[32;1m'
#     BrightYellow = '\u001b[33;1m'
#     BrightBlue = '\u001b[34;1m'
#     BrightMagenta = '\u001b[35;1m'
#     BrightCyan = '\u001b[36;1m'
#     BrightWhite = '\u001b[37;1m'
#     BBlack = '\u001b[40m' 
#     Reset = '\u001b[0m'
#     Bold = '\u001b[1m'
#     Underline = '\u001b[4m'
#     Reversed = '\u001b[7m'
    
#     SetCursor   =  '\u001b[%d;%dH'     # position cursor at x across, y down
#     MoveTo      =  '\u001b[%d;%df'     # position cursor at x across, y down
#     Up          =  '\u001b[nA'       # move cursor n lines up
#     Down        =  '\u001b[nB'       # move cursor n lines down
#     Forward     =  '\u001b[nC'       # move cursor n characters forward
#     Backward    =  '\u001b[nD'       # move cursor n characters backward

#     ClearScreen =  '\u001b[1j'
#     ClearLine   =  '\u001b[1j' 
from colorama import Style, Fore, Back
import traceback
from datetime import datetime
import os

class Console:
    STYLES = {
        'ERROR': Fore.RED,
        'WARNING': Fore.RED,
        'SUCCESS': Fore.GREEN,
        'NOTICE': Fore.YELLOW,
        'LOG': Fore.WHITE
    }
    def __init__(self, verbose=2, logToFile=True, ouput=True, logfile=None):
        self.lock = Lock()
        self.verbose = verbose
        self.logToFile = logToFile
        self.output = ouput
        if logfile:
            self.logfile= logfile
        elif logfile is None:
            self.logfile= (os.path.dirname(__file__) or '.') + '/../../temp/' + datetime.now().strftime("%m-%d-%Y-%H-%M-%S")+ '.log'

        try:
            import termios
        except ImportError:
            # Non-POSIX. Return msvcrt's (Windows') getch.
            import msvcrt
            self.getch = msvcrt.getch
        else:
        # POSIX system. Create and return a getch that manipulates the tty.
            import sys, tty
            def _getch():
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    ch = sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                return ch

            self.getch = _getch

    def _print(self, type, message, bold=False, bright=False):

        prefix = self.getPrefix(type)
        if self.lock:
            self.lock.acquire()
        
        if self.logToFile and self.logfile:
            try:
                with open(self.logfile, 'a') as f:
                    f.write('%s%s\n' % (prefix, message))
            except:
                print(traceback.format_exc())
        if self.output:
            color = Console.STYLES.get(type, Fore.WHITE)
            msg = "%s%s%s%s%s" % (
                Fore.WHITE + prefix,
                ("", Style.DIM)[bold],
                (color, Style.BRIGHT + color)[bright],
                message,
                Style.RESET_ALL
            )
            print(msg)
        
        if self.lock:
            self.lock.release()

    def getPrefix(self, type):
        return '[%s][%s]: ' % (datetime.now().strftime("%m-%d-%Y-%H-%M-%S"), type)

    def error(self, message, bright=False, bold=False):
        if self.verbose > 0:
            self._print('ERROR', message, bright, bold)
            
    def warning(self, message, bright=False, bold=False):
        if self.verbose > 0:
            self._print('WARNING', message, bright, bold)

    def success(self, message, bright=False, bold=False):
        if self.verbose > 1:
            self._print('SUCCESS', message, bright, bold)

    def notice(self, message, bright=False, bold=False):
        if self.verbose > 0:
            self._print('NOTICE', message, bright, bold)

    def log(self, message, bright=False, bold=False):
        if self.verbose > 1:
            self._print('LOG', message, bright, bold)
    def exception(self, reason=None):
        if self.verbose > 0:
            if reason:
                self._print('EXCEPTION', '%s\n%s' % (reason, traceback.format_exc()), True, False)
            else:
                self._print('EXCEPTION', traceback.format_exc(), True, False)

    def clearScreen(self):
        print('\u001b[2J', flush=False)
        
    def printAt(self, x,y, message=''):
        print( "%s%s" % ('\u001b[%d;%df' % (y,x), message), end='', flush=False)
