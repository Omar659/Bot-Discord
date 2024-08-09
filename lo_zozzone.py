import discord
from discord.ext import commands
import shutil
import os
from os import system
import time
from gtts import gTTS
import threading
import asyncio
import random
from utils import print_in_chat

bots_name = ["Neeko", "Lo Zozzone", "inter·punct", "Lara✨", "Lo Zozzone AUDIO"]
sound_prefix = "-"
yt_prefix = ">"
utils_prefix_lo_zozzone = "!"
utils_prefix_la_zozzona = "^"
bots_prefix = [
    utils_prefix_lo_zozzone, sound_prefix, yt_prefix, utils_prefix_la_zozzona
]
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
    "_nome_, benvenuto nel server. Entra e mettiti comodo",
    "Benvenuto _nome_, sei il primo a entrare qui. Benvenuto!",
    "Ah, ecco chi è riapparso... _nome_! Forse il destino ha deciso di concederci la tua presenza di nuovo.",
    "Guarda chi è tornato a turbare la tranquillità... _nome_! Spero tu abbia un buon motivo per esserci.",
    "Ecco il nostro ospite d'onore... _nome_! Spero questa volta tu abbia portato buone notizie con te.",
    "Oh, sembra che il rumore sia tornato nel vuoto... _nome_! Benvenuto, suppongo, se proprio non puoi farne a meno.",
    "Benvenuto, _nome_! Sì, di nuovo. Cercherò di non considerarlo un presagio negativo.",
    "Benvenuto, _nome_! sei tornato a rompere i coglioni... uffa."
]

