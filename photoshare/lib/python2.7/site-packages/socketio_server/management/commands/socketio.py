from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'runs the socketio server'

    def handle(self, *args, **options):
        from socketio_server.server import serve
        try:
            import socketio_settings
            serve(socketio_settings)
        except ImportError, ex:
            print
            print "=" * 80
            print "You need to create a socketio_settings.py file"
            print "You can find a sample file at:"
            print "  socketio_server/socketio_settings.sample.py"
            print
            print "ERROR:", ex
            print "=" * 80
            print
