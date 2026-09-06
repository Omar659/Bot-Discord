import discord
from discord.ext import commands
import shutil
import json
import os
import sys
import time
from gtts import gTTS
import edge_tts
import asyncio
import random
import la_zozzona
from utils import print_in_chat

# tutti i percorsi sono relativi alla cartella dello script, non alla cwd
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_EXTS = (".mp3", ".ogg", ".wav", ".m4a", ".opus", ".webm")
# voci italiane disponibili per il text to speech, scegliibili con !voce
TTS_VOICES = {
    "diego": ("it-IT-DiegoNeural", "voce maschile"),
    "giuseppe": ("it-IT-GiuseppeMultilingualNeural",
                 "voce maschile, legge bene anche le lingue straniere"),
    "elsa": ("it-IT-ElsaNeural", "voce femminile"),
    "isabella": ("it-IT-IsabellaNeural", "voce femminile"),
}
DEFAULT_VOICE = "diego"
# la voce scelta va ricordata tra un riavvio e l'altro
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
# dopo quanti secondi da solo in vocale il bot si sgancia
IDLE_TIMEOUT = 120

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
    "Benvenuto nel server _nome_, entra e lascia un po' della felicità che porti",
    "Un caldo benvenuto a _nome_, nostro raggio di sole che rallegra il nostro server.",
    "Ciao _nome_, sono contento che tu abbia deciso di entrare nel server. Benvenuto!",
    "Si ritorna solo andando via. Sono felice che tu sia di nuovo qui _nome_. Benvenuto nel server.",
    "Che gioia averti tra noi _nome_. Benvenuto!",
    "Un caloroso benvenuto _nome_.",
    "Benvenuto _nome_, regalaci la tua forza vivifica.",
    "Benvenuto _nome_, l'attendevamo con ansia e afa",
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

openings = {
    "ciao986": "vitozzo.ogg"
}

