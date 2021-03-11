from tornado.web import RequestHandler
from src import VERSION
class BaseHandler(RequestHandler):
    db = None
    context = {}
    def __init__(self, application, request, **kwargs) -> None:
        super().__init__(application, request, **kwargs)
        self.db = BaseHandler.db
        self.context = BaseHandler.context

    def get_template_namespace(self):
        ns = super(BaseHandler, self).get_template_namespace()
        ns.update({
            'version': VERSION,
        })
        return ns