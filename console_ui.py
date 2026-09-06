"""Finestra di controllo dei bot: intestazione HUD, stato, console colorata."""
import collections
import os
import queue
import re
import time

try:
    import psutil
except ImportError:  # la telemetria è un extra: senza, la GUI funziona uguale
    psutil = None
import tkinter as tk
from tkinter import ttk

import ui_theme as T

# quante righe tenere nella console: un widget che cresce all'infinito
# rallenta Tkinter fino a bloccare la finestra dopo qualche ora di log
MAX_CONSOLE_LINES = 2000
# quanti messaggi scrivere per ogni giro: se ne arriva una valanga (un
# traceback ripetuto) svuotare tutta la coda in un colpo congela la GUI
MAX_MESSAGES_PER_TICK = 200
TICK_MS = 100
FRAME_MS = 60

# regole di colorazione, applicate riga per riga nell'ordine in cui stanno qui
REGOLE = (
    ("errore",
     re.compile(r"error|traceback|exception|failed|fallit|non riusc", re.I)),
    ("avviso",
     re.compile(r"warning|attenzione|salto |scartat|non trovat", re.I)),
    ("ok",
     re.compile(r"downloaded|logged in|connection complete|eseguito|"
                r"volume misurato|playlist trovata", re.I)),
    ("evento",
     re.compile(r"^(on_|callback|!join|\s*Riproduzione|Voce cambiata|"
                r"Canale vuoto|Stopping|Playlist)", re.I)),
    ("discord",
     re.compile(r"^\[\d{4}-\d{2}-\d{2}|discord\.(client|gateway|voice_state|"
                r"player|voice_client)", re.I)),
)


