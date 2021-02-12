import json
import sys
import random
import os

__DIR__ = (os.path.dirname(__file__) or '.')


USER_AGENT_FILE = __DIR__ + '../../data/user-agents.txt'
PROXY_FILE = __DIR__ + '../../data/proxies.txt'

# create a class that loads a json
class AccountManager:
    def __init__(self, config_file):
        self.config_file = config_file
        self.userAgents = []

    # create a function that opens the file, deletes an account, and closes it
    def delete_account(self, email, account_key='accounts', email_key='email'):
        with open(self.config_file, 'r') as infile:
            data = json.loads(infile.read())

        accounts = data[account_key]

        accounts = list(filter(lambda i: i[email_key] != email, accounts))
        data[account_key] = accounts

        with open(self.config_file, 'w') as outfile:
            outfile.write(json.dumps(data, indent=4))

    def getRandomUserAgent(self):
        if len(self.userAgents):
            return self.userAgents[random.randint(0, len(self.userAgents)-1)]
    # Build an accounts array and return it
    def get_accounts(self):
        with open(self.config_file, 'r') as infile:
            data = json.loads(infile.read())

        try:
            user_agent_file_path = data['user_agent_file_path']
            AccountbuilderConfig = data['account_builder']
            proxies_file_path = AccountbuilderConfig['proxies_file_path']
            users_file_path = AccountbuilderConfig['users_file_path']
            path = __DIR__ + '/../config/'

            if user_agent_file_path:
                with open(path + user_agent_file_path, 'r') as userAgentsFile:
                    line = 1
                    for userAgent in userAgentsFile:
                        ua = userAgent.strip()
                        if ua :
                            self.userAgents.append(ua)
                            line += 1    
                        else:
                            print('Malformed user agent data at line #%d : Emty string' % line)    
                    print('Found %d user agent' % len(self.userAgents))



            proxies = []
            accounts = []
            if users_file_path:
                if proxies_file_path:
                    with open(path + proxies_file_path, 'r') as proxiesFile:
                        line = 1
                        for proxy in proxiesFile:
                            p = proxy.strip().split(':')
                            if len(p) == 4 :
                                proxies.append({
                                    "host": p[0],
                                    "port": p[1],
                                    "username": p[2],
                                    "password": p[3]
                                })
                                line += 1    
                            else:
                                print('Malformed proxy data at line #%d : %s' % (line, proxy.replace('\n', '')))    
                        print('Found %d proxies' % len(proxies))

                usersFile = open(path + users_file_path, 'r')
                line = 1
                
                for user in usersFile:
                    u = user.strip().split(':')
                    if len(u) == 2:
                        account = {
                            "email": u[0],
                            "password": u[1]
                        }
                        if len(proxies):
                            account['proxi'] = proxies[random.randint(0, len(proxies)-1)]
                        accounts.append(account)
                    else:
                        print('Malformed user data at line #%d : %s' % (line, user.replace('\n', '')))
                    line += 1

            print('Found %d users' % len(accounts))
            return accounts


        except KeyError:
            print('Warning: No config data found to build accounts')
        except:
            print("Error during account building:", sys.exc_info()[0])



# run a test
if __name__ == '__main__':

    am = AccountManager( __DIR__ +  '/../config/config.json')

    accounts = am.get_accounts()
    
    for account in accounts:
        print(account)


