
import sqlite3
import os
import sys



class DatabaseManager:
    def __init__(self, datafilePath, databaseName):
        print('Open database %s' % datafilePath)
        self.connection = None
        try:
            self.connection = sqlite3.connect(datafilePath)
            c = self.connection.cursor()
            accounts = c.execute('select count(*) from account')
            print(accounts)
        except sqlite3.OperationalError:
            c.close()
            self.createTables()
        except:
            print(sys.exc_info())
    
    def __del__(self): 
        if self.connection:
            self.connection.close()

    def createTables(self):
        c = self.connection.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS user (
            email varchar(255) PRIMARY KEY,
            user_agent varchar(512),
            proxi_ip varchar(15),
            proxi_host varchar(50),
            proxi_user varchar(50),
            proxi_pwd varchar(50),
            
        );
        """)
if __name__ == '__main__':
    dm = DatabaseManager((os.path.dirname(__file__) or '.') + '/../../data/test.db', 'interstellar')
