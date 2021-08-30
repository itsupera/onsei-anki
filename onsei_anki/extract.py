import os
import re
from typing import Optional

from anki.notes import Note
from aqt import mw
from bs4 import BeautifulSoup

from onsei_anki.config import CONFIG


def get_sentence_transcript(note: Note) -> Optional[str]:
    for field in CONFIG['sentence_transcript_fields']:
        if field in note:
            break
    else:
        return
    soup = BeautifulSoup(note[field], "html.parser")
    sentence = soup.get_text()
    # Remove spaces, furigana annotations ...
    sentence = re.sub(r'\s+', '', sentence)
    if CONFIG["remove_parenthesis"]:
        sentence = re.sub(r'\([^\)]*\)', '', sentence)
    if CONFIG["remove_square_brackets"]:
        sentence = re.sub(r'\[[^\]]*\]', '', sentence)
    return sentence


def get_sentence_audio_filepath(note: Note) -> Optional[str]:
    for field in CONFIG['sentence_audio_fields']:
        if field in note:
            match = re.search(r"\[sound:([^\]]+)\]", note[field])
            if match:
                audio_filename = match.group(1)
                break
    else:
        return

    # ~/.local/share/Anki2/User1/collection.media
    col_media_path = os.path.join(mw.pm.profileFolder(), "collection.media")
    audio_filepath = os.path.join(col_media_path, audio_filename)
    return audio_filepath