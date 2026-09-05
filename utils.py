import os
import subprocess
import weakref

# Su Windows ffmpeg, ffprobe e yt-dlp girano in processi console: avviati da
# pythonw (che una console non ce l'ha) ne fanno lampeggiare una per un frame
# a ogni audio riprodotto. CREATE_NO_WINDOW evita che venga creata.
CREATE_NO_WINDOW = 0x08000000

# processi figli avviati dal bot (ffmpeg, ffprobe, yt-dlp): vanno terminati
# alla chiusura, altrimenti restano orfani a suonare e a tenere i file aperti
CHILD_PROCESSES = weakref.WeakSet()


def hide_subprocess_windows():
    original_init = subprocess.Popen.__init__
    # la patch va applicata una volta sola
    if getattr(original_init, "patched_by_bot", False):
        return

    def patched_init(self, *args, **kwargs):
        if os.name == "nt":
            kwargs["creationflags"] = kwargs.get("creationflags",
                                                 0) | CREATE_NO_WINDOW
        original_init(self, *args, **kwargs)
        CHILD_PROCESSES.add(self)

    patched_init.patched_by_bot = True
    subprocess.Popen.__init__ = patched_init


def kill_child_processes():
    # senza questo ffmpeg sopravvive alla chiusura della finestra
    for process in list(CHILD_PROCESSES):
        try:
            if process.poll() is None:
                process.kill()
        except Exception:
            pass


# Function: print_in_chat
# Description:
# This asynchronous function sends a given text to a specified chat channel. It can format the text in monospace,
# utilize text-to-speech (TTS), and handle long texts by splitting them appropriately based on specified characters.
#
# Parameters:
# - text (str): The text to be sent to the chat channel.
# - channel (object): The chat channel object where the text will be sent.
# - monospace (bool, optional): If True, the text will be formatted in monospace using triple backticks. Default is False.
# - tts (bool, optional): If True, the message will be sent with text-to-speech enabled. Default is False.
# - split_character (bool, optional): If True, the text will be split at spaces/newlines/tabs if it exceeds the limit.
#                                     If False, the text will be split by newlines only. Default is True.
async def print_in_chat(text,
                        channel,
                        monospace=False,
                        tts=False,
                        split_character=True):
    # Maximum number of characters allowed per message
    max_char = 1900

    # Determine the monospace formatting characters based on the monospace flag
    mono = "```" if monospace else ""

    if split_character:
        # If the text fits in one message, send it directly
        if len(text) <= max_char:
            await channel.send(mono + text + mono, tts=tts)
            return

        # Split the long text into chunks, breaking at whitespace boundaries
        chunks = []
        start = 0
        while start < len(text):
            end = start + max_char
            if end >= len(text):
                # Last chunk: take everything remaining
                chunks.append(text[start:])
                break
            # Try to break at a whitespace character to avoid cutting words
            split_pos = end
            for j in range(end, start, -1):
                if text[j] in (" ", "\n", "\t"):
                    split_pos = j
                    break
            chunks.append(text[start:split_pos])
            # Skip the whitespace character we split on
            start = split_pos + 1

        for chunk in chunks:
            if chunk:  # skip empty chunks
                await channel.send(mono + chunk + mono, tts=tts)
    else:
        # Split by newlines, accumulating rows until the chunk is full
        to_send = ""
        for row in text.split("\n"):
            if len(to_send) + len(row) + 1 < max_char:
                to_send += row + "\n"
            else:
                if to_send:
                    await channel.send(mono + to_send + mono, tts=tts)
                to_send = row + "\n"

        # Send the final remaining part
        if to_send:
            await channel.send(mono + to_send + mono, tts=tts)
