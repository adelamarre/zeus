
import xvfbwrapper
import os
import subprocess
import time
#/usr/bin/x11vnc -display :0 -forever -shared -many -rfbauth /root/.vnc_passwd

class X11vnc:
    SLEEP_TIME_BEFORE_START = 0.1

    def __init__(self, xvfb: xvfbwrapper.Xvfb) -> None:
        self.xvfb = xvfb
        self.x11vnc_cmd = None
        self.proc = None
    def start(self):
        
        display_var = ':{}'.format(self.xvfb.new_display)
        self.x11vnc_cmd = ['x11vnc', '-display', display_var, '-forever', '-shared', '-many']
        with open(os.devnull, 'w') as fnull:
            self.proc = subprocess.Popen(self.x11vnc_cmd,
                                         stdout=fnull,
                                         stderr=fnull,
                                         close_fds=True)
        # give Xvfb time to start
        time.sleep(self.__class__.SLEEP_TIME_BEFORE_START)
        self.proc.poll()
        
    def stop(self):
        if self.proc:
            try:
                self.proc.terminate()
            except:
                pass
