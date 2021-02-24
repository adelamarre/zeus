import os
import random
__DIR__ = (os.path.dirname(__file__) or '.')

PROXY_FILE_LISTENER = __DIR__ + '/../../data/listener_proxies.txt'
PROXY_FILE_REGISTER = __DIR__ + '/../../data/register_proxies.txt'

class Proxy():
    def getUrl(proxy, scheme = None) -> str:
        _scheme = 'http'
        if scheme:
            _scheme = scheme
        elif 'scheme' in proxy:
            _scheme = proxy['scheme']
            
        if 'username' in proxy:
            return f'{_scheme}://{proxy["username"]}:{proxy["password"]}@{proxy["host"]}:{proxy["port"]}'
        else:
            return f'{_scheme}://{proxy["host"]}:{proxy["port"]}'

    def loads(csv):
        p = csv.strip().split(':')
        if len(p) == 4 :
            return {
                'host': p[0],
                'port': int(p[1]),
                'username': p[2],
                'password': p[3],
                'scheme': 'http'
            }
        elif len(p) == 5 :
            return {
                'host': p[0],
                'port': int(p[1]),
                'username': p[2],
                'password': p[3],
                'scheme': p[4]
            }    
        elif len(p) == 2:
            return {
                'host': p[0],
                'port': int(p[1]),
                'scheme': 'http'
            }   
        elif len(p) == 3:
            return {
                'host': p[0],
                'port': int(p[1]),
                'scheme': p[2]
            } 
        else:
            print('Malformed proxy data : %s' % csv.strip())

class ProxyManager:
    def __init__(self, proxyFile=PROXY_FILE_LISTENER):
        self.proxies = []
        with open(proxyFile, 'r') as proxiesFile:
            for csv in proxiesFile:
                p = Proxy.loads(csv)
                if p:
                    self.proxies.append(p)

    def getRandomProxy(self):
        if len(self.proxies):
            return random.choice(self.proxies)

    def getProxies(self):
        return self.proxies