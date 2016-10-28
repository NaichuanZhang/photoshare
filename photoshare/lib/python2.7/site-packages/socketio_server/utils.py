from socketIO_client import SocketIO

def import_class(name):
    module, classname = name.rsplit(".", 1)
    mod = __import__(module, fromlist=[classname])
    return getattr(mod, classname)

def send_socketio(namespace, event, *args):
    with SocketIO(socketio_settings.HOST, socketio_settings.PORT) as io:
        io.emit(event, path=namespace, *args)
