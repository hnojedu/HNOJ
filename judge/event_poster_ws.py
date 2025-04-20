import json
import logging
import socket
import threading

from django.conf import settings
from websocket import WebSocketException, create_connection, setdefaulttimeout

__all__ = ['EventPostingError', 'EventPoster', 'post', 'last']
_local = threading.local()

logger = logging.getLogger('judge.event_poster')

# Set the default timeout to 5 seconds
# Without this, create_connection will block the whole process indefinitely
setdefaulttimeout(5)


class EventPostingError(RuntimeError):
    pass


class EventPoster(object):
    def __init__(self):
        self._connect()

    def _connect(self):
        self._conn = create_connection(settings.EVENT_DAEMON_POST)
        if settings.EVENT_DAEMON_KEY is not None:
            self._conn.send(json.dumps({'command': 'auth', 'key': settings.EVENT_DAEMON_KEY}))
            resp = json.loads(self._conn.recv())
            if resp['status'] == 'error':
                raise EventPostingError(resp['code'])

    def post(self, channel, message, tries=0):
        try:
            self._conn.send(json.dumps({'command': 'post', 'channel': channel, 'message': message}))
            resp = json.loads(self._conn.recv())
            if resp['status'] == 'error':
                raise EventPostingError(resp['code'])
            else:
                return resp['id']
        except WebSocketException:
            if tries > 10:
                raise
            self._connect()
            return self.post(channel, message, tries + 1)

    def last(self, tries=0):
        try:
            self._conn.send('{"command": "last-msg"}')
            resp = json.loads(self._conn.recv())
            if resp['status'] == 'error':
                raise EventPostingError(resp['code'])
            else:
                return resp['id']
        except WebSocketException:
            if tries > 10:
                raise
            self._connect()
            return self.last(tries + 1)


def _get_poster():
    if 'poster' not in _local.__dict__:
        _local.poster = EventPoster()
    return _local.poster


def post(channel, message):
    try:
        return _get_poster().post(channel, message)
    except (WebSocketException, socket.error) as e:
        logger.error(e, exc_info=True)
        try:
            del _local.poster
        except AttributeError:
            pass
    return 0


def last():
    try:
        return _get_poster().last()
    except (WebSocketException, socket.error) as e:
        logger.error(e, exc_info=True)
        try:
            del _local.poster
        except AttributeError:
            pass
    return 0
