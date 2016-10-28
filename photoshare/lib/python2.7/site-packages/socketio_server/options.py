from socketio.namespace import BaseNamespace, allowed_event_name_regex
from django.contrib.auth.models import User
import gevent


class SocketList:
    all = {}
    user = {}

sockets = SocketList()


def emit_to(key, event, data, endpoint=''):
    """ sends a generic message to the socket at User/session_key """

    socket = None

    if key is User:
        key = key.id
        if key in sockets.user:
            socket = sockets.user.get(key)
    elif key in sockets.all:
        socket = sockets.all.get(key)

    if socket:
        socket.send_packet(dict(
            type="event",
            name=event,
            args=data,
            endpoint=endpoint))
    else:
        print "not found"


def emit_to_all(event, data, endpoint=''):
    for socket in sockets.all.values():
        socket.send_packet(dict(
            type="event",
            name=event,
            args=data,
            endpoint=endpoint))


class UserNamespace(BaseNamespace):

    def on_identify(self):
        sockets.all[self.request.session.session_key] = self.socket
        if self.request.user.is_authenticated:
            sockets.user[self.request.user.id] = self.socket

        message = "Hello, %s" % str(self.request.user)

        self.emit("welcome", message)

    def recv_disconnect(self):
        try:
            del sockets[self.request.session.session_key]
        except:
            pass


class DispatchingNamespace(UserNamespace):
    namespaces = {
        '': {
        }
    }

    def process_event(self, packet):
        args = packet['args']
        name = packet['name']
        if not allowed_event_name_regex.match(name):
            self.error("unallowed_event_name",
                       "name must only contains alpha numerical characters")
            return

        method_name = 'on_' + name.replace(' ', '_')
        # This means the args, passed as a list, will be expanded to
        # the method arg and if you passed a dict, it will be a dict
        # as the first parameter.

        if method_name in self.namespaces[self.ns_name]:
            inst = self.namespaces[self.ns_name][method_name]()
            return getattr(inst, method_name)(self, *args)
        else:
            super(DispatchingNamespace, self).process_event(packet)

    @classmethod
    def register_class(self, klass):

        namespace = getattr(klass, "socketio_namespace", "")
        recievers = DispatchingNamespace.namespaces.get(namespace)
        for member in dir(klass):
            if member.startswith("on_"):
                attr = getattr(klass, member)
                if callable(attr):
                    recievers[member] = klass

        return klass
