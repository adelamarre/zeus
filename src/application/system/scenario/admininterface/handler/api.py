
from json import loads

from requests.api import get
from src.application.spotify.scenario.config.monitor import MonitorConfig
from src.application.spotify.stats import ListenerRemoteStat
from tornado.template import Template
from src.application.db.table.statistic import StatisticTable
from src.application.system.scenario.admininterface.handler.basehandler import BaseHandler

class ApiContractsTable(BaseHandler):
    def get(self):
        template = Template("""{% module Table([
            'application',
            'client',
            'contract',
            'status',
            'sold',
            'played',
            'progress'
            ], contracts) %}"""
        ) 
        template.namespace = self.get_template_namespace()
        template.autoescape = False
        
        self.finish(template.generate(contracts=StatisticTable(self.db).getContractStats()))
        #contracts = StatisticTable(self.db).getContractStats()
        #self.render("api/contracts-table.html", contracts=contracts)

class ApiTracksTable(BaseHandler):
    def get(self):
        template = Template("""{% module Table([
            'application',
            'client',
            'contract',
            'artist',
            'track',
            'played',
            ], contracts) %}"""
        ) 
        template.namespace = self.get_template_namespace()
        template.autoescape = False
        
        self.finish(template.generate(contracts=StatisticTable(self.db).getTracksStats()))
        #contracts = StatisticTable(self.db).getTracksStats()
        #self.render("api/contracts-table.html", contracts=contracts)

class ApiServers(BaseHandler):
    def get(self):
        
        GLOBAL = 'global'
        SERVERS = 'servers'
        statistics = {
            GLOBAL: {
                ListenerRemoteStat.LOGGING_IN: 0,
                ListenerRemoteStat.PLAYING: 0,
                ListenerRemoteStat.PLAYED: 0,
                ListenerRemoteStat.ERROR: 0,
                ListenerRemoteStat.PREPARE: 0,
            },
            SERVERS: []
        }
            
        serversStats = statistics[SERVERS]
        globalStats = statistics[GLOBAL]
        configData = self.context['config']
        servers = configData[MonitorConfig.SERVERS].split(',')
        secret  = configData[MonitorConfig.SECRET]

        for server in servers:
            try:
                host = server.strip()
                serverStat = loads(get('https://%s:63443/?k=%s' % (host, secret), verify=False).text)
                serverStat['host'] = host

                if serverStat['runner'][ListenerRemoteStat.PLAYED]:
                    serverStat['runner']['percentError'] = '%.2f' % ((serverStat['runner'][ListenerRemoteStat.ERROR] / serverStat['runner'][ListenerRemoteStat.PLAYED]) * 100)
                else:
                    serverStat['runner']['percentError'] = 'n/a'

                
                for key in globalStats:
                    globalStats[key] += serverStat['runner'][key]
                serversStats.append(serverStat)

            except Exception as e:
                statistics['servers'].append({
                    'host': host,
                    'exception': e
                })

        if globalStats[ListenerRemoteStat.PLAYED]:
            globalStats['percentError'] = '%.2f' % ((globalStats[ListenerRemoteStat.ERROR] / globalStats[ListenerRemoteStat.PLAYED]) * 100)
        else:
            globalStats['percentError'] = 'n/a'
        self.render("api/servers.html", statistics=statistics)
