"""
Point d'entrée PyInstaller — remplace lancer.pyw pour le build .exe.
Démarre Flask en arrière-plan, ouvre le navigateur, affiche une fenêtre tkinter.
"""
import os
import sys
import threading
import time
import webbrowser
import tkinter as tk

from app import app as flask_app, BASE_DIR, PATRONS_DIR

PORT = 5000
URL  = f"http://127.0.0.1:{PORT}"

# Créer le dossier patrons s'il n'existe pas
os.makedirs(PATRONS_DIR, exist_ok=True)

def start_server():
    flask_app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)

threading.Thread(target=start_server, daemon=True).start()

def open_browser():
    time.sleep(1.5)
    webbrowser.open(URL)

threading.Thread(target=open_browser, daemon=True).start()

# ── Fenêtre de contrôle ────────────────────────────────────────────────────
root = tk.Tk()
root.title("CkiLePatron")
root.geometry("320x120")
root.resizable(False, False)

tk.Label(root, text="CkiLePatron est en cours d'exécution.",
         font=("Segoe UI", 10, "bold")).pack(pady=(18, 2))
tk.Label(root, text=URL, font=("Segoe UI", 9), fg="#888",
         cursor="hand2").pack()

tk.Button(root, text="Ouvrir dans le navigateur",
          command=lambda: webbrowser.open(URL),
          font=("Segoe UI", 9), relief="flat",
          bg="#B85447", fg="white", padx=12, pady=4,
          cursor="hand2", activebackground="#9C3F36",
          activeforeground="white").pack(pady=12)

root.mainloop()
