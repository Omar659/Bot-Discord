"""Apre la finestra con log finti, solo per valutare la grafica."""
import queue
import sys
import ui_theme
from console_ui import ConsoleWindow

RIGHE = [
    "[2026-09-06 18:02:11] [INFO    ] discord.client: logging in using static token\n",
    "[2026-09-06 18:02:12] [INFO    ] discord.gateway: Shard ID None has connected to Gateway\n",
    "on_ready:\n\tWe have logged in as Lo Zozzone#6976\n",
    "on_ready:\n\tWe have logged in as La Zozzona#9351\n",
    "!join:\n\tJoin command executed with success.\n",
    "[2026-09-06 18:02:31] [INFO    ] discord.voice_state: Voice connection complete.\n",
    "Playlist trovata: Best Anime Openings/Endings\n",
    "Volume misurato -20.3 LUFS -> correggo di +6.3 dB\n",
    "#######\nDownloaded: JUJUTSU KAISEN Opening - Kaikai Kitan by Eve.opus\n######\n",
    "callback:\n\t00000_yt_JUJUTSU KAISEN Opening.opus | codec opus | durata 3:58 | canale Minecraft\n",
    "\tRiproduzione finita dopo 238.4s\n",
    "Salto la diretta: lofi hip hop radio - beats to relax/study to\n",
    "Voce cambiata in diego (it-IT-DiegoNeural)\n",
    "on_voice_state_update:\n\tVito e' entrato\n",
    "Download fallito per https://youtu.be/Q7w5IMyJ3pM: ERROR: Video unavailable\n",
    "Canale vuoto: mi disconnetto dalla voce.\n",
]

if __name__ == "__main__":
    ui_theme.load_fonts()
    q = queue.Queue(maxsize=10000)
    for r in RIGHE:
        q.put(r)
    finestra = ConsoleWindow(q, lambda root: sys.exit(0))
    # un po' di traffico continuo, per vedere il misuratore muoversi
    contatore = [0]

    def battito():
        contatore[0] += 1
        q.put("tick %d :: coda 4 brani :: uptime ok\n" % contatore[0])
        finestra.root.after(400, battito)

    finestra.root.after(1200, battito)
    finestra.avvia()
