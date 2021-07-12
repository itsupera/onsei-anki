import base64
import os
import re
import time
from typing import Optional

from aqt import gui_hooks
from bs4 import BeautifulSoup
import requests
from anki.hooks import wrap
from aqt.reviewer import Reviewer
from aqt.utils import showInfo
from aqt import mw

DEBUG_USE_REF_AS_MY_RECORDING = False


ADDON_PATH = os.path.dirname(__file__)
ADDON_FOLDERNAME = mw.addonManager.addonFromModule(__name__)


# FIXME make it work with a local file
# regex = r"web.*"
# mw.addonManager.setWebExports(__name__, regex)
# SPINNER_PATH = f"/_addons/{ADDON_FOLDERNAME}/web/spinner.gif"
SPINNER_PATH = f"https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fi.stack.imgur.com%2FkOnzy.gif&f=1&nofb=1"


CONFIG = mw.addonManager.getConfig(__name__)


def on_replay_recorded(self: Reviewer):
    # Has audio been recorded yet ?
    if self._recordedAudio is None:
        return

    display_html(f'<img height="100px" src="{SPINNER_PATH}"></img>', self, close_button=False)

    nid = self.card.nid
    note = self.mw.col.getNote(nid)

    audio_filepath = get_sentence_audio_filepath(note, self)
    if not audio_filepath:
        if audio_filepath is None:
            display_html(error_div(f"Could not find sentence audio field ! Tried with: "
                                   f"{','.join(CONFIG['sentence_audio_fields'])}"), self)
        else:
            display_html(error_div("Sentence audio field is empty !"), self)
        return

    sentence = get_sentence_transcript(note)
    if not sentence:
        if sentence is None:
            display_html(error_div(f"Could not find sentence transcript field ! Tried with: "
                                   f"{','.join(CONFIG['sentence_transcript_fields'])}"), self)
        else:
            display_html(error_div("Sentence transcript field is empty !"), self)
        return

    # showInfo(f"Will compare {self._recordedAudio} to {audio_filepath}")

    recorded_audio = self._recordedAudio
    if DEBUG_USE_REF_AS_MY_RECORDING:
        recorded_audio = audio_filepath

    res = requests.post(
        "http://127.0.0.1:8000/compare/graph.png",
        data={"sentence": sentence},
        files={
            "teacher_audio_file": open(audio_filepath, 'rb'),
            "student_audio_file": open(recorded_audio, 'rb'),
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
    for field in CONFIG['sentence_transcript_fields']:
        if field in note:
            break
    else:
        return
    soup = BeautifulSoup(note[field], features="lxml")
    sentence = soup.get_text()
    # Remove spaces, furigana annotations ...
    sentence = re.sub(r'\s+', '', sentence)
    if CONFIG["remove_parenthesis"]:
        sentence = re.sub(r'\([^\)]*\)', '', sentence)
    if CONFIG["remove_square_brackets"]:
        sentence = re.sub(r'\[[^\]]*\]', '', sentence)
    return sentence


def get_sentence_audio_filepath(note, reviewer: Reviewer) -> Optional[str]:
    for field in CONFIG['sentence_audio_fields']:
        if field in note:
            match = re.search(r"\[sound:([^\]]+)\]", note[field])
            if match:
                audio_filename = match.group(1)
                break
    else:
        return

    # ~/.local/share/Anki2/User1/collection.media
    col_media_path = os.path.join(reviewer.mw.pm.profileFolder(), "collection.media")
    audio_filepath = os.path.join(col_media_path, audio_filename)
    return audio_filepath


def error_div(detail: str) -> str:
    return f"""
    <div style="color: #ba3939; background: #ffe0e0; border: 1px solid #a33a3a; padding: 10px; margin: 10px;">
        <b>Error</b>: {detail}
    </div>
    """


def display_html(div_content: str, reviewer: Reviewer, close_button: bool = True):
    """
    Display the given HTML content at the beginning of the card's view, with a button to close.
    """
    close = f"""
    <button
        type="button" style="float: right" class="close"
        onclick="$(this).parent().remove();">
        ×
    </button>"""
    div = f"""
    <div id="onsei" style="overflow: hidden">
        {close if close_button else ""}
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


def cleanup_hook(reviewer, card, ease):
    script = f"""
    if ($("#onsei").length > 0) $("#onsei").remove();
    """
    reviewer.web.eval(script)


gui_hooks.reviewer_did_answer_card.append(cleanup_hook)