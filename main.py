import discord
from discord.ext import commands
import shutil
import os
from os import system
from keep_alive import keep_alive
import time
# from discord.ui import Button
from gtts import gTTS
import threading
import asyncio
import random

bots_name = ["Neeko", "Lo Zozzone"]
sound_prefix = "-"
bots_prefix = ["!", sound_prefix]
names_om = [
    "L'invincibile", "Il maestro supremo", "Il dominatore incontrastato",
    "L'artefice di ogni vittoria", "Il colosso imprendibile",
    "Il signore del destino", "L'occhio che tutto vede",
    "Il supremo comandante", "L'imperatore immortale.", "Il principe oscuro",
    "L'incubo degli avversari", "Il cavaliere errante", "L'ombra silenziosa",
    "Il guardiano delle tenebre", "L'architetto del caos", "Il mago supremo",
    "Il dio della guerra", "Il giustiziere implacabile"
]
welcome_messages = [
    "Che gioia averti tra noi _nome_. Benvenuto!",
    "Stare qui non aveva senso senza di te. Benvenuto _nome_!",
    "Finalmente è arrivato il tanto desiderato _nome_!",
    "Benvenuto nel server _nome_!",
    "Benvenuto nel nostro server _nome_, faremo grandi cose insieme",
    "Benvenuto nel server _nome_, entra e lascia un po’ della felicità che porti",
    "Un caldo benvenuto a _nome_, nostro raggio di sole che rallegra il nostro server.",
    "Ciao _nome_, sono contento che tu abbia deciso di entrare nel server. Benvenuto!",
    "Si ritorna solo andando via. Sono felice che tu sia di nuovo qui _nome_. Benvenuto nel server.",
    "Che gioia averti tra noi _nome_. Benvenuto!",
    "Un caloroso benvenuto _nome_.",
    "Benvenuto _nome_, regalaci la tua forza vivifica.",
    "Benvenuto _nome_, l’attendevamo con ansia e afa",
    "_nome_, benvenuto nel server. Entra e mettiti comodo"
]

sounds = {
    sound_prefix + "baka": ["baka.mp3", "Baka detto in modo carino"],
    sound_prefix + "banishment":
    ["banishment.ogg", "Chuunibyou \"Banishment this warudo\""],
    sound_prefix + "chance boru":
    ["chance boru.mp3", "Dal nostro haycoso... CHANCE BORUUU"],
    sound_prefix + "eliminato":
    ["eliminato.ogg", "Teru Mikami, ELIMINATO ELIMINATOOOOOO"],
    sound_prefix + "eren": [
        "eren.ogg",
        "Subete no yimiru no taminitsugu... Ore no na wa... Eren Yega"
    ],
    sound_prefix + "kira risata":
    ["kira laugh.mp3", "KIRA AHAHAHAHAAHAHAHAHAHAHA"],
    sound_prefix + "patatina":
    ["kira patatina.ogg", "Prendo una patatina... e me la mangio"],
    sound_prefix + "lelouch eng":
    ["lelouch die.mp3", "Lelouch vi ordina, a tutti voi, di morire. [ENG]"],
    sound_prefix + "lelouch ita":
    ["lelouch morire.ogg", "Lelouch vi ordina, a tutti voi, di morire. [ITA]"],
    sound_prefix + "lelouch jap":
    ["lelouch scine.ogg", "Lelouch vi ordina, a tutti voi, di morire. [JAP]"],
    sound_prefix + "lo sapevo":
    ["lo sapevo.ogg", "KIRA LO SAPEVO LO SAPEVO LO SAPEVO!"],
    sound_prefix + "mendokuse": ["mendokse.mp3", "Shikamaru: Ah... mendokuse"],
    sound_prefix + "nandomo": ["nandomo.mp3", "Sasuke che si incazza"],
    sound_prefix + "nino1": [
        "nino love vacation.mp3",
        "Nino che rompe le palle con \"love vacation\""
    ],
    sound_prefix + "o kawaii koto": ["o kawaii koto.mp3", "Kaguya sama <3"],
    sound_prefix + "osass": ["osass.mp3", "Un bellissimo nome"],
    sound_prefix + "osu": ["osu.mp3", "Welcome to osu!"],
    sound_prefix + "owo": ["OwO.mp3", "OwO sound"],
    sound_prefix + "porco schifo":
    ["porco schifo.mp3", "Porco schifo è uno sballo mi piace"],
    sound_prefix + "quanto a te":
    ["quanto a te.ogg", "Il bellissimo doppiaggio italiano di Evangelion"],
    sound_prefix + "rero": ["rero rero.ogg", "JOJO RERO RERO RERO"],
    sound_prefix + "sium": ["sium.mp3", "SIUUUUUUUM"],
    sound_prefix + "sugoi": ["sugoi.mp3", "Sugoi sugoi di Marin Kitagawa"],
    sound_prefix + "tatakae": ["tatakae.mp3", "Eren tatakae"],
    sound_prefix + "uwu": ["UwU.mp3", "UwU sound"],
    sound_prefix + "vito au": ["vito au.ogg", "Il dolce ululato di vito"],
    sound_prefix + "waku": ["waku waku.mp3", "Anya Waku Waku"],
    sound_prefix + "za warudo": ["za warudo.mp3", "ZA WARUDO DIO BRANDO"]
}


