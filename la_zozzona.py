import discord
from discord.ext import commands
import os
import subprocess
import sys
import time
from youtube_downloader import YouTubeDownloader
import asyncio
from threading import Thread
import random
from utils import print_in_chat

# tutti i percorsi sono relativi alla cartella dello script, non alla cwd
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_EXTS = (".mp3", ".ogg", ".wav", ".m4a", ".opus")
# quanti brani già ascoltati tenere da parte per il tasto "indietro"
HISTORY_SIZE = 20
# ogni quanti secondi ridisegnare la barra di avanzamento: modificare un
# messaggio troppo spesso fa scattare i rate limit di Discord
PROGRESS_REFRESH = 5
BAR_LENGTH = 20

# istanza attiva del bot musicale: serve a Lo Zozzone per abbassare la musica
# mentre parla, così le due tracce si sentono insieme senza coprirsi
CURRENT_BOT = None
# volume della musica mentre Lo Zozzone parla (1.0 = nessun abbassamento).
# Con 1.0 la musica viene riprodotta in copia diretta, senza ricodifica:
# più leggero per la CPU, ma il volume non è più regolabile al volo.
DUCK_VOLUME = 0.25
# dopo quanti secondi da solo in vocale il bot si sgancia
IDLE_TIMEOUT = 120

bots_name = ["Neeko", "Lo Zozzone", "inter·punct", "Lara✨", "Lo Zozzone AUDIO"]
sound_prefix = "-"
yt_prefix = ">"
utils_prefix_lo_zozzone = "!"
utils_prefix_la_zozzona = "^"
bots_prefix = [
    utils_prefix_lo_zozzone, utils_prefix_la_zozzona, yt_prefix, sound_prefix
]

youtube_help_message = '''Comandi per la riproduzione audio da YouTube.

• yt_prefixyoutube: visualizza questo messaggio di aiuto.

• yt_prefixplayer: mostra il player con i pulsanti per indietro, pausa, avanti, riascolta, stop, shuffle e la ricerca di video e playlist.

• yt_prefixplay [-random] [-playlist] link/titolo: riproduce l'audio di un video o di una playlist di youtube tramite il link. È possibile riprodurre l'audio del singolo video anche tramite il titolo della canzone. Con l'opzione -playlist il titolo viene cercato tra le playlist invece che tra i video. Se impostata l'opzione -random, gli audio verranno riprodotti in modo casuale.

• yt_prefixstop: ferma la riproduzione audio e svuota la coda.

• yt_prefixshuffle: esegue uno shuffle sulle canzoni in coda, lasciando al suo posto quella in riproduzione.

• yt_prefixqueue: mostra la coda di riproduzione.

• yt_prefixnow: mostra il titolo della canzone in riproduzione.'''.replace(
    "yt_prefix", yt_prefix)


class SearchModal(discord.ui.Modal):
    # finestra di ricerca: una per i video, una per le playlist
    def __init__(self, bot, search_playlist):
        super().__init__(title="Cerca una playlist"
                         if search_playlist else "Cerca un video")
        self.bot = bot
        self.search_playlist = search_playlist
        # in discord.py 2.7 l'etichetta è un componente a sé (Label)
        self.query = discord.ui.TextInput(
            placeholder="lofi hip hop     oppure     https://youtu.be/...",
            max_length=300)
        self.random_queue = discord.ui.TextInput(default="no",
                                                 required=False,
                                                 max_length=3)
        self.add_item(
            discord.ui.Label(text="Titolo o link", component=self.query))
        self.add_item(
            discord.ui.Label(text="Ordine casuale (si/no)",
                             component=self.random_queue))

    async def on_submit(self, interaction):
        channel = interaction.user.voice.channel if interaction.user.voice else None
        if channel is None:
            await interaction.response.send_message(
                "Devi essere in un canale vocale", ephemeral=True)
            return
        # il download può durare parecchio: la risposta va rimandata
        await interaction.response.defer()
        random_queue = self.random_queue.value.strip().lower() in ("si", "sì",
                                                                  "yes", "y",
                                                                  "1")
        self.bot.stop_yt["flag_yt"] = False
        try:
            await self.bot.save_youtube_music(self.query.value, channel,
                                              random_queue,
                                              self.search_playlist)
        except Exception as e:
            print("Ricerca dal player fallita:", e)
            await interaction.followup.send("Non ho trovato niente",
                                            ephemeral=True)
        await self.bot.refresh_player()


