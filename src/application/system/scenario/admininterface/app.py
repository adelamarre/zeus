from src.application.system.scenario.admininterface.handler.page import DashboardHandler
from src.services.console import Console
import tornado.ioloop
import tornado.web
from src.application.system.scenario.admininterface import helpers
from src import VERSION
from src.services.db import Db

from src.application.system.scenario.admininterface.handler.basehandler import BaseHandler
from src.application.system.scenario.admininterface.handler.page import MainHandler
from src.application.system.scenario.admininterface.handler.api import ApiContractsTable, ApiServers, ApiTracksTable


def makeAdminApp(userDir: str,console: Console, config: dict):
    BaseHandler.db = Db(userDir=userDir, console=console)
    BaseHandler.context = {
        'userDir': userDir,
        'console': console,
        'config': config,
    }

    settings = {
        #"autoescape": None,
        "compiled_template_cache":False,
        "autoreload": False,
        "ui_modules": helpers,
        "template_path": 'src/application/system/scenario/admininterface/templates',
        "static_path": 'src/application/system/scenario/admininterface/static'
    }
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/dashboard", DashboardHandler),
        (r"/api/contracts-table", ApiContractsTable),
        (r"/api/tracks-table", ApiTracksTable),
        (r"/api/servers", ApiServers)

        #(r"favicon\.png", tornado.web.StaticFileHandler),
        #dict(path=settings['static_path'])
    ], **settings)


    