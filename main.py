"""
Point d'entrée PyInstaller — lance Flask, ouvre le navigateur, reste actif.
"""
import os
import sys
import shutil
import threading
import time
import webbrowser

from app import app as flask_app, BASE_DIR, PATRONS_DIR

PORT = 5000
URL  = f"http://127.0.0.1:{PORT}"

os.makedirs(PATRONS_DIR, exist_ok=True)

# Extraire l'extension à côté de l'exe (si pas déjà fait)
if getattr(sys, 'frozen', False):
    ext_src = os.path.join(sys._MEIPASS, 'extension')
else:
    ext_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extension')

ext_dst = os.path.join(BASE_DIR, 'extension')
if not os.path.isdir(ext_dst):
    shutil.copytree(ext_src, ext_dst)

# Démarrer le serveur
server = threading.Thread(
    target=lambda: flask_app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False),
    daemon=True
)
server.start()

# Ouvrir le navigateur
time.sleep(1.2)
webbrowser.open(URL)

# Garder le processus vivant tant que le serveur tourne
server.join()
