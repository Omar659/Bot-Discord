"""Tema grafico della console dei bot: palette, font e widget su misura.

L'ispirazione è l'estetica HUD/terminale fantascientifico: fondo quasi nero
bluastro, accenti al neon, testo monospaziato e cornici ad angoli aperti.
"""
import ctypes
import os
import tkinter as tk
import tkinter.font as tkfont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(BASE_DIR, "assets", "fonts")

# palette
BG_DEEP = "#05080f"      # fondo finestra
BG_PANEL = "#0a111c"     # pannelli
BG_INSET = "#070c15"     # interno console
LINE = "#16324a"         # cornici e griglie
CYAN = "#22d3ee"         # accento principale
MAGENTA = "#ff2e88"      # accento secondario
GREEN = "#3ef58b"        # stato attivo
AMBER = "#ffb020"        # avvisi
RED = "#ff4d5e"          # errori
TEXT = "#c6dcec"         # testo normale
DIM = "#4d6d85"          # testo secondario

# i font vengono caricati dal progetto, senza installarli nel sistema
FR_PRIVATE = 0x10
TITLE_FONT = "Orbitron"
MONO_FONT = "Share Tech Mono"


def load_fonts():
    """Registra i font solo per questo processo. Va chiamata prima di Tk()."""
    caricati = []
    if os.name != "nt" or not os.path.isdir(FONTS_DIR):
        return caricati
    for nome in os.listdir(FONTS_DIR):
        if not nome.lower().endswith((".ttf", ".otf")):
            continue
        percorso = os.path.join(FONTS_DIR, nome)
        try:
            if ctypes.windll.gdi32.AddFontResourceExW(
                    ctypes.c_wchar_p(percorso), FR_PRIVATE, 0):
                caricati.append(nome)
        except Exception:
            pass
    return caricati


def font_disponibile(nome, riserva):
    return nome if nome in tkfont.families() else riserva


def titolo_font(size, weight="normal"):
    return (font_disponibile(TITLE_FONT, "Bahnschrift"), size, weight)


def mono_font(size, weight="normal"):
    return (font_disponibile(MONO_FONT, "Consolas"), size, weight)


def barra_titolo_scura(root):
    """Barra del titolo scura (Windows 10 2004+), per non stonare col tema."""
    try:
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        valore = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20,
                                                   ctypes.byref(valore),
                                                   ctypes.sizeof(valore))
    except Exception:
        pass


def angoli_hud(canvas, x1, y1, x2, y2, colore=LINE, lato=14, spessore=1):
    """Cornice ad angoli aperti, il tratto tipico delle interfacce HUD."""
    for (ax, ay, dx, dy) in ((x1, y1, 1, 1), (x2, y1, -1, 1), (x1, y2, 1, -1),
                             (x2, y2, -1, -1)):
        canvas.create_line(ax, ay, ax + lato * dx, ay, fill=colore,
                           width=spessore)
        canvas.create_line(ax, ay, ax, ay + lato * dy, fill=colore,
                           width=spessore)


class NeonButton(tk.Frame):
    """Pulsante piatto con bordo al neon che si accende al passaggio del mouse."""

    def __init__(self, parent, text, colore, command, larghezza=15):
        super().__init__(parent,
                         bg=BG_PANEL,
                         highlightbackground=colore,
                         highlightthickness=1,
                         bd=0)
        self.colore = colore
        self.command = command
        self.label = tk.Label(self,
                              text=text,
                              font=mono_font(11),
                              bg=BG_PANEL,
                              fg=colore,
                              width=larghezza,
                              pady=7,
                              cursor="hand2")
        self.label.pack()
        for widget in (self, self.label):
            widget.bind("<Enter>", self._entra)
            widget.bind("<Leave>", self._esce)
            widget.bind("<Button-1>", self._click)

    def _entra(self, _=None):
        self.label.configure(bg=self.colore, fg=BG_DEEP)
        self.configure(bg=self.colore)

    def _esce(self, _=None):
        self.label.configure(bg=BG_PANEL, fg=self.colore)
        self.configure(bg=BG_PANEL)

    def _click(self, _=None):
        if self.command:
            self.command()


class StatusDot(tk.Canvas):
    """Pallino di stato che pulsa lentamente quando il bot è connesso."""

    def __init__(self, parent, dimensione=14):
        super().__init__(parent,
                         width=dimensione,
                         height=dimensione,
                         bg=BG_PANEL,
                         highlightthickness=0)
        self.dimensione = dimensione
        self.acceso = False
        self.fase = 0.0
        centro = dimensione / 2
        self.alone = self.create_oval(1, 1, dimensione - 1, dimensione - 1,
                                      outline="", fill=BG_PANEL)
        self.nucleo = self.create_oval(centro - 3, centro - 3, centro + 3,
                                       centro + 3, outline="", fill=DIM)

    def imposta(self, acceso):
        self.acceso = acceso
        if not acceso:
            self.itemconfigure(self.nucleo, fill=DIM)
            self.itemconfigure(self.alone, fill=BG_PANEL)

    def anima(self, passo):
        if not self.acceso:
            return
        self.fase = (self.fase + passo) % 1.0
        # da verde pieno a verde smorzato e ritorno
        intensita = 0.55 + 0.45 * abs(1 - 2 * self.fase)
        self.itemconfigure(self.nucleo, fill=self._sfuma(GREEN, intensita))
        self.itemconfigure(self.alone,
                           fill=self._sfuma(GREEN, intensita * 0.18))

    @staticmethod
    def _sfuma(colore, fattore):
        r = int(int(colore[1:3], 16) * fattore) + int(
            int(BG_PANEL[1:3], 16) * (1 - fattore))
        g = int(int(colore[3:5], 16) * fattore) + int(
            int(BG_PANEL[3:5], 16) * (1 - fattore))
        b = int(int(colore[5:7], 16) * fattore) + int(
            int(BG_PANEL[5:7], 16) * (1 - fattore))
        return "#%02x%02x%02x" % (min(r, 255), min(g, 255), min(b, 255))
