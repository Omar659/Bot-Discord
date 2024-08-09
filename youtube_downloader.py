from pytube import YouTube, Playlist
from youtube_search import YoutubeSearch
import os
import random


class YouTubeDownloader():
    def __init__(self, path, generate_idx_message):
        self.path = path
        self.generate_idx_message = generate_idx_message

    def __download_video(self, link, channels_audio, channel):
        yt = YouTube(link)
        # audio = yt.streams.filter(only_audio=True).first()
        print(yt.check_availability())
        audio = yt.streams.filter(only_audio=True, file_extension='mp4').first()

        exit()
        filename = audio.default_filename.replace("mp4", "mp3")
        last_audio_number = self.generate_idx_message() + 1
        filename = str(last_audio_number).zfill(5) + "_yt_" + filename
        file_path = os.path.join(self.path, filename)
        channels_audio[filename] = channel
        audio.download(self.path)
        os.rename(os.path.join(self.path, audio.default_filename), file_path)

    def __download_playlist(self, link, channels_audio, channel, stop,
                            random_queue):
        playlist = Playlist(link)
        video_urls = list(playlist.video_urls)
        random.shuffle(video_urls) if random_queue else None
        for url in video_urls:
            if stop["flag_yt"]:
                audio_tts = os.listdir("./youtube_musics/")
                for audio in audio_tts:
                    os.remove("./youtube_musics/" + audio)
                break
            self.__download_video(url, channels_audio, channel)

    def start_download(self, link, channels_audio, channel, stop,
                       random_queue):
        try:
            if not link or not self.path:
                print("Attenzione!",
                      "Inserisci un link e la cartella di download!")
                raise
            if "playlist?list=" in link:
                self.__download_playlist(link, channels_audio, channel, stop,
                                         random_queue)
            else:
                self.__download_video(link, channels_audio, channel)
        except Exception as e:
            print(e)
            print("Qualcosa è andato storto")

    def search_youtube_link(self, input):
        results = YoutubeSearch(input, max_results=1).to_dict()
        if results:
            return "https://www.youtube.com" + results[0]['url_suffix']
        else:
            return ""
