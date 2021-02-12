
from .spotify.constants import SCENARY as SpotifyScenary
from .system.constants import SCENARY as SystemScenary

APPLICATIONS = {
    'spotify': {
        'displayName': 'Spotify',
        'scenary': SpotifyScenary,
        'enable': True,
    },
    'system': {
        'displayName': 'System',
        'scenary': SystemScenary,
        'enable': True,
    },
}