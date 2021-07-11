import base64
import os
import re
import time
from typing import Optional

import requests
from anki.hooks import wrap
from aqt.reviewer import Reviewer
from aqt.utils import showInfo


SENTENCE_AUDIO_FIELDS = ["Sentence Audio", "Sentence-Audio"]
SENTENCE_TRANSCRIPT_FIELDS = ["Sentence", "Expression"]


def on_replay_recorded(self: Reviewer):
    # Has audio been recorded yet ?
    if self._recordedAudio is None:
        return

    nid = self.card.nid
    note = self.mw.col.getNote(nid)

    audio_filepath = get_sentence_audio_filepath(note, self)
    if not audio_filepath:
        if audio_filepath is None:
            display_html(error_div(f"Could not find sentence audio field ! Tried with: {','.join(SENTENCE_AUDIO_FIELDS)}"), self)
        else:
            display_html(error_div("Sentence audio field is empty !"), self)
        return

    sentence = get_sentence_transcript(note)
    if not sentence:
        if sentence is None:
            display_html(error_div(f"Could not find sentence transcript field ! Tried with: {','.join(SENTENCE_TRANSCRIPT_FIELDS)}"), self)
        else:
            display_html(error_div("Sentence transcript field is empty !"), self)
        return

    # showInfo(f"Will compare {self._recordedAudio} to {audio_filepath}")

    res = requests.post(
        "http://127.0.0.1:8000/compare/graph.png",
        data={"sentence": sentence},
        files={
            "teacher_audio_file": open(audio_filepath, 'rb'),
            "student_audio_file": open(self._recordedAudio, 'rb'),
        }
    )

    if res.ok:
        b64_img = str(base64.b64encode(res.content), 'utf-8')
        div_content = f'<img id="cmp_graph" src="data:image/png;base64,{b64_img}"></img>'
    else:
        detail = res.json()['detail']
        # showInfo(f"Error: {detail}")
        div_content = error_div(detail)

    display_html(div_content, self)


def get_sentence_transcript(note):
    for field in SENTENCE_TRANSCRIPT_FIELDS:
        if field in note:
            break
    else:
        return
    # Remove spaces and furigana annotations
    sentence = re.sub(r'\s+', '', re.sub(r'\[[^\]]*\]', '', note[field]))
    return sentence


def get_sentence_audio_filepath(note, reviewer: Reviewer) -> Optional[str]:
    for field in SENTENCE_AUDIO_FIELDS:
        if field in note:
            break
    else:
        return
    audio_filename = note[field].replace("[sound:", "").rstrip("]")
    # ~/.local/share/Anki2/User1/collection.media
    col_media_path = os.path.join(reviewer.mw.pm.profileFolder(), "collection.media")
    audio_filepath = os.path.join(col_media_path, audio_filename)
    return audio_filepath


def error_div(detail: str) -> str:
    # return f"""Error: toto""" # {detail.replace("'", " ")}"""
    return f"""
    <div style="color: #ba3939; background: #ffe0e0; border: 1px solid #a33a3a; padding: 10px; margin: 10px;">
        <b>Error</b>: {detail}
    </div>
    """


def display_html(div_content: str, reviewer: Reviewer):
    """
    Display the given HTML content at the beginning of the card's view, with a button to close.
    """
    div = f"""
    <div id="onsei" style="overflow: hidden">
        <button
            type="button" style="float: right" class="close"
            onclick="$(this).parent().remove();">
            ×
        </button>
        {div_content}
    </div>
    """.replace("\n", "")  # Need to remove newlines for the replace below to work

    script = f"""
    if ($("#onsei").length > 0)
      $('#onsei').replaceWith('{div}');
    else
      $('body').prepend('{div}');
    """

    reviewer.web.eval(script)


Reviewer.onReplayRecorded = wrap(Reviewer.onReplayRecorded, on_replay_recorded)