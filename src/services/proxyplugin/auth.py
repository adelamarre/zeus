
from proxy.plugin import ManInTheMiddlePlugin, ProxyPoolPlugin
from proxy.common.utils import build_http_response
from proxy.http.codes import httpStatusCodes
from proxy.common.utils import new_socket_connection
from typing import Optional, Any
from proxy.http.parser import HttpParser
from requests.auth import _basic_auth_str
from src.services.proxies import ProxyManager
from proxy.common.constants import DEFAULT_BUFFER_SIZE, SLASH, COLON
from src.services.config import Config


class ProxyRedirect(ProxyPoolPlugin):
    def __init__(self):
        super.__init__(self)
    
    def before_upstream_connection(
            self, request: HttpParser) -> Optional[HttpParser]:
        """Avoid upstream connection of server in the request.
        Initialize, connection to upstream proxy.
        """
        if 'Zeus-proxy' in request.headers:
            [host, port, username, password] = request.header['Zeus-proxy'].split(':')
            del request.header['Zeus-proxy']
            request.add_header('Proxy-Authorization', _basic_auth_str(self.username, self.password))
            self.conn = new_socket_connection((host, int(port)))    
        else:
            raise Exception('Could not find Zeus-proxy header')

        # Implement your own logic here e.g. round-robin, least connection etc.
        return None