sounds = {
    sound_prefix + "baka": [["baka.mp3"], "Baka detto in modo carino"],
    sound_prefix + "banishment": [["banishment.ogg"],
                                  "Chuunibyou \"Banishment this warudo\""],
    sound_prefix + "chance boru": [["chance boru.mp3"],
                                   "Dal nostro haycoso... CHANCE BORUUU"],
    sound_prefix + "eliminato": [["eliminato.ogg"],
                                 "Teru Mikami, ELIMINATO ELIMINATOOOOOO"],
    sound_prefix + "eren":
    [["eren.ogg"],
     "Subete no yimiru no taminitsugu... Ore no na wa... Eren Yega"],
    sound_prefix + "erwin tatakae": [["erwin tatakae.ogg"],
                                     "L'urlo della battaglia di erwin"],
    sound_prefix + "kira risata": [["kira laugh.mp3"],
                                   "KIRA AHAHAHAHAAHAHAHAHAHAHA"],
    sound_prefix + "patatina": [["kira patatina.ogg"],
                                "Prendo una patatina... e me la mangio"],
    sound_prefix + "lelouch eng":
    [["lelouch die.mp3"], "Lelouch vi ordina, a tutti voi, di morire. [ENG]"],
    sound_prefix + "lelouch ita":
    [["lelouch morire.ogg"],
     "Lelouch vi ordina, a tutti voi, di morire. [ITA]"],
    sound_prefix + "lelouch jap":
    [["lelouch scine.ogg"],
     "Lelouch vi ordina, a tutti voi, di morire. [JAP]"],
    sound_prefix + "lo sapevo": [["lo sapevo.ogg"],
                                 "KIRA LO SAPEVO LO SAPEVO LO SAPEVO!"],
    sound_prefix + "mendokuse": [["mendokse.mp3"],
                                 "Shikamaru: Ah... mendokuse"],
    sound_prefix + "nandomo": [["nandomo.mp3"], "Sasuke che si incazza"],
    sound_prefix + "nino1": [["nino love vacation.mp3"],
                             "Nino che rompe le palle con \"love vacation\""],
    sound_prefix + "o kawaii koto": [["o kawaii koto.mp3"], "Kaguya sama <3"],
    sound_prefix + "osass": [["osass.mp3"], "Un bellissimo nome"],
    sound_prefix + "osu": [["osu.mp3"], "Welcome to osu!"],
    sound_prefix + "owo": [["OwO.mp3"], "OwO sound"],
    sound_prefix + "porco schifo": [["porco schifo.mp3"],
                                    "Porco schifo è uno sballo mi piace"],
    sound_prefix + "quanto a te":
    [["quanto a te.ogg"], "Il bellissimo doppiaggio italiano di Evangelion"],
    sound_prefix + "rero": [["rero rero.ogg"], "JOJO RERO RERO RERO"],
    sound_prefix + "sium": [["sium.mp3"], "SIUUUUUUUM"],
    sound_prefix + "sugoi": [["sugoi.mp3"], "Sugoi sugoi di Marin Kitagawa"],
    sound_prefix + "tatakae": [["tatakae.mp3"], "Eren tatakae"],
    sound_prefix + "uwu": [["UwU.mp3"], "UwU sound"],
    sound_prefix + "vito au": [["vito au.ogg"], "Il dolce ululato di vito"],
    sound_prefix + "waku": [["waku waku.mp3"], "Anya Waku Waku"],
    sound_prefix + "za warudo": [["za warudo.mp3"], "ZA WARUDO DIO BRANDO"],
    sound_prefix + "civ": [["just civ.ogg"], "Qualcuno ha detto just civ!"],
    sound_prefix + "villager curioso":
    [["villager_curious1.ogg", "villager_curious2.ogg"],
     "Villager incuriosito"],
    sound_prefix + "villager danno": [[
        "villager_damage1.ogg", "villager_damage2.ogg", "villager_damage3.ogg",
        "villager_damage4.ogg", "villager_damage5.ogg"
    ], "Villager che prende danno"],
    sound_prefix + "villager deluso":
    [["villager_disappointing1.ogg", "villager_disappointing2.ogg"],
     "Villager che è deluso"],
    sound_prefix + "villager ok": [["villager_ok1.ogg"],
                                   "Villager che è daccordo"],
    sound_prefix + "villager perplesso":
    [["villager_perplexed1.ogg", "villager_perplexed2.ogg"],
     "Villager che è perplesso"],
    sound_prefix + "villager sorpreso": [["villager_surprise1.ogg"],
                                         "Villager che è sorpreso"],
    sound_prefix + "villager pensieroso": [[
        "villager_think1.ogg", "villager_think2.ogg", "villager_think3.ogg",
        "villager_think4.ogg"
    ], "Villager che è pensieroso"],
    sound_prefix + "villager trade":
    [["villager_trade1.ogg", "villager_trade2.ogg"],
     "Villager che è contento per un trade"],
    sound_prefix + "villager": [[
        'villager_curious1.ogg', 'villager_curious2.ogg',
        'villager_damage1.ogg', 'villager_damage2.ogg', 'villager_damage3.ogg',
        'villager_damage4.ogg', 'villager_damage5.ogg',
        'villager_disappointing1.ogg', 'villager_disappointing2.ogg',
        'villager_normal1.ogg', 'villager_normal2.ogg', 'villager_normal3.ogg',
        'villager_normal4.ogg', 'villager_normal5.ogg', 'villager_ok1.ogg',
        'villager_ok2.ogg', 'villager_perplexed1.ogg',
        'villager_surprise1.ogg', 'villager_trade1.ogg', 'villager_trade2.ogg'
    ], "Suono di villager random"],
    sound_prefix + "i see": [['i_see.ogg'], "I see di Vito"],
    sound_prefix + "pedro": [['pedro pedro.ogg'],
                             "PEDRO PEDRO PEDRO, PEDRO PE"],
    sound_prefix + "vito smash": [['vito_smash.mp3'], "vito che smasha"]
}