class MyBot(commands.Bot):
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
        self.message_audio_path = "./message_audio/"
        # used for tell who is the sender of a message
        self.last_message_name = ""
        # used to initialize the thread
        self.play_messages_is_run = False

        self.channels_audio = {}

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
            print("\t" + str(e))

    #################
    # system events #
    #################
    async def on_disconnect(self):
        print("on_disconnect:")

    async def on_voice_state_update(self, member, before, after):
        print("on_voice_state_update:")
        name = member.name if str(member.nick) == str(None) else member.nick
        if name in bots_name or name == str(self.user.name):
            return
        if member.name == "ciao986":
            name = "Vito" if random.random() > 0.3 else "Guido"
        if member.name == "Omar97":
            name = name + ', anche chiamato "' + random.choice(
                names_om) + '", '
        if before.channel == None:
            welcome_message = random.choice(welcome_messages)
            if member.name == "Light":
                welcome_message = welcome_message.replace(
                    "_nome_", name + ', anche chiamato "Big Boss", ')
            else:
                welcome_message = welcome_message.replace("_nome_", name)
            await self.save_message(welcome_message, welcome_message, name,
                                    after.channel, True)
            print("\t" + name + " è entrato")
        elif after.channel == None:
            await self.save_message(name + " ha abbandonato il server",
                                    name + " ha abbandonato il server", name,
                                    before.channel, True)
            print("\t" + name + " è uscito")
        elif str(before.channel.name) == str(after.channel.name):
            if after.self_mute != before.self_mute:
                if after.self_mute:
                    await self.save_message(name + " si è mutato",
                                            name + " si è mutato", name,
                                            after.channel, True)
                    print("\t" + name + " si è mutato")
                else:
                    await self.save_message(name + " si è smutato",
                                            name + " si è smutato", name,
                                            after.channel, True)
                    print("\t" + name + " si è smutato")
        else:
            await self.save_message(
                name + " è andato in " + str(after.channel.name),
                name + " è andato in " + str(after.channel.name), name,
                before.channel, True)
            await self.save_message(
                name + " si è unito venendo da " + str(before.channel.name),
                name + " si è unito venendo da " + str(before.channel.name),
                name, after.channel, True)
            print("\t" + name + " è andato da " + str(before.channel.name) +
                  " a " + str(after.channel.name))

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
        if (message.author == self.user
                or message.content == self.command_prefix + "join"
                or message.content[0] in bots_prefix):
            if message.content[0] == sound_prefix:
                if message.content.lower() == "-sounds":
                    maxlen = 0
                    for command in sounds.keys():
                        if maxlen < len(command):
                            maxlen = len(command)
                    helper = "COMMANDS"
                    helper += "    " + " " * (maxlen -
                                              len(helper)) + "DESCRIPTIONS"
                    title = "SOUND COMMANDS"
                    title_offset = "-" * (len(helper) // 2 - len(title) // 2)
                    helper = "```" + title_offset + title + title_offset + "\n" + helper
                    for command, value in sounds.items():
                        spaces = maxlen - len(command)
                        # if tabs == 0:
                        #     tabs = 1
                        helper += "\n" + command + "\t" + " " * spaces + value[
                            1]
                    helper += "```"
                    await ctx.send(helper)
                elif sounds.get(message.content.lower()) != None:
                    sound_name = sounds[message.content.lower()][0]
                    await self.save_sound_board_message(
                        sound_name, message.author.voice.channel)
                else:
                    await ctx.send("Sound not found")
            # elif message.content[0] == other_prefix: #TODO
            return

        print("on_message:")
        print("\tcontenuto messaggeio: ", message.content)

        # if I wrote in chat-bot text channel, save a text to speech file
        if message.channel.name == "chat-bot":
            # last_audio_number = self.generate_idx_message()
            message_to_save1 = str(message.content)
            name_dice = ""
            if "Vito" not in str(name):
                name_dice = str(name)
            else:
                name_dice = str(name) if random.random() > 0.3 else str(
                    name).replace("Vito", "Guido")
            if str(message.author) == "Omar97#3049":
                name_dice = str(name) + ', "' + random.choice(names_om) + '", '
            message_to_save2 = str(name_dice) + " dice: " + message_to_save1
            await self.save_message(message_to_save1, message_to_save2, name,
                                    message.author.voice.channel, False)

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
        except:
            audio_tts = os.listdir(self.message_audio_path)
            for audio in audio_tts:
                os.remove(self.message_audio_path + audio)
        self.play_messages_is_run = False

    async def callback(self, audio_tts):
        # play the text to speech audio
        print("callback:")
        if audio_tts[0].split("_")[1] == "bot":
            audio2play = audio_tts[0]
        elif audio_tts[0].split("_")[4][:-4] == "False":
            if self.last_message_name != audio_tts[0].split("_")[1]:
                self.last_message_name = audio_tts[0].split("_")[1]
                audio2play = audio_tts[0] if audio_tts[0].split("_")[2] == str(
                    True) else audio_tts[1]
            else:
                audio2play = audio_tts[0] if audio_tts[0].split("_")[2] == str(
                    False) else audio_tts[1]
        else:
            audio2play = audio_tts[0]
        if audio_tts[0].split("_")[1] != "bot":
            audio2notPlay = audio_tts[
                0] if audio_tts[0] != audio2play else audio_tts[1]
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
        # remove audio
        os.remove(self.message_audio_path + audio2play)
        if audio_tts[0].split("_")[1] != "bot":
            os.remove(self.message_audio_path + audio2notPlay)

    def generate_idx_message(self):
        audio_tts = os.listdir(self.message_audio_path)
        audio_tts.sort(key=lambda x: int(x.split("_")[0]))
        if os.listdir(self.message_audio_path) == []:
            last_audio_number = -1
        else:
            last_audio_number = int(audio_tts[-1].split("_")[0])
        return last_audio_number

    def save_audio_message(self,
                           message,
                           author_name,
                           channel,
                           number,
                           with_name=False,
                           member_move=False,
                           lang="it"):
        filename = str(number + 1) + "_" + str(author_name) + "_" + str(
            with_name) + "_" + str(channel) + "_" + str(member_move) + ".mp3"
        self.channels_audio[filename] = channel
        tts = gTTS(message, lang=lang)
        tts.save(self.message_audio_path + filename)

    async def save_message(self,
                           message1,
                           message2,
                           name,
                           channel,
                           member_move,
                           lang="it"):
        if self.voice_client is None:
            self.voice_client = await channel.connect()
        last_audio_number = self.generate_idx_message()
        self.save_audio_message(message1,
                                name,
                                channel,
                                last_audio_number,
                                False,
                                member_move,
                                lang=lang)
        self.save_audio_message(message2,
                                name,
                                channel,
                                last_audio_number,
                                True,
                                member_move,
                                lang=lang)
        if not self.play_messages_is_run:
            play_messages_thread = threading.Thread(target=self.play_messages)
            play_messages_thread.start()

    async def save_sound_board_message(self, sound_name, channel):
        if self.voice_client is None:
            self.voice_client = await channel.connect()
        last_audio_number = self.generate_idx_message() + 1
        src_file = "./sound_board/" + sound_name
        dst_folder = "./message_audio/"
        new_file_name = str(last_audio_number) + "_bot_" + sound_name
        self.channels_audio[new_file_name] = channel
        dst_file = os.path.join(dst_folder, new_file_name)
        shutil.copy(src_file, dst_file)
        if not self.play_messages_is_run:
            play_messages_thread = threading.Thread(target=self.play_messages)
            play_messages_thread.start()


keep_alive()
try:
    bot = MyBot(command_prefix="%", self_bot=False)
    bot.run(os.getenv('TOKEN'))
except discord.errors.HTTPException as e:
    if str(e.status) == "429":
        print("\n\n\nBLOCKED BY RATE LIMITS\nRESTARTING NOW\n\n\n")
        system("python restarter.py")
        system('kill 1')
