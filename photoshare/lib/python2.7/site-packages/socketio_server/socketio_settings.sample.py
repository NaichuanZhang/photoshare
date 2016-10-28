
# import your namespaces here
# namespaces should inherit from: 
# from socketio.namespace import BaseNamespace
# See example in the options.py file

from django.conf import settings
from socketio_server.options import UserNamespace

PORT = getattr(settings, "SOCKETIO_PORT", 7000) # replace this port with yours
HOST = getattr(settings, "SOCKETIO_HOST", "127.0.0.1")

NAMESPACES = {
    "/socket.io": UserNamespace
}
