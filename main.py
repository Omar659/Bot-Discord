import discord
from lo_zozzone import main as main_zozzone
from la_zozzona import main as main_zozzona
from utils import hide_subprocess_windows, kill_child_processes
import ui_theme
from console_ui import ConsoleWindow
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
    # i font del tema vanno registrati prima di creare la finestra
    ui_theme.load_fonts()

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

    # Avvia la finestra di controllo
    ConsoleWindow(output_queue, stop_all_bots).avvia()
