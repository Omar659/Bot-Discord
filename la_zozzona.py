import discord
from discord.ext import commands
import os
from os import system
from youtube_downloader import YouTubeDownloader
import time
import threading
import asyncio
from threading import Thread
import random
from utils import print_in_chat

bots_name = ["Neeko", "Lo Zozzone", "inter·punct", "Lara✨", "Lo Zozzone AUDIO"]
sound_prefix = "-"
yt_prefix = ">"
utils_prefix_lo_zozzone = "!"
utils_prefix_la_zozzona = "^"
bots_prefix = [
    utils_prefix_lo_zozzone, utils_prefix_la_zozzona, yt_prefix, sound_prefix
]


class MyBotAUDIO(commands.Bot):
    def __init__(self, command_prefix, self_bot):
        # init of the superclass
        intents = discord.Intents.all()
        intents.members = True
        # intents.message_content = True
        commands.Bot.__init__(self,
                              command_prefix=command_prefix,
                              self_bot=self_bot,
                              intents=intents)
        # voice client where the bot is connected
        self.voice_client = None
        # path of the text to speech files
        self.message_audio_path = "./youtube_musics/"
        # used to initialize the thread
        self.play_messages_is_run = False

        self.stop_yt = {"flag_yt": False}
        self.channels_audio = {}
        self.youtube_downloader = YouTubeDownloader("./youtube_musics/",
                                                    self.generate_idx_message)

    ############
    # commands #
    ############
    async def join(self, ctx):
        # join command
        print("!join:")
        try:
            channel = ctx.author.voice.channel
            self.voice_client = await channel.connect()
            print("\tJoin command executed with success.")
        except AttributeError:
            print(
                "\tError! You are not connected to the channel available to me."
            )
        except Exception as e:
            print("exetpion")
            print("\t" + str(e))

    #################
    # system events #
    #################
    async def on_disconnect(self):
        audio_tts = os.listdir(self.message_audio_path)
        for audio in audio_tts:
            os.remove(self.message_audio_path + audio)
        print("on_disconnect:")

    async def on_ready(self):
        # when the bot is ready remove old messages
        print("on_ready:")
        audio_tts = os.listdir(self.message_audio_path)
        for audio in audio_tts:
            os.remove(self.message_audio_path + audio)
        print('\tWe have logged in as {0.user}'.format(self))

    async def on_message(self, message):
        name = message.author.name if str(
            message.author.nick) == str(None) else message.author.nick
        ctx = await self.get_context(message)
        await self.join(ctx)
        # if is some message from bot
        if name in bots_name:
            return
        if (message.author == self.user or message.content[0] in bots_prefix):
            # Youtube
            if message.content[0] == yt_prefix:
                if message.content.lower().startswith(yt_prefix + "youtube"):
                    helper = "```TODO```"
                    await print_in_chat(helper, ctx, monospace=True)
                elif message.content.lower().startswith(yt_prefix + "play"):
                    self.stop_yt["flag_yt"] = False
                    try:
                        random_queue = True if message.content.split(
                            " ")[1] == "-random" else False
                        len_not_link = yt_prefix
                        len_not_link += "play"
                        len_not_link += " -random " if random_queue else " "
                        len_not_link = len(len_not_link)
                        link = message.content[len_not_link:].strip()
                        await self.save_youtube_music(
                            link, message.author.voice.channel, random_queue)
                    except Exception as e:
                        print(e)
                        await print_in_chat("Youtube video not found", ctx)
                elif message.content.lower().startswith(yt_prefix + "now"):
                    yt_musics = [
                        x[9:-4] for x in os.listdir("./youtube_musics")
                        if "_yt_" in x
                    ]
                    yt_musics.sort(reverse=True)
                    await print_in_chat("Attualmente in esecuzione: " +
                                           str(yt_musics[0]), ctx)
                elif message.content.lower().startswith(yt_prefix + "shuffle"):
                    count = 0
                    while True:
                        try:
                            yt_musics = os.listdir("./youtube_musics")[1:]
                            numbers = [int(x.split("_")[0]) for x in yt_musics]
                            random.shuffle(numbers)
                            new_yt_musics = [
                                str(numbers[i]).zfill(5) + "_" +
                                "_".join(x.split("_")[1:])
                                for i, x in enumerate(yt_musics)
                            ]
                            for i, new_yt_music in enumerate(new_yt_musics):
                                os.rename("./youtube_musics/" + yt_musics[i],
                                          "./youtube_musics/" + new_yt_music)
                            await print_in_chat("Shuffle eseguito", ctx)
                            break
                        except:
                            count += 1
                            if count > 10:
                                await print_in_chat("Errore nella shuffle, riprova", ctx)
                                break
                            continue
                elif message.content.lower().startswith(yt_prefix + "queue"):
                    yt_musics = [
                        x[9:-4] for x in os.listdir("./youtube_musics")
                        if "_yt_" in x
                    ]
                    yt_musics.sort(reverse=True)
                    yt_musics = "\n".join([
                        "\t" + str(i + 1).zfill(len(str(len(yt_musics)))) +
                        ") " + x + (" <- IN ESECUZIONE" if i == 0 else "")
                        for i, x in enumerate(yt_musics)
                    ])
                    await print_in_chat("Queue:\n" + yt_musics, ctx, monospace=True, split_character=False)
                elif message.content.lower().startswith(yt_prefix + "stop"):
                    self.stop_yt["flag_yt"] = True
                    await print_in_chat("Musica da youtube stoppata", ctx)
            # elif message.content[0] == other_prefix: #TODO
            return

    ###########
    # Utility #
    ###########
    def play_messages(self):
        try:
            # repeat until the message audio folder is empty
            while os.listdir(self.message_audio_path) != []:
                self.play_messages_is_run = True
                audio_tts = os.listdir(self.message_audio_path)
                audio_tts.sort()
                if audio_tts != []:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    loop.run_until_complete(self.callback(audio_tts))
                    loop.close()
                time.sleep(1)
        except Exception as e:
            print(e)
            audio_tts = os.listdir(self.message_audio_path)
            for audio in audio_tts:
                os.remove(self.message_audio_path + audio)
        self.play_messages_is_run = False

    async def callback(self, audio_tts):
        # play the text to speech audio
        print("callback:")
        audio2play = audio_tts[0]
        audio_source = await discord.FFmpegOpusAudio.from_probe(
            self.message_audio_path + audio2play, options='-filter:a loudnorm')
        await self.voice_client.move_to(self.channels_audio[audio2play])
        # when the bot switch channel the voice client change
        # so I catch the error and I rerun the command untill it work
        while True:
            try:
                self.voice_client.play(audio_source)
                break
            except Exception as e:
                print("\t", e)
                time.sleep(1)
                continue
        while self.voice_client.is_playing():
            time.sleep(0.1)
            if self.stop_yt["flag_yt"]:
                self.voice_client.stop()
                break
        # remove audio
        if self.stop_yt["flag_yt"]:
            for yt_file in [_ for _ in audio_tts if _.split("_")[1] == "yt"]:
                os.remove(self.message_audio_path + yt_file)
        else:
            os.remove(self.message_audio_path + audio2play)

    def generate_idx_message(self):
        audio_tts = os.listdir(self.message_audio_path)
        audio_tts.sort(key=lambda x: int(x.split("_")[0]))
        if os.listdir(self.message_audio_path) == []:
            last_audio_number = -1
        else:
            last_audio_number = int(audio_tts[-1].split("_")[0])
        return last_audio_number

    async def save_youtube_music(self, input, channel, random_queue):
        try:
            if self.voice_client is None:
                self.voice_client = await channel.connect()
            dst_folder = "./youtube_musics/"

            link = input.strip() if input.strip().startswith(
                "https://") else self.youtube_downloader.search_youtube_link(
                    input)
            if link == "":
                print("Video non trovato")
                return

            yt_down_thread = Thread(
                target=self.youtube_downloader.start_download,
                args=(link, self.channels_audio, channel, self.stop_yt,
                      random_queue))
            yt_down_thread.start()

            while len([_ for _ in os.listdir(dst_folder) if "_yt_" in _]) == 0:
                time.sleep(0.1)
            if not self.play_messages_is_run:
                play_messages_thread = threading.Thread(
                    target=self.play_messages)
                play_messages_thread.start()
        except Exception as e:
            print(
                "##########################\nERRORE\n##########################"
            )
            print(e)
            raise


def main():
    try:
        bot = MyBotAUDIO(command_prefix=utils_prefix_la_zozzona,
                         self_bot=False)
        bot.run(os.getenv('TOKEN_ZOZZONE_AUDIO'))
    except discord.errors.HTTPException as e:
        if str(e.status) == "429":
            print("\n\n\nBLOCKED BY RATE LIMITS\nRESTARTING NOW\n\n\n")
            system("python restarter.py")
            system('kill 1')
