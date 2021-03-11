
from src.application.system.scenario.admininterface.handler.basehandler import BaseHandler

class MainHandler(BaseHandler):
    def get(self):
        self.redirect('/dashboard')
        #self.render(template_name='home.html')
        
class DashboardHandler(BaseHandler):
    def get(self):
        self.render(template_name='dashboard.html')
