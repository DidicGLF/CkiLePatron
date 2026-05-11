"""
Point d'entrée PyInstaller — lance Flask, ouvre le navigateur, fenêtre tkinter.
"""
import os
import sys
import shutil
import threading
import time
import webbrowser
import tkinter as tk
from tkinter import messagebox

from app import app as flask_app, BASE_DIR, PATRONS_DIR

PORT = 5000
URL  = f"http://127.0.0.1:{PORT}"

os.makedirs(PATRONS_DIR, exist_ok=True)

# ── Serveur ────────────────────────────────────────────────────────────────
threading.Thread(
    target=lambda: flask_app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False),
    daemon=True
).start()

threading.Thread(
    target=lambda: (time.sleep(1.5), webbrowser.open(URL)),
    daemon=True
).start()

# ── Extension : chemin source (dans le bundle) et destination (à côté de l'exe) ──
if getattr(sys, 'frozen', False):
    EXT_SRC = os.path.join(sys._MEIPASS, 'extension')
else:
    EXT_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extension')
EXT_DST = os.path.join(BASE_DIR, 'extension')

def installer_extension():
    # Copier l'extension à côté de l'exe si pas encore fait
    if not os.path.isdir(EXT_DST):
        shutil.copytree(EXT_SRC, EXT_DST)

    # Détecter le navigateur et ouvrir la page extensions
    import subprocess
    chrome = (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    )
    for path in chrome:
        if os.path.exists(path):
            subprocess.Popen([path, "chrome://extensions"])
            break
    else:
        webbrowser.open("edge://extensions")

    messagebox.showinfo(
        "Installer l'extension",
        "1. Activez le « Mode développeur » (en haut à droite)\n"
        "2. Cliquez « Charger l'extension non empaquetée »\n"
        f"3. Sélectionnez le dossier :\n{EXT_DST}"
    )

# ── Fenêtre tkinter ────────────────────────────────────────────────────────
root = tk.Tk()
root.title("CkiLePatron")
root.geometry("320x160")
root.resizable(False, False)

tk.Label(root, text="CkiLePatron est en cours d'exécution.",
         font=("Segoe UI", 10, "bold")).pack(pady=(16, 2))
tk.Label(root, text=URL, font=("Segoe UI", 9), fg="#888").pack()

tk.Button(root, text="Ouvrir dans le navigateur",
          command=lambda: webbrowser.open(URL),
          font=("Segoe UI", 9), relief="flat",
          bg="#B85447", fg="white", padx=12, pady=4,
          activebackground="#9C3F36", activeforeground="white").pack(pady=(14, 4))

tk.Button(root, text="Installer l'extension navigateur",
          command=installer_extension,
          font=("Segoe UI", 9), relief="flat",
          bg="#e8e0d8", fg="#333", padx=12, pady=4).pack()

root.mainloop()
