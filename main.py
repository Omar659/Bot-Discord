import tkinter as tk
from tkinter import scrolledtext
import discord
from lo_zozzone import main as main_zozzone
from la_zozzona import main as main_zozzona
from utils import hide_subprocess_windows, kill_child_processes
import json
import queue
import sys
import os
from threading import Thread

# i bot usano percorsi relativi alla cartella del progetto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)


# Funzione per avviare il bot in un thread dedicato
def start_bot(main_func, config):
    try:
        main_func(config)
    except Exception as e:
        print("Bot terminato con errore:", e)


# quante righe tenere nella console: un ScrolledText che cresce all'infinito
# rallenta Tkinter fino a bloccare la finestra dopo qualche ora di log
MAX_CONSOLE_LINES = 2000
# quanti messaggi scrivere per ogni giro: se ne arriva una valanga (un
# traceback ripetuto) svuotare tutta la coda in un colpo congela la GUI
MAX_MESSAGES_PER_TICK = 200

closing = False


# Funzione per fermare tutti i bot
def stop_all_bots(root=None):
    global closing
    if closing:
        return
    closing = True
    print("Stopping all bots...")
    # da qui in poi l'output non deve più toccare la finestra
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    # ffmpeg e yt-dlp sono processi separati: sopravviverebbero alla chiusura
    kill_child_processes()
    if root is not None:
        try:
            root.quit()
            root.destroy()
        except Exception:
            pass
    # i bot girano in thread con il loro event loop: l'unico modo affidabile
    # di chiudere tutto subito è terminare il processo
    os._exit(0)


# Cattura tutto l'output (print, errori) e lo mette in coda per la GUI.
# Tkinter non è thread-safe: i widget vanno aggiornati solo dal thread
# principale, che legge la coda con after().
class ConsoleRedirector:
    def __init__(self, output_queue, original_stream=None):
        self.output_queue = output_queue
        self.original_stream = original_stream

    def write(self, message):
        try:
            # mai bloccante: se la GUI non sta dietro si perde qualche riga,
            # ma il thread del bot non si ferma ad aspettarla
            self.output_queue.put_nowait(message)
        except queue.Full:
            pass
        if self.original_stream is not None:
            try:
                self.original_stream.write(message)
            except Exception:
                pass

    def flush(self):
        if self.original_stream is not None:
            try:
                self.original_stream.flush()
            except Exception:
                pass


# GUI per il controllo del bot
def launch_gui(output_queue):
    root = tk.Tk()
    root.title("Bot Controller")

    # Imposta l'icona della finestra
    try:
        root.iconbitmap(os.path.join(BASE_DIR, "icon.ico"))
    except Exception as e:
        print("Impossibile caricare l'icona:", e)

    # Imposta la finestra per occupare l'80% dello schermo
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = int(screen_width * 0.8)
    window_height = int(screen_height * 0.8)
    root.geometry(f"{window_width}x{window_height}")

    # Aggiungi padding per la GUI
    padding = 20

    # Titolo
    title_label = tk.Label(root, text="I ZOZZONI", font=("Arial", 16, "bold"))
    title_label.pack(pady=padding)

    # Pulsante per fermare i bot
    stop_button = tk.Button(root,
                            text="STOP",
                            command=lambda: stop_all_bots(root),
                            bg="red",
                            fg="white",
                            font=("Arial", 12))
    stop_button.pack(pady=padding)

    # Frame che contiene l'area di output (console)
    output_frame = tk.Frame(root)
    output_frame.pack(fill=tk.BOTH, expand=True, padx=padding, pady=padding)

    # Aggiungi un box scorribile per visualizzare l'output
    output_box = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD)
    output_box.pack(fill=tk.BOTH, expand=True)

    # Svuota periodicamente la coda dei messaggi nella Text box
    def drain_queue():
        if closing:
            return
        try:
            pieces = []
            for _ in range(MAX_MESSAGES_PER_TICK):
                try:
                    pieces.append(output_queue.get_nowait())
                except queue.Empty:
                    break
            if pieces:
                # un solo insert invece di uno per messaggio
                output_box.insert(tk.END, "".join(pieces))
                # la console non deve crescere all'infinito
                righe = int(output_box.index("end-1c").split(".")[0])
                if righe > MAX_CONSOLE_LINES:
                    output_box.delete("1.0",
                                      "%d.0" % (righe - MAX_CONSOLE_LINES))
                output_box.yview(tk.END)
        except Exception:
            # un errore qui finirebbe su stderr, cioè di nuovo in questa
            # coda: si creerebbe un ciclo che blocca la finestra
            pass
        if not closing:
            root.after(100, drain_queue)

    root.after(100, drain_queue)

    # Avvia la GUI e chiude i bot alla chiusura della finestra
    root.protocol("WM_DELETE_WINDOW", lambda: stop_all_bots(root))

    # Avvia la GUI
    root.mainloop()


def start_bots():
    with open(os.path.join(BASE_DIR, "config.json"), "r") as json_file:
        config = json.load(json_file)

    # Verifica se la configurazione contiene entrambi i bot
    if "lo_zozzone" not in config or "la_zozzona" not in config:
        print(
            "Errore nella configurazione del file. Verifica che entrambi i bot siano configurati."
        )
        return []

    threads = []
    for main_func, token in ((main_zozzone, config["lo_zozzone"]),
                             (main_zozzona, config["la_zozzona"])):
        thread = Thread(target=start_bot, args=(main_func, token), daemon=True)
        thread.start()
        threads.append(thread)
    return threads


if __name__ == "__main__":
    output_queue = queue.Queue(maxsize=10000)
    # con pythonw stdout/stderr sono None, quindi vanno gestiti
    sys.stdout = ConsoleRedirector(output_queue, sys.stdout)
    sys.stderr = ConsoleRedirector(output_queue, sys.stderr)

    # I due bot girano nello stesso processo: il logging va configurato qui
    # una volta sola, altrimenti ogni bot.run() aggiunge un handler e ogni
    # riga di log viene stampata due volte
    discord.utils.setup_logging()

    # niente finestre console lampeggianti per ffmpeg/ffprobe
    hide_subprocess_windows()

    # Esegui i bot in thread separati
    start_bots()

    # Avvia la GUI
    launch_gui(output_queue)
