import sys; sys.path.insert(0, '.')  # @IgnorePep8
if 'threading' in sys.modules:
    raise Exception('threading module loaded before patching!')

import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')  # @IgnorePep8
from gevent import monkey; monkey.patch_all()  # @IgnorePep8
from django.conf import settings as django_settings
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.handlers.wsgi import WSGIRequest, WSGIHandler
from django.utils import autoreload
from socketio import socketio_manage
from socketio.handler import SocketIOHandler
from socketio.server import SocketIOServer
from socketio_server.options import DispatchingNamespace
from threading import Lock
from utils import import_class
import _socket

lock = Lock()


def unlink(path):
    from errno import ENOENT
    try:
        os.unlink(path)
    except OSError, ex:
        if ex.errno != ENOENT:
            raise


def link(src, dest):
    from errno import ENOENT
    try:
        os.link(src, dest)
    except OSError, ex:
        if ex.errno != ENOENT:
            raise


def bind_unix_listener(path, backlog=50):
    pid = os.getpid()
    tempname = os.path.abspath('%s.%s.tmp' % (path, pid))
    backname = os.path.abspath('%s.%s.bak' % (path, pid))
    unlink(tempname)
    unlink(backname)
    link(path, backname)
    try:
        sock = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
        sock.setblocking(0)
        sock.bind(tempname)

        os.chmod(tempname, 0777)
        sock.listen(backlog)
        os.rename(tempname, path)
        return sock
    finally:
        unlink(backname)


class ProxiedWSGIHandler(SocketIOHandler):

    def get_environ(self):
#         print
#         print "*" * 80
#         print self.headers
        self.client_address = (self.headers.get('X-Real-IP', '1.1.1.1'), '')
#         print "^" * 80
#         print
        return super(ProxiedWSGIHandler, self).get_environ()


def not_found(start_response):
    print "not found"
    start_response('404 Not Found', [])
    return ['<h1>Not Found</h1>']


def load_namespaces():
    namespace_module = getattr(django_settings, "NAMESPACE_MODULE", None)
    if namespace_module:
        try:
            namespaces = import_class(namespace_module).namespaces
            return namespaces
        except Exception, ex:
            print ex
            pass
    return {}


class Application(object):
    _my_namespaces = {
        '': DispatchingNamespace
    }

    def __init__(self):
        print
        print "Starting SOCKETIO Application"
        print "=" * 20
        print
        namespaces = load_namespaces()
        if namespaces:
            self._my_namespaces = namespaces

        self.django_wsgi = WSGIHandler()
        super(Application, self).__init__()
        self.middleware = [
            SessionMiddleware(),
            AuthenticationMiddleware()
        ]

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']

        if path.startswith('/socket.io/static/'):
            try:
                filename = os.path.join(django_settings.STATIC_ROOT,
                    path.replace("/socket.io/static/", ""))
                data = open(filename).read()
            except Exception, ex:
                print ex
                return not_found(start_response)

            if path.endswith(".js"):
                content_type = "text/javascript"
            elif path.endswith(".css"):
                content_type = "text/css"
            elif path.endswith(".swf"):
                content_type = "application/x-shockwave-flash"
            else:
                content_type = "text/html"

            start_response('200 OK', [('Content-Type', content_type)])
            return [data]

        if "socketio" not in environ:
            return self.django_wsgi(environ, start_response)
        else:
            request = WSGIRequest(environ)
            for middle in self.middleware:
                middle.process_request(request)
            socketio_manage(environ, self._my_namespaces, request=request)


def serve(settings):
    autoreload_setting = getattr(settings, "AUTORELOAD", django_settings.DEBUG)
    if autoreload_setting:
        autoreload.main(_serve, [settings])
    else:
        autoreload.main(_serve, [settings])


def _serve(settings):
    autoreload_setting = getattr(settings, "AUTORELOAD", django_settings.DEBUG)
    host = settings.HOST
    port = settings.PORT
    print
    print 'Listening on %s:%s' % (settings.HOST, settings.PORT)
    print "Autoreload:", autoreload_setting and "ON" or "OFF"
    print

    data = {}

    keyfile = getattr(settings, "KEYFILE", None)
    certfile = getattr(settings, "CERTFILE", None)
    if keyfile and certfile:
        data.update(dict(
            keyfile=keyfile,
            certfile=certfile
        ))

    app_module = getattr(settings, "APPLICATION", None)
    if not app_module:
        app = Application(settings.NAMESPACES)
    else:
        app = import_class(app_module)(settings.NAMESPACES)

    CrossOriginSocketIOServer((host, port), app,
        policy_server=False, **data).serve_forever()


if __name__ == "__main__":
    SocketIOServer(
        ('', 8000), Application(),
        policy_server=False,
    ).serve_forever()
