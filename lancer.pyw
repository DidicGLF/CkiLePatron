import os
import sys
import threading
import time
import webbrowser
import tkinter as tk
from tkinter import font as tkfont

# S'assurer que le répertoire courant est celui du script
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PORT = 5000
URL  = f"http://127.0.0.1:{PORT}"

# ── Démarrer Flask ──────────────────────────────────────────────────────────
from app import app as flask_app

def start_server():
    flask_app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)

server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

# ── Ouvrir le navigateur après démarrage ───────────────────────────────────
def open_browser():
    time.sleep(1.5)
    webbrowser.open(URL)

threading.Thread(target=open_browser, daemon=True).start()

# ── Fenêtre de contrôle ────────────────────────────────────────────────────
root = tk.Tk()
root.title("CkiLePatron")
root.geometry("320x120")
root.resizable(False, False)


pad = dict(padx=20, pady=0)

tk.Label(root, text="CkiLePatron est en cours d'exécution.",
         font=("Segoe UI", 10, "bold")).pack(pady=(18, 2))

url_label = tk.Label(root, text=URL, font=("Segoe UI", 9), fg="#888",
                     cursor="hand2")
url_label.pack()
url_label.bind("<Button-1>", lambda e: webbrowser.open(URL))

btn = tk.Button(root, text="Ouvrir dans le navigateur",
                command=lambda: webbrowser.open(URL),
                font=("Segoe UI", 9), relief="flat",
                bg="#B85447", fg="white", padx=12, pady=4,
                cursor="hand2", activebackground="#9C3F36", activeforeground="white")
btn.pack(pady=12)

root.mainloop()
# La fermeture de la fenêtre arrête le serveur (daemon thread)
