import yt_dlp
import os
import random
import shutil
from urllib.parse import quote


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
    def __init__(self, path, generate_idx_message):
        self.path = path
        self.generate_idx_message = generate_idx_message
        self.ffmpeg_location = find_ffmpeg()

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
        }
        if self.ffmpeg_location:
            opts['ffmpeg_location'] = self.ffmpeg_location
        return opts

    def __download_video(self, link, channels_audio, channel):
        ydl_opts = self.__base_opts()
        # si scarica in un nome temporaneo: il file finale viene reso visibile
        # al player solo dopo la conversione, con il nome definitivo
        ydl_opts['outtmpl'] = os.path.join(self.path, 'tmp_%(id)s.%(ext)s')

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            downloaded_filename = self.__final_path(ydl, info_dict)
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
            video_urls = [
                entry['url'] if entry.get('url', '').startswith('http')
                else f"https://www.youtube.com/watch?v={entry['id']}"
                for entry in playlist_dict.get('entries', []) if entry
            ]
            if random_queue:
                random.shuffle(video_urls)

        for url in video_urls:
            if stop["flag_yt"]:
                for audio in os.listdir(self.path):
                    try:
                        os.remove(os.path.join(self.path, audio))
                    except OSError:
                        pass
                break
            try:
                self.__download_video(url, channels_audio, channel)
            except Exception as e:
                # un video non disponibile non deve fermare tutta la playlist
                print(f"Download fallito per {url}: {e}")

    def start_download(self, link, channels_audio, channel, stop, random_queue):
        try:
            if not link or not self.path:
                print("Attenzione!", "Inserisci un link e la cartella di download!")
                raise ValueError("Link o percorso non valido")
            if "playlist?list=" in link:
                self.__download_playlist(link, channels_audio, channel, stop,
                                         random_queue)
            else:
                self.__download_video(link, channels_audio, channel)
        except Exception as e:
            print(e)
            print("Qualcosa è andato storto")

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
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            entries = info.get("entries") or []
            if not entries:
                return ""
            entry = entries[0]
            return entry.get("url") or f"https://www.youtube.com/watch?v={entry['id']}"
        except Exception as e:
            print(f"Errore nella ricerca YouTube: {e}")
            return ""
