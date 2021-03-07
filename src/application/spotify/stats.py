from multiprocessing import Array
from src import VERSION

class ListenerStat:
    LOGGING_IN = 0
    PLAYING = 1
    PLAYED = 2
    ERROR = 3
    DRIVER_NONE = 4
    PREPARE = 5

class ListenerRemoteStat:
    VERSION = 'version'
    LOGGING_IN = 'loggingIn'
    PLAYING = 'playing'
    PLAYED = 'played'
    ERROR = 'error'
    DRIVER_NONE = 'driverNone'
    PREPARE = 'prepare'

    def parse(stats: Array) -> dict:
        return {
            ListenerRemoteStat.VERSION: VERSION,
            ListenerRemoteStat.ERROR: stats[ListenerStat.ERROR],
            ListenerRemoteStat.DRIVER_NONE: stats[ListenerStat.DRIVER_NONE],
            ListenerRemoteStat.PLAYED: stats[ListenerStat.PLAYED],
            ListenerRemoteStat.LOGGING_IN: stats[ListenerStat.LOGGING_IN],
            ListenerRemoteStat.PLAYING: stats[ListenerStat.PLAYING],
            ListenerRemoteStat.PREPARE: stats[ListenerStat.PREPARE],
        }

class RegisterStat:
    FILLING_OUT = 0
    SUBMITTING = 1
    CREATED = 2
    ERROR = 3
    DRIVER_NONE = 4
    PREPARE = 5

class RegisterRemoteStat:
    VERSION = 'version'
    ERROR = 'error'
    DRIVER_NONE = 'driverNone'
    CREATED = 'created'
    FILLING_OUT = 'fillingOut'
    SUBMITTING = 'submitting'
    PREPARE = 'prepare'

    def parse(stats: Array) -> dict:
        return {
            RegisterRemoteStat.VERSION: VERSION,
            RegisterRemoteStat.ERROR: stats[RegisterStat.ERROR],
            RegisterRemoteStat.DRIVER_NONE: stats[RegisterStat.DRIVER_NONE],
            RegisterRemoteStat.CREATED: stats[RegisterStat.CREATED],
            RegisterRemoteStat.FILLING_OUT: stats[RegisterStat.FILLING_OUT],
            RegisterRemoteStat.SUBMITTING: stats[RegisterStat.SUBMITTING],
            RegisterRemoteStat.PREPARE: stats[RegisterStat.PREPARE],
        }
