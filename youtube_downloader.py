import yt_dlp
from yt_dlp.utils import match_filter_func
import json
import os
import random
import re
import shutil
import subprocess
from urllib.parse import quote

# volume di riferimento a cui portare tutti i brani (LUFS, stesso valore
# usato da YouTube e Spotify): senza, una canzone urla e la successiva sussurra
TARGET_LUFS = -14.0
# quanti secondi analizzare per misurare il volume: sui primi due minuti il
# risultato è già identico a quello del brano intero, ma costa molto meno
LOUDNESS_SAMPLE_SECONDS = 120
# limite al guadagno applicabile, per non far esplodere registrazioni pessime
MAX_GAIN_DB = 12.0


def find_ffmpeg():
    # ffmpeg serve a yt-dlp per estrarre l'audio: se non è nel PATH si prova
    # la copia installata con imageio-ffmpeg
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return os.path.dirname(ffmpeg)
    try:
        import imageio_ffmpeg
        return os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        return None


class YouTubeDownloader():
    def __init__(self, path, generate_idx_message, status=None, loudness=None):
        self.path = path
        self.generate_idx_message = generate_idx_message
        self.ffmpeg_location = find_ffmpeg()
        # motivo dell'ultimo fallimento, da mostrare in chat
        self.last_error = None
        # avanzamento del download, letto dal player per mostrare il contatore
        self.status = status if status is not None else {}
        # guadagno da applicare a ogni brano, indicizzato per titolo
        self.loudness = loudness if loudness is not None else {}
        # durata complessiva desiderata per una playlist, in secondi
        # (None = si scarica tutta)
        self.target_total = None
        self.reset_status()

    def reset_status(self):
        self.status.update({"active": False, "done": 0, "total": 0})

    def __base_opts(self):
        opts = {
            'format': 'bestaudio/best',
            # Opus è il formato che Discord usa davvero: salvando già in opus
            # la riproduzione può copiare lo stream invece di ricodificarlo,
            # che è quello che faceva scattare l'audio
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '160',
            }],
            'keepvideo': False,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            # la barra di avanzamento allagherebbe la console della GUI
            'noprogress': True,
            # le dirette non finiscono mai: scaricarle blocca la coda per
            # sempre e riempie il disco, quindi vanno rifiutate a monte
            'match_filter': match_filter_func('!is_live'),
        }
        if self.ffmpeg_location:
            opts['ffmpeg_location'] = self.ffmpeg_location
        return opts

    @staticmethod
    def durata_umana(secondi):
        secondi = int(secondi)
        if secondi >= 3600:
            return "%dh %02dm" % (secondi // 3600, (secondi % 3600) // 60)
        return "%dm %02ds" % (secondi // 60, secondi % 60)

    def scegli_fino_alla_durata(self, voci):
        """Sceglie i video il cui totale si avvicina di più alla durata chiesta.

        Prima si riempie la scaletta senza superare il bersaglio, scavalcando
        i video che non ci starebbero (in una scaletta da venti minuti quello
        da un'ora viene saltato, non chiude la selezione). Alla fine, se resta
        del tempo scoperto, si valuta un ultimo video: viene aggiunto solo se
        sforare avvicina più di quanto avvicini restare corti.
        """
        if self.target_total is None:
            return voci, None
        scelti, totale, esclusi = [], 0, []
        for indice, voce in enumerate(voci):
            durata = voce[1]
            if totale + durata <= self.target_total:
                scelti.append(indice)
                totale += durata
                if totale == self.target_total:
                    break
            else:
                esclusi.append((indice, durata))

        mancante = self.target_total - totale
        if mancante > 0 and esclusi:
            indice, durata = min(esclusi, key=lambda v: abs(v[1] - mancante))
            if abs(durata - mancante) < mancante:
                scelti.append(indice)
                totale += durata

        scelti.sort()      # l'ordine della playlist va rispettato
        return [voci[i] for i in scelti], totale

    def __download_video(self, link, channels_audio, channel, durata_nota=None):
        ydl_opts = self.__base_opts()
        # si scarica in un nome temporaneo: il file finale viene reso visibile
        # al player solo dopo la conversione, con il nome definitivo
        ydl_opts['outtmpl'] = os.path.join(self.path, 'tmp_%(id)s.%(ext)s')

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            # il match_filter salta il download ma restituisce comunque le
            # info: senza questo controllo si proverebbe a rinominare un file
            # che non è mai stato scaricato
            if info_dict is None or info_dict.get("is_live") or info_dict.get(
                    "live_status") == "is_live":
                raise ValueError("è una diretta, non posso metterla in coda")
            downloaded_filename = self.__final_path(ydl, info_dict)
            if not os.path.isfile(downloaded_filename):
                raise ValueError("il download non ha prodotto nessun file")
            print(f"\n\n\n#######\nDownloaded: {downloaded_filename}\n######\n\n\n")

            title = info_dict.get("title",
                                  os.path.basename(downloaded_filename))
            ext = os.path.splitext(downloaded_filename)[1]
            last_audio_number = self.generate_idx_message() + 1
            new_filename = (str(last_audio_number).zfill(5) + "_yt_" +
                            self.__safe_title(title) + ext)
            new_file_path = os.path.join(self.path, new_filename)
            os.replace(downloaded_filename, new_file_path)
            channels_audio[new_filename] = channel
            self.loudness[self.__safe_title(title)] = self.measure_gain(
                new_file_path)
            self.status["done"] = self.status.get("done", 0) + 1

    def measure_gain(self, path):
        # moltiplicatore da applicare al brano per portarlo a TARGET_LUFS
        try:
            result = subprocess.run([
                "ffmpeg", "-hide_banner", "-nostats", "-t",
                str(LOUDNESS_SAMPLE_SECONDS), "-i", path, "-af",
                "loudnorm=I=%s:TP=-1:print_format=json" % TARGET_LUFS, "-f",
                "null", "-"
            ],
                                    capture_output=True,
                                    text=True,
                                    errors="ignore",
                                    timeout=120)
            blocks = re.findall(r"\{[^{}]*input_i[^{}]*\}", result.stderr,
                                re.S)
            measured = float(json.loads(blocks[-1])["input_i"])
            gain_db = max(-MAX_GAIN_DB, min(MAX_GAIN_DB,
                                            TARGET_LUFS - measured))
            print("Volume misurato %.1f LUFS -> correggo di %+.1f dB" %
                  (measured, gain_db))
            return 10**(gain_db / 20.0)
        except Exception as e:
            print("Misura del volume non riuscita:", e)
            return 1.0

    @staticmethod
    def __final_path(ydl, info_dict):
        # dopo la conversione il nome vero è nelle info; prepare_filename
        # restituirebbe l'estensione del download originale (.webm/.m4a)
        for entry in info_dict.get("requested_downloads") or []:
            if entry.get("filepath"):
                return entry["filepath"]
        base = os.path.splitext(ydl.prepare_filename(info_dict))[0]
        return base + ".opus"

    @staticmethod
    def __safe_title(title):
        # "_" separa i campi nel nome file e alcuni caratteri non sono validi
        # nei nomi file di Windows
        for char in '\\/:*?"<>|_':
            title = title.replace(char, "-")
        return title.strip()[:100]

    def __download_playlist(self, link, channels_audio, channel, stop,
                            random_queue):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # estrai solo i metadati senza scaricare
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_dict = ydl.extract_info(link, download=False)
            video_urls = []
            senza_durata = 0
            for entry in playlist_dict.get('entries', []) or []:
                if not entry:
                    continue
                durata = entry.get("duration")
                # senza durata non si può fare il conto: con un bersaglio
                # impostato queste voci si lasciano fuori
                if durata is None:
                    senza_durata += 1
                    if self.target_total is not None:
                        continue
                    durata = 0
                url = (entry['url'] if entry.get('url', '').startswith('http')
                       else f"https://www.youtube.com/watch?v={entry['id']}")
                video_urls.append((url, durata))
            # prima si mescola, poi si taglia: così con l'ordine casuale la
            # selezione cambia ogni volta invece di essere sempre la stessa
            if random_queue:
                random.shuffle(video_urls)
            totali = len(video_urls)
            video_urls, totale_scelto = self.scegli_fino_alla_durata(video_urls)
            if totale_scelto is not None:
                print("Durata chiesta %s: scelti %d video su %d, totale %s" %
                      (self.durata_umana(self.target_total), len(video_urls),
                       totali, self.durata_umana(totale_scelto)))
            if senza_durata and self.target_total is not None:
                print("Saltati %d video di durata sconosciuta" % senza_durata)
            if self.target_total is not None and not video_urls:
                raise ValueError(
                    "nessun video si avvicina ai %s richiesti: sono tutti "
                    "troppo lunghi" % self.durata_umana(self.target_total))

        # da qui il player sa quanti brani aspettarsi
        self.status["total"] = len(video_urls)
        for url, durata in video_urls:
            if stop["flag_yt"]:
                for audio in os.listdir(self.path):
                    try:
                        os.remove(os.path.join(self.path, audio))
                    except OSError:
                        pass
                break
            try:
                self.__download_video(url, channels_audio, channel, durata)
            except Exception as e:
                # un video non disponibile non deve fermare tutta la playlist
                print(f"Download fallito per {url}: {e}")

    def start_download(self, link, channels_audio, channel, stop, random_queue):
        self.last_error = None
        self.reset_status()
        self.status["active"] = True
        try:
            if not link or not self.path:
                print("Attenzione!", "Inserisci un link e la cartella di download!")
                raise ValueError("Link o percorso non valido")
            if "playlist?list=" in link:
                self.__download_playlist(link, channels_audio, channel, stop,
                                         random_queue)
            else:
                self.status["total"] = 1
                self.__download_video(link, channels_audio, channel)
        except Exception as e:
            print(e)
            print("Qualcosa è andato storto")
            self.last_error = str(e)
            self.__clean_partials()
        finally:
            self.status["active"] = False

    def __clean_partials(self):
        # i download interrotti lasciano file .part e temporanei
        for name in os.listdir(self.path):
            if name.startswith("tmp_") or name.endswith(".part"):
                try:
                    os.remove(os.path.join(self.path, name))
                except OSError:
                    pass

    def search_youtube_playlist(self, query):
        # yt-dlp non ha una ricerca playlist nativa: si usa la pagina dei
        # risultati di YouTube con il filtro "playlist" (sp=EgIQAw%3D%3D)
        try:
            url = ("https://www.youtube.com/results?search_query=" +
                   quote(query) + "&sp=EgIQAw%3D%3D")
            with yt_dlp.YoutubeDL({
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                    'playlistend': 5,
            }) as ydl:
                info = ydl.extract_info(url, download=False)
            for entry in info.get("entries") or []:
                link = entry.get("url") or ""
                if "list=" in link:
                    print(f"Playlist trovata: {entry.get('title')}")
                    return link
                if entry.get("id"):
                    return "https://www.youtube.com/playlist?list=" + entry["id"]
            return ""
        except Exception as e:
            print(f"Errore nella ricerca della playlist: {e}")
            return ""

    def search_youtube_link(self, query):
        # ricerca fatta con yt-dlp: youtube-search-python non è più mantenuto
        # e fallisce con le versioni recenti delle sue dipendenze
        try:
            with yt_dlp.YoutubeDL({
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                    'default_search': 'ytsearch',
            }) as ydl:
                # più di un risultato: i primi sono spesso radio in diretta,
                # che non si possono scaricare
                info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            for entry in info.get("entries") or []:
                if entry.get("live_status") == "is_live":
                    print(f"Salto la diretta: {entry.get('title')}")
                    continue
                return entry.get(
                    "url") or f"https://www.youtube.com/watch?v={entry['id']}"
            return ""
        except Exception as e:
            print(f"Errore nella ricerca YouTube: {e}")
            return ""
