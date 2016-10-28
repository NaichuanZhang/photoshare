import subprocess
import os

def start(name):
    devnull = open(os.devnull)
    process = subprocess.Popen([
        #"screen", "-S", name, 
        "python", "socketio_server/server.py"],        
        stdout=devnull, stderr=devnull)
    