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
# - split_character (bool, optional): If True, the text will be split based on spaces, newlines, or tabs if it exceeds the character limit. If False, the text will be split by newlines only. Default is True.
async def print_in_chat(text,
                        channel,
                        monospace=False,
                        tts=False,
                        split_character=True):
    # Maximum number of characters allowed per message
    max_char = 1900

    # Determine the monospace formatting characters based on the monospace flag
    monospace_superscripts = "```" if monospace else ""

    if split_character:
        # If the text length is less than the max character limit, send the entire text
        if len(text) < max_char:
            to_send = monospace_superscripts + text + monospace_superscripts
            await channel.send(to_send, tts=tts)
            return

        # Initialize an empty buffer to hold partial text chunks
        buffer = ""

        # Loop through the text in chunks of max_char
        for i in range(max_char, len(text), max_char):
            # If the character at the current max_char position is a space, newline, or tab, split there
            if text[i] in [" ", "\n", "\t"]:
                # Prepare the message to send
                to_send = monospace_superscripts + buffer + " " + text[
                    i - max_char:i] + monospace_superscripts
                await channel.send(to_send, tts=tts)
            else:
                # If not, find the nearest space, newline, or tab before the max_char limit to split
                for j in range(i, -1, -1):
                    if text[j] in [" ", "\n", "\t"]:
                        # Prepare the message to send
                        to_send = monospace_superscripts + buffer + text[
                            i - max_char:j] + monospace_superscripts
                        await channel.send(to_send, tts=tts)
                        # Update the buffer with the remaining text after the split
                        buffer = text[j + 1:i]
                        break

        # If the end of the text has not been reached, send the remaining part
        if i != len(text) - 1:
            to_send = monospace_superscripts + buffer + text[
                i:] + monospace_superscripts
            await channel.send(to_send, tts=tts)
    else:
        # Initialize an empty string to hold the current message
        to_send = ""

        # Split the text by newline characters and process each row
        for row in text.split("\n"):
            # If the current message length plus the new row is within the limit, append the row
            if len(to_send) + len(row) + 1 < max_char:
                to_send += row + "\n"
            else:
                # If the limit is reached, send the current message and start a new one
                to_send = monospace_superscripts + to_send + monospace_superscripts
                await channel.send(to_send, tts=tts)
                # Start a new message with the current row
                to_send = row + "\n"

        # Send the final part of the text
        to_send = monospace_superscripts + to_send + monospace_superscripts
        await channel.send(to_send, tts=tts)
