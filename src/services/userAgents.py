import os
import random

USER_AGENT_FILE = '/user-agents.txt'

class UserAgentManager:
    def __init__(self, basePath):
        self.userAgents = []
        with open(basePath + USER_AGENT_FILE, 'r') as userAgentsFile:
            line = 1
            for userAgent in userAgentsFile:
                p = userAgent.strip()
                if p :
                    self.userAgents.append(p)
                    line += 1    
                else:
                    print('Malformed user agent data at line #%d : %s' % (line, userAgent.replace('\n', '')))    
            #print('Found %d user agents' % len(self.userAgents))

    def getRandomUserAgent(self):
        if len(self.userAgents):
            return random.choice(self.userAgents)
