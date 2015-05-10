# -*- coding: utf-8 -*-
import uwsgi
from datetime import datetime, timedelta 
import gevent.select
from ws4redis.exceptions import WebSocketError
from ws4redis.wsgi_server import WebsocketWSGIServer


class uWSGIWebsocket(object):
    def __init__(self, user):
        self._closed = False
        self._user = user
        self._last_seen = None

    def get_file_descriptor(self):
        """Return the file descriptor for the given websocket"""
        try:
            return uwsgi.connection_fd()
        except IOError, e:
            self.close()
            raise WebSocketError(e)

    @property
    def closed(self):
        return self._closed

    def receive(self):
        if self._closed:
            raise WebSocketError("Connection is already closed")
        try:
            return uwsgi.websocket_recv_nb()
        except IOError, e:
            self.close()
            raise WebSocketError(e)

    def flush(self):
        try:
            uwsgi.websocket_recv_nb()
        except IOError:
            self.close()

    def send(self, message, binary=None):
        try:
            uwsgi.websocket_send(message)
        except IOError, e:
            self.close()
            raise WebSocketError(e)

    def close(self, code=1000, message=''):
        self._closed = True
        try:
            # If a handler has been defined in the settings, call it
            # to notify disconnection of user
            settings.DISCONNECTION_HANDLER(self.user)
        except:
            pass

    def reset_last_seen(self):
        self._last_seen = datetime.now()

    def is_active(self):
        return datetime.now() - self._last_seen <= timedelta(seconds=25)


class uWSGIWebsocketServer(WebsocketWSGIServer):
    def upgrade_websocket(self, environ, start_response, user):
        uwsgi.websocket_handshake(environ['HTTP_SEC_WEBSOCKET_KEY'], environ.get('HTTP_ORIGIN', ''))
        return uWSGIWebsocket(user)

    def select(self, rlist, wlist, xlist, timeout=None):
        return gevent.select.select(rlist, wlist, xlist, timeout)
