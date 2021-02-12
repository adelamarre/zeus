import os
import random
__DIR__ = (os.path.dirname(__file__) or '.')

PROXY_FILE_LISTENER = __DIR__ + '/../../data/listener_proxies.txt'
PROXY_FILE_REGISTER = __DIR__ + '/../../data/register_proxies.txt'



class ProxyManager:
    def __init__(self, proxyFile=PROXY_FILE_LISTENER):
        self.proxies = []
        with open(proxyFile, 'r') as proxiesFile:
            line = 1
            for proxy in proxiesFile:
                p = proxy.strip().split(':')
                if len(p) == 4 :
                    self.proxies.append({
                        "host": p[0],
                        "port": p[1],
                        "username": p[2],
                        "password": p[3]
                    })
                    line += 1    
                elif len(p) == 2:
                    self.proxies.append({
                        "host": p[0],
                        "port": p[1],
                    })
                else:   
                    print('Malformed proxy data at line #%d : %s' % (line, proxy.replace('\n', '')))    
            print('Found %d proxies' % len(self.proxies))

    def getRandomProxy(self):
        if len(self.proxies):
            return random.choice(self.proxies)

    def getProxies(self):
        return self.proxies