class ConsoleWindow:
    def __init__(self, output_queue, on_stop):
        self.output_queue = output_queue
        self.on_stop = on_stop
        self.closing = False
        self.avvio = time.time()
        self.autoscroll = True
        # traffico recente, per il misuratore di attività
        self.traffico = collections.deque([0] * 40, maxlen=40)
        self.messaggi_tick = 0
        self.stati = {}
        self.barre = []
        self.processo = psutil.Process() if psutil else None
        self.cartella_coda = os.path.join(T.BASE_DIR, "youtube_musics")

        self.root = tk.Tk()
        self.root.title("I ZOZZONI - Bot Control Deck")
        self.root.configure(bg=T.BG_DEEP)
        self._geometria()
        try:
            self.root.iconbitmap(os.path.join(T.BASE_DIR, "icon.ico"))
        except Exception:
            pass
        T.barra_titolo_scura(self.root)

        self._costruisci()
        self.root.protocol("WM_DELETE_WINDOW", self.chiudi)
        self.root.after(TICK_MS, self._svuota_coda)
        self.root.after(FRAME_MS, self._anima)

    # ---------------------------------------------------------------- layout
    def _geometria(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = int(sw * 0.72), int(sh * 0.78)
        self.root.geometry("%dx%d+%d+%d" % (w, h, (sw - w) // 2, (sh - h) // 2))
        self.root.minsize(880, 560)

    def _costruisci(self):
        cornice = tk.Frame(self.root, bg=T.BG_DEEP)
        cornice.pack(fill=tk.BOTH, expand=True, padx=18, pady=14)
        self._intestazione(cornice)
        self._pannello_stato(cornice)
        self._console(cornice)
        self._barra_comandi(cornice)

    def _intestazione(self, parent):
        self.header = tk.Canvas(parent,
                                height=116,
                                bg=T.BG_DEEP,
                                highlightthickness=0)
        self.header.pack(fill=tk.X)
        self.header.bind("<Configure>", self._disegna_intestazione)

    def _disegna_intestazione(self, _=None):
        c = self.header
        c.delete("all")
        w = max(c.winfo_width(), 400)
        h = 116
        # griglia di sfondo, appena accennata
        for x in range(0, w, 26):
            c.create_line(x, 0, x, h, fill="#0b1520")
        for y in range(0, h, 26):
            c.create_line(0, y, w, y, fill="#0b1520")
        T.angoli_hud(c, 2, 2, w - 3, h - 3, T.LINE, lato=18)

        # titolo, con un alone dietro per dare profondità
        c.create_text(28, 34, text="I  Z O Z Z O N I", anchor="w",
                      font=T.titolo_font(26, "bold"), fill="#0e4d5e")
        c.create_text(26, 32, text="I  Z O Z Z O N I", anchor="w",
                      font=T.titolo_font(26, "bold"), fill=T.CYAN)
        c.create_text(30, 66, text="BOT CONTROL DECK", anchor="w",
                      font=T.mono_font(11), fill=T.DIM)
        c.create_text(30, 88, text="lo zozzone  ::  la zozzona", anchor="w",
                      font=T.mono_font(9), fill="#31506a")

        # blocco telemetria: sessione, carico e memoria
        self.uptime_id = c.create_text(w - 28, 30, text="00:00:00", anchor="e",
                                       font=T.mono_font(16), fill=T.CYAN)
        c.create_text(w - 28, 48, text="UPTIME SESSIONE", anchor="e",
                      font=T.mono_font(8), fill=T.DIM)
        self.telemetria_id = c.create_text(w - 28, 64, text="", anchor="e",
                                           font=T.mono_font(10), fill=T.DIM)

        # misuratore di attività della console
        self.barre = []
        passo, larghezza = 5, 3
        x0 = w - 28 - (len(self.traffico) * passo)
        for i in range(len(self.traffico)):
            x = x0 + i * passo
            self.barre.append(
                c.create_rectangle(x, 94, x + larghezza, 96, outline="",
                                   fill="#123449"))
        c.create_line(x0, 97, w - 28, 97, fill="#0f2637")
        c.create_text(x0 - 10, 90, text="ATTIVITÀ", anchor="e",
                      font=T.mono_font(8), fill="#2c4a61")

        # linea di scansione che attraversa l'intestazione
        self.scanline = [
            c.create_line(0, h - 2, 60, h - 2, fill="#0d3b4d", width=2),
            c.create_line(0, h - 2, 60, h - 2, fill="#12718c", width=2),
            c.create_line(0, h - 2, 60, h - 2, fill=T.CYAN, width=2),
        ]
        self.scan_x = 0

    def _pannello_stato(self, parent):
        riga = tk.Frame(parent, bg=T.BG_DEEP)
        riga.pack(fill=tk.X, pady=(12, 10))
        schede = (("LO ZOZZONE", T.CYAN, "voce, benvenuti, soundboard"),
                  ("LA ZOZZONA", T.MAGENTA, "musica da youtube"))
        for indice, (nome, colore, ruolo) in enumerate(schede):
            scheda = tk.Frame(riga, bg=T.BG_PANEL,
                              highlightbackground=T.LINE,
                              highlightthickness=1)
            scheda.pack(side=tk.LEFT, expand=True, fill=tk.X,
                        padx=(0, 10) if indice == 0 else (0, 0))
            interno = tk.Frame(scheda, bg=T.BG_PANEL)
            interno.pack(fill=tk.X, padx=14, pady=10)
            punto = T.StatusDot(interno)
            punto.pack(side=tk.LEFT, padx=(0, 12))
            testi = tk.Frame(interno, bg=T.BG_PANEL)
            testi.pack(side=tk.LEFT, anchor="w")
            tk.Label(testi, text=nome, font=T.titolo_font(11, "bold"),
                     bg=T.BG_PANEL, fg=colore).pack(anchor="w")
            stato = tk.Label(testi, text="in attesa di connessione...",
                             font=T.mono_font(9), bg=T.BG_PANEL, fg=T.DIM)
            stato.pack(anchor="w")
            tk.Label(interno, text=ruolo, font=T.mono_font(9), bg=T.BG_PANEL,
                     fg="#2c4a61").pack(side=tk.RIGHT)
            self.stati[nome] = {"punto": punto, "label": stato,
                                "online": False}

        motore = tk.Frame(riga, bg=T.BG_PANEL, highlightbackground=T.LINE,
                          highlightthickness=1)
        motore.pack(side=tk.LEFT, fill=tk.X, padx=(10, 0))
        interno = tk.Frame(motore, bg=T.BG_PANEL)
        interno.pack(fill=tk.X, padx=14, pady=10)
        tk.Label(interno, text="MOTORE AUDIO", font=T.titolo_font(11, "bold"),
                 bg=T.BG_PANEL, fg=T.GREEN).pack(anchor="w")
        self.motore_label = tk.Label(interno, text="coda vuota",
                                     font=T.mono_font(9), bg=T.BG_PANEL,
                                     fg=T.DIM)
        self.motore_label.pack(anchor="w")

    def _console(self, parent):
        contenitore = tk.Frame(parent, bg=T.BG_PANEL,
                               highlightbackground=T.LINE,
                               highlightthickness=1)
        contenitore.pack(fill=tk.BOTH, expand=True)

        barra = tk.Frame(contenitore, bg=T.BG_PANEL)
        barra.pack(fill=tk.X, padx=12, pady=(8, 0))
        tk.Label(barra, text="| CONSOLE", font=T.mono_font(10),
                 bg=T.BG_PANEL, fg=T.CYAN).pack(side=tk.LEFT)
        self.contatore = tk.Label(barra, text="0 righe", font=T.mono_font(9),
                                  bg=T.BG_PANEL, fg=T.DIM)
        self.contatore.pack(side=tk.RIGHT)

        area = tk.Frame(contenitore, bg=T.BG_INSET)
        area.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        stile = ttk.Style()
        stile.theme_use("clam")
        stile.configure("Neon.Vertical.TScrollbar", troughcolor=T.BG_INSET,
                        background=T.LINE, darkcolor=T.BG_INSET,
                        lightcolor=T.BG_INSET, bordercolor=T.BG_INSET,
                        arrowcolor=T.DIM, gripcount=0)
        stile.map("Neon.Vertical.TScrollbar", background=[("active", T.CYAN)])

        self.box = tk.Text(area, wrap=tk.WORD, bg=T.BG_INSET, fg=T.TEXT,
                           insertbackground=T.CYAN, font=T.mono_font(11),
                           relief=tk.FLAT, padx=12, pady=8,
                           selectbackground="#14405a", spacing1=1)
        scroll = ttk.Scrollbar(area, orient="vertical", command=self.box.yview,
                               style="Neon.Vertical.TScrollbar")
        self.box.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.box.tag_configure("normale", foreground=T.TEXT)
        self.box.tag_configure("discord", foreground="#3c6382")
        self.box.tag_configure("evento", foreground=T.CYAN)
        self.box.tag_configure("ok", foreground=T.GREEN)
        self.box.tag_configure("avviso", foreground=T.AMBER,
                               background="#20180a")
        self.box.tag_configure("errore", foreground=T.RED,
                               background="#240d12")
        self.box.tag_configure("ok", foreground=T.GREEN)

    def _barra_comandi(self, parent):
        riga = tk.Frame(parent, bg=T.BG_DEEP)
        riga.pack(fill=tk.X, pady=(12, 0))
        T.NeonButton(riga, "ARRESTA TUTTO", T.RED, self.chiudi,
                     larghezza=18).pack(side=tk.LEFT)
        T.NeonButton(riga, "PULISCI", T.CYAN, self.pulisci,
                     larghezza=12).pack(side=tk.LEFT, padx=10)
        self.bottone_scroll = T.NeonButton(riga, "AUTOSCROLL: ON", T.GREEN,
                                           self.toggle_scroll, larghezza=18)
        self.bottone_scroll.pack(side=tk.LEFT)
        tk.Label(riga, text="entrambi i bot girano in questo processo",
                 font=T.mono_font(9), bg=T.BG_DEEP,
                 fg=T.DIM).pack(side=tk.RIGHT)

    # ---------------------------------------------------------------- azioni
    def pulisci(self):
        self.box.delete("1.0", tk.END)
        self.contatore.configure(text="0 righe")

    def toggle_scroll(self):
        self.autoscroll = not self.autoscroll
        stato = "ON" if self.autoscroll else "OFF"
        colore = T.GREEN if self.autoscroll else T.AMBER
        self.bottone_scroll.colore = colore
        self.bottone_scroll.label.configure(text="AUTOSCROLL: " + stato,
                                            fg=colore)
        self.bottone_scroll.configure(highlightbackground=colore)

    def chiudi(self):
        self.closing = True
        self.on_stop(self.root)

    # ---------------------------------------------------------- aggiornamenti
    @staticmethod
    def _tag_per_riga(riga):
        for nome, regola in REGOLE:
            if regola.search(riga):
                return nome
        return "normale"

    def _aggiorna_stati(self, testo):
        # il bot annuncia "We have logged in as <nome>" quando è operativo
        if "logged in as" not in testo:
            return
        compatto = testo.replace(" ", "").lower()
        for nome, stato in self.stati.items():
            if stato["online"]:
                continue
            if nome.replace(" ", "").lower() in compatto:
                stato["online"] = True
                stato["punto"].imposta(True)
                stato["label"].configure(text="connesso  ::  operativo",
                                         fg=T.GREEN)

    def _svuota_coda(self):
        if self.closing:
            return
        try:
            pezzi = []
            for _ in range(MAX_MESSAGES_PER_TICK):
                try:
                    pezzi.append(self.output_queue.get_nowait())
                except queue.Empty:
                    break
            self.messaggi_tick = len(pezzi)
            if pezzi:
                testo = "".join(pezzi)
                self._aggiorna_stati(testo)
                self._inserisci(testo)
        except Exception:
            # un errore qui finirebbe su stderr, cioè di nuovo in questa
            # coda: si creerebbe un ciclo che blocca la finestra
            pass
        if not self.closing:
            self.root.after(TICK_MS, self._svuota_coda)

    def _inserisci(self, testo):
        # righe consecutive dello stesso tipo vengono scritte in un colpo solo
        blocco, tag_corrente = [], None
        for riga in testo.splitlines(True):
            tag = self._tag_per_riga(riga)
            if tag != tag_corrente and blocco:
                self.box.insert(tk.END, "".join(blocco), tag_corrente)
                blocco = []
            tag_corrente = tag
            blocco.append(riga)
        if blocco:
            self.box.insert(tk.END, "".join(blocco), tag_corrente)

        righe = int(self.box.index("end-1c").split(".")[0])
        if righe > MAX_CONSOLE_LINES:
            self.box.delete("1.0", "%d.0" % (righe - MAX_CONSOLE_LINES))
            righe = MAX_CONSOLE_LINES
        self.contatore.configure(text="%d righe" % righe)
        if self.autoscroll:
            self.box.yview(tk.END)

    def _anima(self):
        if self.closing:
            return
        c = self.header
        w = max(c.winfo_width(), 400)

        # linea di scansione con scia
        self.scan_x = (self.scan_x + 9) % (w + 200)
        for indice, segmento in enumerate(self.scanline):
            fine = self.scan_x - indice * 55
            c.coords(segmento, fine - 55, 102, fine, 102)

        # orologio di sessione
        trascorso = int(time.time() - self.avvio)
        c.itemconfigure(self.uptime_id,
                        text="%02d:%02d:%02d" % (trascorso // 3600,
                                                 (trascorso % 3600) // 60,
                                                 trascorso % 60))

        # misuratore di attività
        self.traffico.append(self.messaggi_tick)
        self.messaggi_tick = 0
        massimo = max(max(self.traffico), 1)
        for barra, valore in zip(self.barre, self.traffico):
            quota = valore / massimo
            altezza = 2 + int(16 * quota)
            coord = c.coords(barra)
            if coord:
                c.coords(barra, coord[0], 96 - altezza, coord[2], 96)
                if not valore:
                    colore = "#123449"
                elif valore >= 15:      # raffica di log
                    colore = T.MAGENTA
                else:
                    colore = T.CYAN
                c.itemconfigure(barra, fill=colore)

        for stato in self.stati.values():
            stato["punto"].anima(0.06)

        self._telemetria()
        self.root.after(FRAME_MS, self._anima)

    def _telemetria(self):
        # aggiornata una volta al secondo: leggere carico e cartella a ogni
        # fotogramma sarebbe sprecato
        adesso = time.time()
        if adesso - getattr(self, "_ultima_telemetria", 0) < 1.0:
            return
        self._ultima_telemetria = adesso

        if self.processo is not None:
            try:
                cpu = self.processo.cpu_percent()
                ram = self.processo.memory_info().rss / (1024 * 1024)
                figli = len([p for p in self.processo.children()
                             if p.is_running()])
                self.header.itemconfigure(
                    self.telemetria_id,
                    text="CPU %4.1f%%   RAM %4.0f MB   PROC %d" %
                    (cpu, ram, figli))
            except Exception:
                pass

        try:
            brani = [f for f in os.listdir(self.cartella_coda)
                     if "_yt_" in f and f.lower().endswith(
                         (".opus", ".mp3", ".ogg", ".m4a", ".wav"))]
        except OSError:
            brani = []
        if brani:
            testo = "%d brani in coda" % len(brani)
            colore = T.GREEN
        else:
            testo = "coda vuota"
            colore = T.DIM
        self.motore_label.configure(text=testo, fg=colore)

    def avvia(self):
        self.root.mainloop()