bot_welcome_message = '''Benvenuto nell'helper che ti fornisce informazioni sui comandi disponibili per i miei bot. Queste funzionalità sono attive esclusivamente sul canale testuale 'chat-bot'.


Lo Zozzone
Questo bot ti accoglie con messaggi personalizzati e ti informa sui cambiamenti di stato, come attivazioni o disattivazioni del microfono, e sui cambiamenti di stanza. Inoltre, ha una funzione text-to-speech utile per coloro che hanno il microfono disattivato.


Ecco i macro-comandi disponibili:

• self.command_prefixhelp: Visualizza questo messaggio di aiuto.

• sound_prefixsounds: Mostra l'elenco dei suoni disponibili nella soundboard.

• self.command_prefixjoin: Invita il bot a entrare nella tua stanza.

• self.command_prefixclear [opzione] [numero]: Permette di eliminare i messaggi all'interno di chat-bot. L'opzione può essere 'bots' per eliminare solo i messaggi dei bot, 'chats' per eliminare solo i messaggi degli utenti, o nessuna opzione per cancellare entrambi. Il numero indica quanti messaggi cancellare. Se non viene specificato, verranno eliminati tutti i messaggi.


La Zozzona (ATTUALMENTE NON FUNZIONANTE, LEGGENDO SUL GITHUB DI PYTUBE C'È UN BUG NOTO DA FIXARE)
Questo bot permette la riproduzione e la gestione audio dei video da youtube.


Ecco i macro-comandi disponibili:

• yt_prefixplay [-random] link/titolo: riproduce l'audio di video o di una playlist da youtube tramite il link. È possibile riprodurre l'audio del singolo video anche tramite il titolo della canzone. Se impostato l'opzione -random, gli audio verranno riprodotti in modo casuale.

• yt_prefixstop: ferma la riproduzione audio.

• yt_prefixshuffle: esegue uno shuffle sulle canzoni in coda.

• yt_prefixqueue: mostra la coda di riproduzione.

• yt_prefixnow: mostra il titolo della canzone in riproduzione.'''


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

    async def clear_messages(self, ctx, option=None, num=None):
        def is_bot_command(msg):
            name = msg.author.name if str(
                msg.author.nick) == str(None) else msg.author.nick
            return len(
                msg.content
            ) == 0 or msg.content[0] in bots_prefix or name in bots_name

        msg_counter = 0
        async for message in ctx.channel.history(limit=None):
            cond = True
            while cond:
                try:
                    cond = False
                    if is_bot_command(message) and option == "bots":
                        await message.delete()
                        time.sleep(0.25)
                        msg_counter += 1
                    elif not is_bot_command(message) and option == "chats":
                        await message.delete()
                        time.sleep(0.25)
                        msg_counter += 1
                    elif option is None:
                        await message.delete()
                        time.sleep(0.25)
                        msg_counter += 1
                except:
                    cond = True
            if num is not None:
                print(msg_counter, num)
                if msg_counter == num:
                    break

    async def on_voice_state_update(self, member, before, after):
        print("on_voice_state_update:")
        name = member.name if str(member.nick) == str(None) else member.nick
        if name in bots_name or name == str(self.user.name):
            return
        if member.name == "ciao986":
            name = "Vito" if random.random() > 0.3 else "Guido"
        if member.name == "omar97":
            name = name if random.random(
            ) > 0.2 else name + ', anche chiamato "' + random.choice(
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
        channel_pvt = self.get_channel(783465600722665493)
        channel = self.get_channel(1073741331307954207)

        await print_in_chat(bot_welcome_message.replace(
            "self.command_prefix", self.command_prefix).replace(
                "sound_prefix", sound_prefix).replace("yt_prefix", yt_prefix),
                            channel_pvt,
                            monospace=True)
        await print_in_chat(bot_welcome_message.replace(
            "self.command_prefix", self.command_prefix).replace(
                "sound_prefix", sound_prefix).replace("yt_prefix", yt_prefix),
                            channel,
                            monospace=True)

    async def on_message(self, message):
        name = message.author.name if str(
            message.author.nick) == str(None) else message.author.nick
        ctx = await self.get_context(message)
        await self.join(ctx)
        # if is some message from bot
        if name in bots_name:
            return
        if (message.author == self.user or message.content[0] in bots_prefix):
            # Soundboard
            if message.content[0] == sound_prefix:
                if message.content.lower() == sound_prefix + "sounds":
                    maxlen = 0
                    for command in sounds.keys():
                        if maxlen < len(command):
                            maxlen = len(command)
                    helper = "COMMANDS"
                    helper += "    " + " " * (maxlen -
                                              len(helper)) + "DESCRIPTIONS"
                    title = "SOUND COMMANDS"
                    title_offset = "-" * (len(helper) // 2 - len(title) // 2)
                    helper = title_offset + title + title_offset + "\n" + helper
                    for command, value in sounds.items():
                        spaces = maxlen - len(command)
                        # if tabs == 0:
                        #     tabs = 1
                        helper += "\n" + command + "\t" + " " * spaces + value[
                            1]
                    command = "-random"
                    value = "Riproduce un suono random della soundboard"
                    spaces = maxlen - len(command)
                    helper += "\n" + command + "\t" + " " * spaces + value
                    await print_in_chat(helper,
                                        ctx,
                                        monospace=True,
                                        split_character=False)
                elif message.content.lower() == sound_prefix + "random":
                    sound_name = random.choice(sounds[random.choice(
                        list(sounds.keys()))][0])
                    await self.save_sound_board_message(
                        sound_name, message.author.voice.channel)
                elif sounds.get(message.content.lower()) != None:
                    sound_name = random.choice(
                        sounds[message.content.lower()][0])
                    await self.save_sound_board_message(
                        sound_name, message.author.voice.channel)
                else:
                    await print_in_chat("Sound not found", ctx)
            # Utils
            elif message.content[0] == self.command_prefix:
                if message.content.startswith(self.command_prefix + "join"):
                    await self.join(ctx)
                elif message.content.startswith(self.command_prefix + "clear"):
                    info_command = message.content.split(" ")
                    if len(info_command) == 1:
                        await self.clear_messages(ctx)
                    if len(info_command) == 2:
                        if self.check_int(info_command[1]):
                            await self.clear_messages(ctx,
                                                      num=int(info_command[1]))
                        else:
                            if info_command[1].lower() not in [
                                    "chats", "bots"
                            ]:
                                await print_in_chat("Command not found", ctx)
                            else:
                                await self.clear_messages(
                                    ctx, option=info_command[1])
                    if len(info_command) == 3:
                        if (self.check_int(info_command[1])
                                or not self.check_int(info_command[2]) or
                            (not self.check_int(info_command[1])
                             and self.check_int(info_command[2])
                             and info_command[1] not in ["chats", "bots"])):
                            await print_in_chat("Command not found", ctx)
                        else:
                            await self.clear_messages(ctx,
                                                      option=info_command[1],
                                                      num=int(info_command[2]))
                elif message.content.startswith(self.command_prefix + "help"):
                    await print_in_chat(bot_welcome_message.replace(
                        "self.command_prefix", self.command_prefix).replace(
                            "sound_prefix",
                            sound_prefix).replace("yt_prefix", yt_prefix),
                                        ctx,
                                        monospace=True)
            # elif message.content[0] == other_prefix: #TODO
            return

        print("on_message:")
        print("\tcontenuto messaggeio: ", message.content)

        # if I wrote in chat-bot text channel, save a text to speech file
        if message.channel.name == "chat-bot":
            message_to_save1 = str(message.content)
            name_dice = ""
            if "Vito" not in str(name):
                name_dice = str(name)
            else:
                name_dice = str(name) if random.random() > 0.3 else str(
                    name).replace("Vito", "Guido")
            if str(message.author) == "Omar97#3049":
                name_dice = str(name) if random.random() > 0.2 else str(
                    name) + ', "' + random.choice(names_om) + '", '
            message_to_save2 = str(name_dice) + " dice: " + message_to_save1
            await self.save_message(message_to_save1, message_to_save2, name,
                                    message.author.voice.channel, False)

    ###########
    # Utility #
    ###########
    def check_int(self, to_check):
        try:
            int(to_check)
            return True
        except:
            return False

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
        if audio_tts[0].split("_")[1] in ["bot", "yt"]:
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
        if audio_tts[0].split("_")[1] not in ["bot", "yt"]:
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
        if audio_tts[0].split("_")[1] not in ["bot", "yt"]:
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
        filename = str(number + 1).zfill(5) + "_" + str(
            author_name) + "_" + str(with_name) + "_" + str(
                channel) + "_" + str(member_move) + ".mp3"
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
        new_file_name = str(last_audio_number).zfill(5) + "_bot_" + sound_name
        self.channels_audio[new_file_name] = channel
        dst_file = os.path.join(dst_folder, new_file_name)
        shutil.copy(src_file, dst_file)
        if not self.play_messages_is_run:
            play_messages_thread = threading.Thread(target=self.play_messages)
            play_messages_thread.start()


def main():
    try:
        bot = MyBot(command_prefix=utils_prefix_lo_zozzone, self_bot=False)
        bot.run(os.getenv('TOKEN_ZOZZONE'))
    except discord.errors.HTTPException as e:
        if str(e.status) == "429":
            print("\n\n\nBLOCKED BY RATE LIMITS\nRESTARTING NOW\n\n\n")
            system("python restarter.py")
            system('kill 1')