bot_welcome_message = '''Benvenuto nell\'helper che ti fornisce informazioni sui comandi disponibili per i miei bot. Queste funzionalità sono attive esclusivamente sul canale testuale 'chat-bot'.


Lo Zozzone
Questo bot ti accoglie con messaggi personalizzati e ti informa sui cambiamenti di stato, come attivazioni o disattivazioni del microfono, e sui cambiamenti di stanza. Inoltre, ha una funzione text-to-speech utile per coloro che hanno il microfono disattivato.


Ecco i macro-comandi disponibili:

• self.command_prefixhelp: Visualizza questo messaggio di aiuto.

• sound_prefixsounds: Mostra l'elenco dei suoni disponibili nella soundboard.

• self.command_prefixjoin: Invita il bot a entrare nella tua stanza.

• self.command_prefixvoce [nome]: Cambia la voce del text-to-speech. Senza nome mostra le voci disponibili (diego, giuseppe, elsa, isabella) e quella in uso. La scelta resta anche dopo un riavvio.

• self.command_prefixclear [opzione] [numero]: Permette di eliminare i messaggi all\'interno di chat-bot. L\'opzione può essere \'bots\' per eliminare solo i messaggi dei bot, \'chats\' per eliminare solo i messaggi degli utenti, o nessuna opzione per cancellare entrambi. Il numero indica quanti messaggi cancellare. Se non viene specificato, verranno eliminati tutti i messaggi.


La Zozzona
Questo bot permette la riproduzione e la gestione audio dei video da youtube.


Ecco i macro-comandi disponibili:

• yt_prefixplayer: mostra il player con i pulsanti per indietro, pausa, avanti, riascolta, stop, shuffle e la ricerca di video e playlist.

• yt_prefixplay [-random] [-playlist] [-durata minuti] link/titolo: riproduce l\'audio di video o di una playlist da youtube tramite il link. È possibile riprodurre l\'audio del singolo video anche tramite il titolo della canzone. Con l\'opzione -playlist il titolo viene cercato tra le playlist invece che tra i video. Se impostato l\'opzione -random, gli audio verranno riprodotti in modo casuale.

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
        self.message_audio_path = os.path.join(BASE_DIR, "message_audio")
        self.sound_board_path = os.path.join(BASE_DIR, "sound_board")
        self.openings_path = os.path.join(BASE_DIR, "openings")
        # used for tell who is the sender of a message
        self.last_message_name = ""
        # used to initialize the player task
        self.play_messages_is_run = False
        self.player_task = None

        self.channels_audio = {}
        # task che sgancia il bot quando resta solo in vocale
        self.idle_task = None
        # voce del text to speech, ripresa da com'era prima del riavvio
        self.voice_name = self.load_voice()

    ############
    # commands #
    ############
    def humans_in_channel(self):
        # quante persone (bot esclusi) ci sono nel canale del bot
        if self.voice_client is None or not self.voice_client.is_connected():
            return None
        return len([m for m in self.voice_client.channel.members if not m.bot])

    def check_alone(self):
        # avvia o annulla il conto alla rovescia per la disconnessione
        humans = self.humans_in_channel()
        if humans is None or humans > 0:
            if self.idle_task is not None:
                self.idle_task.cancel()
                self.idle_task = None
            return
        if self.idle_task is None or self.idle_task.done():
            self.idle_task = self.loop.create_task(self.leave_when_alone())

    async def leave_when_alone(self):
        try:
            await asyncio.sleep(IDLE_TIMEOUT)
            if self.humans_in_channel() == 0:
                print("Canale vuoto: mi disconnetto dalla voce.")
                await self.voice_client.disconnect()
                self.voice_client = None
                self.clean_audio_folder()
        except asyncio.CancelledError:
            pass
        finally:
            self.idle_task = None

    async def ensure_voice(self, channel):
        # connette il bot al canale voce richiesto riusando la connessione
        # esistente (channel.connect() su un client già connesso solleva
        # ClientException, quindi va usato move_to)
        if channel is None:
            return None
        voice_client = channel.guild.voice_client
        # una connessione rimasta a metà va chiusa, altrimenti connect()
        # solleva "Already connected to a voice channel"
        if voice_client is not None and not voice_client.is_connected():
            try:
                await voice_client.disconnect(force=True)
            except Exception as e:
                print("\tErrore chiudendo la voce:", e)
            voice_client = None
        if voice_client is None:
            voice_client = await channel.connect()
        elif voice_client.channel != channel:
            await voice_client.move_to(channel)
        self.voice_client = voice_client
        return voice_client

    async def join(self, ctx):
        # join command
        print("!join:")
        try:
            channel = ctx.author.voice.channel
            await self.ensure_voice(channel)
            print("\tJoin command executed with success.")
        except AttributeError:
            print(
                "\tError! You are not connected to the channel available to me."
            )
        except Exception as e:
            print("Exception in join:")
            print("\t" + str(e))

    #################
    # system events #
    #################
    async def on_disconnect(self):
        self.clean_audio_folder()
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
            deleted = False
            while not deleted:
                try:
                    if is_bot_command(message) and option == "bots":
                        await message.delete()
                        await asyncio.sleep(0.25)  # FIX: non blocca l'event loop
                        msg_counter += 1
                        deleted = True
                    elif not is_bot_command(message) and option == "chats":
                        await message.delete()
                        await asyncio.sleep(0.25)
                        msg_counter += 1
                        deleted = True
                    elif option is None:
                        await message.delete()
                        await asyncio.sleep(0.25)
                        msg_counter += 1
                        deleted = True
                    else:
                        deleted = True  # non corrisponde al filtro, skippa
                except Exception:
                    await asyncio.sleep(0.25)  # retry in caso di rate limit
            if num is not None:
                if msg_counter >= num:
                    break

    async def on_voice_state_update(self, member, before, after):
        print("on_voice_state_update:")
        # va controllato anche per i movimenti dei bot, prima di uscire
        self.check_alone()
        name = self.display_name_of(member)
        if name in bots_name or name == str(self.user.name):
            return
        if member.name == "ciao986":
            name = "Vito" if random.random() > 0.3 else "Guido"
        if member.name == "omar97":
            name = name if random.random(
            ) > 0.2 else name + ', anche chiamato "' + random.choice(
                names_om) + '", '
        if before.channel is None:  # FIX: usare 'is None' invece di '== None'
            welcome_message = random.choice(welcome_messages)
            if member.name == "Light":
                welcome_message = welcome_message.replace(
                    "_nome_", name + ', anche chiamato "Big Boss", ')
            else:
                welcome_message = welcome_message.replace("_nome_", name)
            if member.name == "ciao986":
                if openings.get("ciao986") is not None:
                    sound_name = openings["ciao986"]
                    await self.save_opening_message(
                        sound_name, member.voice.channel)
            await self.save_message(welcome_message, welcome_message, name,
                                    after.channel, True)
            print("\t" + name + " è entrato")
        elif after.channel is None:  # FIX: usare 'is None' invece di '== None'
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
        self.clean_audio_folder()
        print('\tWe have logged in as {0.user}'.format(self))

        helper = self.build_help_message()
        for channel_id in (783465600722665493, 1073741331307954207):
            channel = self.get_channel(channel_id)
            # il bot potrebbe non avere più accesso al canale
            if channel is None:
                print(f"\tCanale {channel_id} non trovato, messaggio saltato.")
                continue
            try:
                await print_in_chat(helper, channel, monospace=True)
            except Exception as e:
                print(f"\tImpossibile scrivere nel canale {channel_id}: {e}")

    async def on_message(self, message):
        # guard su messaggi vuoti per evitare IndexError
        if not message.content:
            return

        name = self.display_name_of(message.author)

        # skip messaggi di bot PRIMA di fare qualsiasi altra cosa
        if name in bots_name or message.author == self.user or message.author.bot:
            return

        ctx = await self.get_context(message)

        if message.content[0] in bots_prefix:
            # entra nel canale voce dell'autore solo se serve
            await self.join(ctx)

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
                    await self.play_sound_command(ctx, sound_name)
                elif sounds.get(message.content.lower()) is not None:
                    sound_name = random.choice(
                        sounds[message.content.lower()][0])
                    await self.play_sound_command(ctx, sound_name)
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
                elif message.content.startswith(self.command_prefix + "voce"):
                    await self.change_voice(ctx, message.content)
                elif message.content.startswith(self.command_prefix + "help"):
                    await print_in_chat(self.build_help_message(),
                                        ctx,
                                        monospace=True)
            return

        print("on_message:")
        print("\tcontenuto messaggio: ", message.content)

        # if I wrote in chat-bot text channel, save a text to speech file
        if getattr(message.channel, "name", None) == "chat-bot":
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
            # FIX: guard nel caso l'utente non sia in un canale voice
            if message.author.voice and message.author.voice.channel:
                await self.save_message(message_to_save1, message_to_save2,
                                        name, message.author.voice.channel,
                                        False)

    ###########
    # Utility #
    ###########
    def check_int(self, to_check):
        try:
            int(to_check)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def display_name_of(user):
        # gli oggetti User (DM) non hanno l'attributo nick
        nick = getattr(user, "nick", None)
        return user.name if nick is None else nick

    def build_help_message(self):
        return bot_welcome_message.replace(
            "self.command_prefix",
            self.command_prefix).replace("sound_prefix", sound_prefix).replace(
                "yt_prefix", yt_prefix)

    def list_audio(self):
        # solo i file audio completi, in ordine di indice
        return sorted(f for f in os.listdir(self.message_audio_path)
                      if f.lower().endswith(AUDIO_EXTS))

    def remove_audio(self, filename):
        if not filename:
            return
        try:
            os.remove(os.path.join(self.message_audio_path, filename))
        except OSError:
            pass
        self.channels_audio.pop(filename, None)

    def clean_audio_folder(self):
        for audio in os.listdir(self.message_audio_path):
            self.remove_audio(audio)
        self.channels_audio.clear()

    def ensure_player(self):
        # il player gira come task sull'event loop del bot: usare un loop
        # separato in un thread rompe il voice client (è legato al loop del bot)
        if self.player_task is None or self.player_task.done():
            self.player_task = self.loop.create_task(self.play_messages())

    async def play_messages(self):
        self.play_messages_is_run = True
        try:
            # repeat until the message audio folder is empty
            while True:
                audio_tts = self.list_audio()
                if not audio_tts:
                    break
                try:
                    await self.callback(audio_tts)
                except Exception as e:
                    print("Errore nella riproduzione:", e)
                    self.clean_audio_folder()
                    break
                await asyncio.sleep(0.5)
        finally:
            self.play_messages_is_run = False

    def select_audio(self, audio_tts):
        # per ogni messaggio vengono generati due audio (con e senza il nome
        # dell'autore): qui si sceglie quale riprodurre e quale scartare
        parts = os.path.splitext(audio_tts[0])[0].split("_")
        if len(parts) < 5 or parts[1] in ["bot", "yt"]:
            return audio_tts[0], None

        # i due file della stessa coppia condividono l'indice iniziale
        pair = audio_tts[1] if len(audio_tts) > 1 and audio_tts[1].split(
            "_")[0] == parts[0] else None
        if pair is None:
            return audio_tts[0], None
        if parts[-1] != "False":
            # messaggi di stato: i due audio sono identici, ne basta uno
            return audio_tts[0], pair

        if self.last_message_name != parts[1]:
            self.last_message_name = parts[1]
            want_name = str(True)
        else:
            want_name = str(False)
        audio2play = audio_tts[0] if parts[2] == want_name else audio_tts[1]
        audio2notPlay = audio_tts[1] if audio2play == audio_tts[0] else audio_tts[0]
        return audio2play, audio2notPlay

    async def music_control(self, duck):
        # i due bot trasmettono insieme nello stesso canale: la musica non si
        # ferma, si abbassa per il tempo del messaggio. Girano in thread con
        # event loop diversi, quindi la chiamata va schedulata sull'altro loop.
        music_bot = la_zozzona.CURRENT_BOT
        if music_bot is None or music_bot.voice_client is None:
            return
        try:
            coro = (music_bot.duck_for_speech()
                    if duck else music_bot.unduck_after_speech())
            future = asyncio.run_coroutine_threadsafe(coro, music_bot.loop)
            await asyncio.wrap_future(future)
        except Exception as e:
            print("\tControllo musica non riuscito:", e)

    async def play_source(self, audio_source):
        # attende la fine della riproduzione senza bloccare l'event loop
        finished = asyncio.Event()
        loop = self.loop

        def after_playing(error):
            if error:
                print("\tErrore player:", error)
            loop.call_soon_threadsafe(finished.set)

        if self.voice_client.is_playing():
            self.voice_client.stop()
        start = time.monotonic()
        self.voice_client.play(audio_source, after=after_playing)
        await finished.wait()
        # una durata di pochi decimi indica che ffmpeg è morto subito
        print("\tRiproduzione finita dopo %.1fs" % (time.monotonic() - start))

    async def callback(self, audio_tts):
        # play the text to speech audio
        print("callback:")
        audio2play, audio2notPlay = self.select_audio(audio_tts)
        path = os.path.join(self.message_audio_path, audio2play)

        # il canale può mancare se il file è rimasto da un'esecuzione precedente
        channel = self.channels_audio.get(audio2play)
        if channel is not None:
            await self.ensure_voice(channel)
        if self.voice_client is None or not self.voice_client.is_connected():
            print("\tNessun canale voce disponibile, audio scartato.")
            self.remove_audio(audio2play)
            self.remove_audio(audio2notPlay)
            return

        # stderr esplicito: senza, gli errori di ffmpeg finiscono nel nulla
        audio_source = await discord.FFmpegOpusAudio.from_probe(
            path,
            before_options='-nostdin',
            options='-filter:a loudnorm',
            stderr=sys.stderr)
        # la musica continua a suonare, solo più bassa, per il tempo del messaggio
        await self.music_control(duck=True)
        try:
            await self.play_source(audio_source)
        finally:
            await self.music_control(duck=False)
            self.remove_audio(audio2play)
            self.remove_audio(audio2notPlay)

    def generate_idx_message(self):
        audio_tts = [
            f for f in self.list_audio() if self.check_int(f.split("_")[0])
        ]
        if not audio_tts:
            return -1
        return max(int(f.split("_")[0]) for f in audio_tts)

    async def save_audio_message(self,
                                 message,
                                 author_name,
                                 channel,
                                 number,
                                 with_name=False,
                                 member_move=False,
                                 lang="it"):
        safe_name = self.safe_field(author_name)
        safe_channel = self.safe_field(channel)
        filename = str(number + 1).zfill(5) + "_" + safe_name + "_" + str(
            with_name) + "_" + safe_channel + "_" + str(member_move) + ".mp3"
        path = os.path.join(self.message_audio_path, filename)

        # senza lettere né cifre non c'è niente da pronunciare: i motori TTS
        # restituiscono un errore o un file vuoto
        if not any(c.isalnum() for c in message):
            print("\tMessaggio senza testo pronunciabile, saltato.")
            return False

        ok = False
        try:
            voice = TTS_VOICES.get(self.voice_name,
                                   TTS_VOICES[DEFAULT_VOICE])[0]
            await edge_tts.Communicate(message, voice).save(path)
            # a volte edge-tts scrive comunque un file da 0 byte, che
            # manderebbe ffmpeg in errore
            ok = os.path.isfile(path) and os.path.getsize(path) > 0
        except Exception as e:
            print("\tedge-tts non disponibile (%s), uso gTTS" % e)

        if not ok:
            # gTTS come rete di sicurezza: voce peggiore ma sempre disponibile
            try:
                await asyncio.to_thread(self.save_with_gtts, message, path,
                                        lang)
                ok = os.path.isfile(path) and os.path.getsize(path) > 0
            except Exception as e:
                print("\tAnche gTTS ha fallito:", e)

        if not ok:
            # meglio nessun file che un file rotto in coda
            try:
                os.remove(path)
            except OSError:
                pass
            return False
        self.channels_audio[filename] = channel
        return True

    @staticmethod
    def safe_field(value):
        # "_" separa i campi nel nome file, mentre \\ / : * ? " < > | non sono
        # ammessi da Windows: i soprannomi tipo 'omar97, anche chiamato "Il
        # principe oscuro",' facevano fallire il salvataggio dell'audio
        cleaned = str(value)
        for char in '\\/:*?"<>|_\n\r\t':
            cleaned = cleaned.replace(char, "-")
        return cleaned.strip()[:60] or "utente"

    @staticmethod
    def save_with_gtts(message, path, lang):
        gTTS(message, lang=lang).save(path)

    #########
    # voci  #
    #########
    @staticmethod
    def load_voice():
        # se il file manca o è illeggibile si riparte dalla voce predefinita
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as settings_file:
                voice = json.load(settings_file).get("tts_voice")
            if voice in TTS_VOICES:
                return voice
        except Exception:
            pass
        return DEFAULT_VOICE

    def save_voice(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as settings_file:
                json.dump({"tts_voice": self.voice_name},
                          settings_file,
                          indent=2)
        except Exception as e:
            print("\tImpossibile salvare la voce scelta:", e)

    def voices_list(self):
        righe = []
        for name, (_, descrizione) in TTS_VOICES.items():
            attuale = " <- in uso" if name == self.voice_name else ""
            righe.append("  " + name.ljust(9) + descrizione + attuale)
        return "\n".join(righe)

    async def change_voice(self, ctx, content):
        parts = content.split(" ", 1)
        scelta = parts[1].strip().lower() if len(parts) > 1 else ""
        if not scelta:
            await print_in_chat("Voci disponibili:\n" + self.voices_list() +
                                "\n\nPer cambiarla: " + self.command_prefix +
                                "voce <nome>",
                                ctx,
                                monospace=True,
                                split_character=False)
            return
        if scelta not in TTS_VOICES:
            await print_in_chat("Voce \"" + scelta +
                                "\" non trovata. Voci disponibili:\n" +
                                self.voices_list(),
                                ctx,
                                monospace=True,
                                split_character=False)
            return
        self.voice_name = scelta
        self.save_voice()
        print("Voce cambiata in " + scelta + " (" + TTS_VOICES[scelta][0] + ")")
        await print_in_chat("Ok, da adesso parlo con la voce di " +
                            scelta.capitalize(), ctx)

    async def save_message(self,
                           message1,
                           message2,
                           name,
                           channel,
                           member_move,
                           lang="it"):
        await self.ensure_voice(channel)
        last_audio_number = self.generate_idx_message()
        await self.save_audio_message(message1, name, channel,
                                      last_audio_number, False, member_move,
                                      lang)
        await self.save_audio_message(message2, name, channel,
                                      last_audio_number, True, member_move,
                                      lang)
        self.ensure_player()

    async def copy_audio_to_queue(self, src_file, sound_name, channel):
        await self.ensure_voice(channel)
        last_audio_number = self.generate_idx_message() + 1
        new_file_name = str(last_audio_number).zfill(5) + "_bot_" + sound_name
        dst_file = os.path.join(self.message_audio_path, new_file_name)
        shutil.copy(src_file, dst_file)
        self.channels_audio[new_file_name] = channel
        self.ensure_player()

    async def play_sound_command(self, ctx, sound_name):
        # il comando ha senso solo se chi scrive è in un canale voce
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await print_in_chat("Devi essere in un canale vocale", ctx)
            return
        await self.save_sound_board_message(sound_name,
                                            ctx.author.voice.channel)

    async def save_sound_board_message(self, sound_name, channel):
        await self.copy_audio_to_queue(
            os.path.join(self.sound_board_path, sound_name), sound_name,
            channel)

    async def save_opening_message(self, sound_name, channel):
        await self.copy_audio_to_queue(
            os.path.join(self.openings_path, sound_name), sound_name, channel)


def main(token):
    bot = MyBot(command_prefix=utils_prefix_lo_zozzone, self_bot=False)
    try:
        # log_handler=None: il logging è configurato una sola volta in main.py,
        # altrimenti ogni bot aggiunge un handler e i log escono duplicati
        bot.run(token, log_handler=None)
    except discord.errors.HTTPException as e:
        if str(e.status) == "429":
            print("\n\n\nBLOCKED BY RATE LIMITS\nRESTARTING NOW\n\n\n")
            os.system("python restarter.py")
    except Exception as e:
        print("Lo Zozzone si è fermato:", e)