class PlayerView(discord.ui.View):
    # i custom_id rendono i bottoni persistenti: continuano a funzionare
    # anche dopo il riavvio del bot (vedi add_view in on_ready)
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def act(self, interaction, action):
        await interaction.response.defer()
        await action()
        await self.bot.refresh_player()

    @discord.ui.button(emoji="⏮", label="Indietro", custom_id="zozzona:prev")
    async def previous(self, interaction, button):
        await self.act(interaction, self.bot.previous_track)

    @discord.ui.button(emoji="⏯", label="Pausa", custom_id="zozzona:pause")
    async def pause(self, interaction, button):
        await self.act(interaction, self.bot.toggle_pause)

    @discord.ui.button(emoji="⏭", label="Avanti", custom_id="zozzona:skip")
    async def skip(self, interaction, button):
        await self.act(interaction, self.bot.skip_current)

    @discord.ui.button(emoji="🔁", label="Riascolta", custom_id="zozzona:replay")
    async def replay(self, interaction, button):
        await self.act(interaction, self.bot.replay_current)

    @discord.ui.button(emoji="⏹",
                       label="Stop",
                       style=discord.ButtonStyle.danger,
                       custom_id="zozzona:stop")
    async def stop_playback(self, interaction, button):
        await self.act(interaction, self.bot.stop_playback)

    @discord.ui.button(emoji="🔀",
                       label="Shuffle",
                       row=1,
                       custom_id="zozzona:shuffle")
    async def shuffle(self, interaction, button):
        await self.act(interaction, self.bot.shuffle_queue)

    @discord.ui.button(emoji="🔄",
                       label="Aggiorna",
                       row=1,
                       custom_id="zozzona:refresh")
    async def refresh(self, interaction, button):
        await self.act(interaction, self.bot.noop)

    @discord.ui.button(emoji="🔎",
                       label="Cerca video",
                       row=1,
                       style=discord.ButtonStyle.primary,
                       custom_id="zozzona:search_video")
    async def search_video(self, interaction, button):
        await interaction.response.send_modal(SearchModal(self.bot, False))

    @discord.ui.button(emoji="🎧",
                       label="Cerca playlist",
                       row=1,
                       style=discord.ButtonStyle.primary,
                       custom_id="zozzona:search_playlist")
    async def search_playlist(self, interaction, button):
        await interaction.response.send_modal(SearchModal(self.bot, True))


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
        self.message_audio_path = os.path.join(BASE_DIR, "youtube_musics")
        # used to initialize the player task
        self.play_messages_is_run = False
        self.player_task = None

        self.stop_yt = {"flag_yt": False}
        self.channels_audio = {}
        self.youtube_downloader = YouTubeDownloader(self.message_audio_path,
                                                    self.generate_idx_message)
        # messaggio con l'embed del player, tenuto aggiornato a ogni cambio
        self.player_message = None
        self.player_view_added = False
        # thread di download in corso: la coda può essere vuota solo perché
        # il brano successivo non è ancora stato scaricato
        self.download_thread = None
        # i brani già ascoltati vengono archiviati qui invece di essere
        # cancellati, così il tasto "indietro" ha qualcosa a cui tornare
        self.history_path = os.path.join(self.message_audio_path, "history")
        os.makedirs(self.history_path, exist_ok=True)
        self.history_counter = 0
        # se True il brano corrente non viene archiviato: resta in coda e
        # riparte da capo (usato da "riascolta" e "indietro")
        self.replay_flag = False
        # stato per la barra di avanzamento: la posizione si conta a mano
        # perché discord.py non espone quanto ha già suonato
        self.track_duration = None
        self.track_started = None
        self.track_paused_at = None
        self.track_paused_total = 0.0
        self.progress_task = None
        # sorgente audio in riproduzione, per poterne regolare il volume
        self.current_source = None
        # True mentre Lo Zozzone sta parlando e la musica è abbassata
        self.ducked = False
        # task che sgancia il bot quando resta solo in vocale
        self.idle_task = None

    ############
    # commands #
    ############
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

    async def on_ready(self):
        # when the bot is ready remove old messages
        print("on_ready:")
        self.clean_audio_folder()
        # i bottoni dei pannelli inviati prima del riavvio restano attivi
        # (on_ready può scattare più volte: la view va registrata una sola)
        if not self.player_view_added:
            self.add_view(PlayerView(self))
            self.player_view_added = True
        print('\tWe have logged in as {0.user}'.format(self))

    async def on_voice_state_update(self, member, before, after):
        # unico scopo: accorgersi che il canale è rimasto vuoto
        self.check_alone()

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
                print("Canale vuoto: fermo la musica e mi disconnetto.")
                await self.stop_playback()
                await self.voice_client.disconnect()
                self.voice_client = None
                await self.refresh_player()
        except asyncio.CancelledError:
            pass
        finally:
            self.idle_task = None

    async def on_message(self, message):
        # guard su messaggi vuoti per evitare IndexError
        if not message.content:
            return

        nick = getattr(message.author, "nick", None)
        name = message.author.name if nick is None else nick

        # skip messaggi di bot PRIMA di fare qualsiasi altra cosa
        if name in bots_name or message.author == self.user or message.author.bot:
            return

        ctx = await self.get_context(message)

        if message.content[0] in bots_prefix:
            # entra nel canale voce dell'autore solo se serve
            await self.join(ctx)

            # Youtube
            if message.content[0] == yt_prefix:
                if message.content.lower().startswith(yt_prefix + "player"):
                    await self.send_player(message.channel)
                elif message.content.lower().startswith(yt_prefix + "youtube"):
                    await print_in_chat(youtube_help_message,
                                        ctx,
                                        monospace=True,
                                        split_character=False)
                elif message.content.lower().startswith(yt_prefix + "play"):
                    if ctx.author.voice is None or ctx.author.voice.channel is None:
                        await print_in_chat("Devi essere in un canale vocale",
                                            ctx)
                        return
                    self.stop_yt["flag_yt"] = False
                    args = message.content[len(yt_prefix + "play"):].strip()
                    # le opzioni possono essere in qualunque ordine
                    random_queue = False
                    search_playlist = False
                    while args.startswith("-"):
                        flag, _, rest = args.partition(" ")
                        if flag.lower() == "-random":
                            random_queue = True
                        elif flag.lower() == "-playlist":
                            search_playlist = True
                        else:
                            break
                        args = rest.strip()
                    if not args:
                        await print_in_chat(
                            "Serve un link o il titolo di un video", ctx)
                        return
                    try:
                        await self.save_youtube_music(args,
                                                      ctx.author.voice.channel,
                                                      random_queue,
                                                      search_playlist)
                    except Exception as e:
                        print(e)
                        await print_in_chat("Youtube video not found", ctx)
                    # al primo play il pannello compare da solo
                    if self.player_message is None:
                        await self.send_player(message.channel)
                    else:
                        await self.refresh_player()
                elif message.content.lower().startswith(yt_prefix + "now"):
                    yt_musics = self.list_yt_music()
                    if not yt_musics:
                        await print_in_chat("Nessuna canzone in riproduzione", ctx)
                    else:
                        current = self.music_title(yt_musics[0])
                        await print_in_chat("Attualmente in esecuzione: " + current, ctx)
                elif message.content.lower().startswith(yt_prefix + "shuffle"):
                    if await self.shuffle_queue():
                        await print_in_chat("Shuffle eseguito", ctx)
                    else:
                        await print_in_chat("Errore nella shuffle, riprova", ctx)
                    await self.refresh_player()
                elif message.content.lower().startswith(yt_prefix + "queue"):
                    yt_musics = self.list_yt_music()
                    if not yt_musics:
                        await print_in_chat("La coda è vuota", ctx)
                    else:
                        yt_musics_display = [
                            self.music_title(x) for x in yt_musics
                        ]
                        queue_str = "\n".join([
                            "\t" + str(i + 1).zfill(len(str(len(yt_musics_display)))) +
                            ") " + x + (" <- IN ESECUZIONE" if i == 0 else "")
                            for i, x in enumerate(yt_musics_display)
                        ])
                        await print_in_chat("Queue:\n" + queue_str, ctx, monospace=True, split_character=False)
                elif message.content.lower().startswith(yt_prefix + "stop"):
                    await self.stop_playback()
                    await print_in_chat("Musica da youtube stoppata", ctx)
                    await self.refresh_player()
            # elif message.content[0] == other_prefix: #TODO
            return

    ###########
    # Utility #
    ###########
    def list_yt_music(self):
        # solo i file già scaricati e convertiti, in ordine di coda
        return sorted(f for f in os.listdir(self.message_audio_path)
                      if "_yt_" in f and f.lower().endswith(AUDIO_EXTS))

    @staticmethod
    def music_title(filename):
        # i nomi sono nella forma 00001_yt_Titolo.mp3
        return os.path.splitext(filename)[0].split("_yt_", 1)[-1]

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
        for audio in self.history_files():
            try:
                os.remove(os.path.join(self.history_path, audio))
            except OSError:
                pass
        self.history_counter = 0
        self.channels_audio.clear()

    ##############
    # cronologia #
    ##############
    def history_files(self):
        # ordinati dal più vecchio al più recente (il prefisso è un contatore)
        if not os.path.isdir(self.history_path):
            return []
        return sorted(f for f in os.listdir(self.history_path)
                      if f.lower().endswith(AUDIO_EXTS))

    def archive_audio(self, filename):
        # il brano ascoltato passa in cronologia invece di sparire
        self.history_counter += 1
        hist_name = str(self.history_counter).zfill(5) + "_" + filename
        try:
            os.rename(os.path.join(self.message_audio_path, filename),
                      os.path.join(self.history_path, hist_name))
        except OSError as e:
            print("\tArchiviazione fallita:", e)
            self.remove_audio(filename)
            return
        channel = self.channels_audio.pop(filename, None)
        if channel is not None:
            self.channels_audio[hist_name] = channel
        # la cronologia non deve crescere all'infinito
        history = self.history_files()
        for old in history[:-HISTORY_SIZE]:
            try:
                os.remove(os.path.join(self.history_path, old))
            except OSError:
                pass
            self.channels_audio.pop(old, None)

    def shift_queue_forward(self):
        # libera il numero 0 in testa alla coda spostando tutto avanti di uno
        for name in reversed(self.list_yt_music()):
            new_name = str(int(name.split("_")[0]) +
                           1).zfill(5) + "_" + name.split("_", 1)[1]
            os.rename(os.path.join(self.message_audio_path, name),
                      os.path.join(self.message_audio_path, new_name))
            channel = self.channels_audio.pop(name, None)
            if channel is not None:
                self.channels_audio[new_name] = channel

    def restore_previous(self):
        # riporta in testa alla coda l'ultimo brano ascoltato
        history = self.history_files()
        if not history:
            return False
        last = history[-1]
        queue = self.list_yt_music()
        head = int(queue[0].split("_")[0]) if queue else 1
        if head <= 0:
            self.shift_queue_forward()
            head = int(self.list_yt_music()[0].split("_")[0])
        # dal nome in cronologia si tolgono contatore e vecchio indice
        original = last.split("_", 1)[1]
        new_name = str(head - 1).zfill(5) + "_" + original.split("_", 1)[1]
        os.rename(os.path.join(self.history_path, last),
                  os.path.join(self.message_audio_path, new_name))
        channel = self.channels_audio.pop(last, None)
        if channel is not None:
            self.channels_audio[new_name] = channel
        return True

    async def shuffle_queue(self):
        # la prima traccia è quella in riproduzione: resta al suo posto
        try:
            yt_musics = self.list_yt_music()[1:]
            if len(yt_musics) < 2:
                return True
            numbers = sorted(int(x.split("_")[0]) for x in yt_musics)
            shuffled = yt_musics[:]
            random.shuffle(shuffled)

            def rename(old_name, new_name):
                if new_name == old_name:
                    return
                os.rename(os.path.join(self.message_audio_path, old_name),
                          os.path.join(self.message_audio_path, new_name))
                # il canale associato segue il file rinominato
                channel = self.channels_audio.pop(old_name, None)
                if channel is not None:
                    self.channels_audio[new_name] = channel

            # rinomina in due passaggi per non sovrascrivere file omonimi
            tmp_names = []
            for i, old_name in enumerate(shuffled):
                tmp_name = "tmpshuffle" + str(i) + old_name
                rename(old_name, tmp_name)
                tmp_names.append(tmp_name)
            for number, tmp_name, old_name in zip(numbers, tmp_names, shuffled):
                rename(tmp_name,
                       str(number).zfill(5) + "_" + old_name.split("_", 1)[1])
            return True
        except Exception as e:
            print(f"Shuffle error: {e}")
            return False

    ##########
    # player #
    ##########
    async def noop(self):
        # usato dal bottone "Aggiorna": ridisegna solo l'embed
        pass

    async def toggle_pause(self):
        if self.voice_client is None:
            return
        if self.voice_client.is_paused():
            self.voice_client.resume()
            # il tempo passato in pausa non conta nell'avanzamento
            if self.track_paused_at is not None:
                self.track_paused_total += time.monotonic() - self.track_paused_at
                self.track_paused_at = None
        elif self.voice_client.is_playing():
            self.voice_client.pause()
            self.track_paused_at = time.monotonic()

    def set_music_volume(self, volume):
        # funziona solo sulle sorgenti con volume regolabile: se la musica
        # è riprodotta in copia diretta non c'è niente da regolare
        if self.current_source is not None and hasattr(self.current_source,
                                                       "volume"):
            self.current_source.volume = volume
            return True
        return False

    async def duck_for_speech(self):
        # chiamata da Lo Zozzone prima di un messaggio vocale: la musica non
        # si ferma, si abbassa, così le due tracce vanno in contemporanea
        self.ducked = True
        self.set_music_volume(DUCK_VOLUME)

    async def unduck_after_speech(self):
        self.ducked = False
        self.set_music_volume(1.0)

    @staticmethod
    def probe_duration(path):
        # la durata non è nei metadati che usa discord.py: serve ffprobe
        try:
            output = subprocess.check_output([
                "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                "-of", "csv=p=0", path
            ], timeout=20)
            return float(output.strip())
        except Exception as e:
            print("\tDurata non determinabile:", e)
            return None

    def track_position(self):
        # secondi di riproduzione effettiva del brano corrente
        if self.track_started is None:
            return None
        now = time.monotonic()
        paused = self.track_paused_total
        if self.track_paused_at is not None:
            paused += now - self.track_paused_at
        return max(0.0, now - self.track_started - paused)

    @staticmethod
    def format_time(seconds):
        seconds = int(seconds)
        if seconds >= 3600:
            return "%d:%02d:%02d" % (seconds // 3600,
                                     (seconds % 3600) // 60, seconds % 60)
        return "%d:%02d" % (seconds // 60, seconds % 60)

    def progress_bar(self):
        position = self.track_position()
        if position is None or not self.track_duration:
            return None
        total = self.track_duration
        position = min(position, total)
        # il pallino occupa una posizione: la barra resta sempre lunga uguale
        filled = min(int(BAR_LENGTH * position / total), BAR_LENGTH - 1)
        bar = "━" * filled + "🔘" + "─" * (BAR_LENGTH - filled - 1)
        return "`%s` %s `%s`" % (self.format_time(position), bar,
                                 self.format_time(total))

    async def progress_loop(self):
        # ridisegna la barra finché c'è qualcosa in riproduzione
        while self.play_messages_is_run:
            await asyncio.sleep(PROGRESS_REFRESH)
            if self.player_message is not None and self.is_busy():
                await self.refresh_player()

    def is_busy(self):
        return self.voice_client is not None and (
            self.voice_client.is_playing() or self.voice_client.is_paused())

    async def skip_current(self):
        # fermare la sorgente fa scattare la callback di fine brano: il file
        # viene archiviato e il player passa al successivo
        if self.is_busy():
            self.voice_client.stop()

    async def replay_current(self):
        # il brano resta in coda al suo posto e riparte da capo
        if self.is_busy():
            self.replay_flag = True
            self.voice_client.stop()
        else:
            self.ensure_player()

    async def previous_track(self):
        if not self.restore_previous():
            print("\tNessun brano precedente in cronologia")
            return
        if self.is_busy():
            # il brano corrente non va archiviato: si riascolterà dopo
            self.replay_flag = True
            self.voice_client.stop()
        else:
            self.ensure_player()

    async def stop_playback(self):
        self.stop_yt["flag_yt"] = True
        if self.voice_client is not None:
            self.voice_client.stop()

    def build_player_embed(self):
        queue = self.list_yt_music()
        if not queue:
            stato = "Coda vuota"
            colore = discord.Colour.dark_grey()
        elif self.voice_client is not None and self.voice_client.is_paused():
            stato = "In pausa"
            colore = discord.Colour.orange()
        elif self.voice_client is not None and self.voice_client.is_playing():
            stato = "In riproduzione"
            colore = discord.Colour.green()
        else:
            stato = "In attesa"
            colore = discord.Colour.blurple()

        embed = discord.Embed(title="🎵 Player", colour=colore)
        if queue:
            in_esecuzione = self.music_title(queue[0])[:200]
            barra = self.progress_bar()
            if barra:
                in_esecuzione += "\n" + barra
        else:
            in_esecuzione = "—"
        embed.add_field(name="In riproduzione",
                        value=in_esecuzione,
                        inline=False)
        if len(queue) > 1:
            righe = [
                str(i + 1) + ". " + self.music_title(name)[:70]
                for i, name in enumerate(queue[1:11], start=1)
            ]
            if len(queue) > 11:
                righe.append("… e altri " + str(len(queue) - 11))
            embed.add_field(name="In coda (" + str(len(queue) - 1) + ")",
                            value="\n".join(righe),
                            inline=False)
        history = self.history_files()
        if history:
            embed.add_field(name="Precedente",
                            value=self.music_title(history[-1])[:250],
                            inline=False)
        embed.set_footer(text=stato)
        return embed

    async def send_player(self, channel):
        # si tiene un solo pannello: il precedente viene rimosso
        if self.player_message is not None:
            try:
                await self.player_message.delete()
            except Exception:
                pass
        self.player_message = await channel.send(embed=self.build_player_embed(),
                                                 view=PlayerView(self))
        return self.player_message

    async def refresh_player(self):
        if self.player_message is None:
            return
        try:
            await self.player_message.edit(embed=self.build_player_embed())
        except Exception as e:
            # il messaggio può essere stato cancellato a mano
            print("Player non aggiornabile:", e)
            self.player_message = None

    def ensure_player(self):
        # il player gira come task sull'event loop del bot: usare un loop
        # separato in un thread rompe il voice client (è legato al loop del bot)
        if self.player_task is None or self.player_task.done():
            self.player_task = self.loop.create_task(self.play_messages())
        if self.progress_task is None or self.progress_task.done():
            self.progress_task = self.loop.create_task(self.progress_loop())

    def is_downloading(self):
        return self.download_thread is not None and self.download_thread.is_alive()

    async def play_messages(self):
        self.play_messages_is_run = True
        try:
            # repeat until the message audio folder is empty
            while True:
                audio_tts = self.list_yt_music()
                if not audio_tts:
                    # con le playlist la coda si svuota tra un download e
                    # l'altro: uscire qui ucciderebbe il player a metà coda
                    if self.is_downloading() and not self.stop_yt["flag_yt"]:
                        await asyncio.sleep(0.5)
                        continue
                    break
                await self.refresh_player()
                try:
                    await self.callback(audio_tts)
                except Exception as e:
                    print("Errore nella riproduzione:", e)
                    self.clean_audio_folder()
                    break
                await asyncio.sleep(0.5)
        finally:
            self.play_messages_is_run = False
            # lo stop è un segnale una tantum: va riarmato, altrimenti il
            # tasto salta successivo svuoterebbe di nuovo tutta la coda
            if not self.is_downloading():
                self.stop_yt["flag_yt"] = False
            await self.refresh_player()

    async def play_source(self, audio_source):
        # attende la fine della riproduzione senza bloccare l'event loop,
        # controllando periodicamente la richiesta di stop
        finished = asyncio.Event()
        loop = self.loop

        def after_playing(error):
            if error:
                print("\tErrore player:", error)
            loop.call_soon_threadsafe(finished.set)

        if self.voice_client.is_playing():
            self.voice_client.stop()
        start = time.monotonic()
        # azzera il cronometro della barra di avanzamento
        self.track_started = start
        self.track_paused_at = None
        self.track_paused_total = 0.0
        self.current_source = audio_source
        self.voice_client.play(audio_source, after=after_playing)
        while not finished.is_set():
            try:
                await asyncio.wait_for(finished.wait(), timeout=0.2)
            except asyncio.TimeoutError:
                if self.stop_yt["flag_yt"]:
                    self.voice_client.stop()
        # una durata di pochi decimi indica che ffmpeg è morto subito
        print("\tRiproduzione finita dopo %.1fs" % (time.monotonic() - start))

    async def callback(self, audio_tts):
        # play the text to speech audio
        print("callback:")
        audio2play = audio_tts[0]
        path = os.path.join(self.message_audio_path, audio2play)

        # il canale può mancare se il file è rimasto da un'esecuzione precedente
        channel = self.channels_audio.get(audio2play)
        if channel is not None:
            await self.ensure_voice(channel)
        if self.voice_client is None or not self.voice_client.is_connected():
            print("\tNessun canale voce disponibile, audio scartato.")
            self.remove_audio(audio2play)
            return

        codec, bitrate = await discord.FFmpegOpusAudio.probe(path)
        self.track_duration = await asyncio.to_thread(self.probe_duration, path)
        print("\t%s | codec %s | durata %s | canale %s" %
              (audio2play, codec,
               self.format_time(self.track_duration)
               if self.track_duration else "?", channel))
        # stderr esplicito: senza, gli errori di ffmpeg finiscono nel nulla
        if DUCK_VOLUME >= 1.0:
            # nessun ducking richiesto: il file opus viene copiato così com'è,
            # senza ricodifica (è quello che evita gli scatti)
            audio_source = discord.FFmpegOpusAudio(path,
                                                   codec=codec,
                                                   bitrate=bitrate,
                                                   before_options='-nostdin',
                                                   stderr=sys.stderr)
        else:
            # per regolare il volume al volo serve il PCM: si paga una
            # ricodifica, ma la musica può abbassarsi mentre l'altro parla
            audio_source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(path,
                                       before_options='-nostdin',
                                       stderr=sys.stderr),
                volume=DUCK_VOLUME if self.ducked else 1.0)
        try:
            await self.play_source(audio_source)
        finally:
            # il brano è finito: niente barra finché non parte il successivo
            self.track_started = None
            self.track_duration = None
            self.current_source = None
            if self.stop_yt["flag_yt"]:
                # stop: si svuota tutta la coda
                for yt_file in self.list_yt_music():
                    self.remove_audio(yt_file)
            elif self.replay_flag:
                # riascolta / indietro: il brano resta in coda dov'è
                self.replay_flag = False
            else:
                self.archive_audio(audio2play)

    def generate_idx_message(self):
        audio_tts = [
            f for f in self.list_yt_music() if f.split("_")[0].isdigit()
        ]
        if not audio_tts:
            return -1
        return max(int(f.split("_")[0]) for f in audio_tts)

    async def save_youtube_music(self,
                                 input,
                                 channel,
                                 random_queue,
                                 search_playlist=False):
        try:
            await self.ensure_voice(channel)

            query = input.strip()
            if query.startswith("http"):
                link = query
            elif search_playlist:
                link = await asyncio.to_thread(
                    self.youtube_downloader.search_youtube_playlist, query)
            else:
                link = await asyncio.to_thread(
                    self.youtube_downloader.search_youtube_link, query)
            if not link:
                print("Video non trovato")
                raise ValueError("Video non trovato")

            yt_down_thread = Thread(
                target=self.youtube_downloader.start_download,
                args=(link, self.channels_audio, channel, self.stop_yt,
                      random_queue),
                daemon=True)
            yt_down_thread.start()
            self.download_thread = yt_down_thread

            # attende il primo file scaricato, ma senza restare bloccata
            # per sempre se il download fallisce
            while not self.list_yt_music() and yt_down_thread.is_alive():
                await asyncio.sleep(0.2)
            if not self.list_yt_music():
                raise ValueError("Download fallito")
            self.ensure_player()
        except Exception as e:
            print(
                "##########################\nERRORE\n##########################"
            )
            print(e)
            raise


def main(token):
    global CURRENT_BOT
    bot = MyBotAUDIO(command_prefix=utils_prefix_la_zozzona, self_bot=False)
    CURRENT_BOT = bot
    try:
        # log_handler=None: il logging è configurato una sola volta in main.py,
        # altrimenti ogni bot aggiunge un handler e i log escono duplicati
        bot.run(token, log_handler=None)
    except discord.errors.HTTPException as e:
        if str(e.status) == "429":
            print("\n\n\nBLOCKED BY RATE LIMITS\nRESTARTING NOW\n\n\n")
            os.system("python restarter.py")
    except Exception as e:
        print("La Zozzona si è fermata:", e)
