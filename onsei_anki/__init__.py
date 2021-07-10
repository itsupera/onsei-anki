import base64
import os
import re

import requests
from anki.hooks import wrap
from aqt.reviewer import Reviewer
from aqt.utils import showInfo


def on_replay_recorded(self):
    # Has audio been recorded yet ?
    if self._recordedAudio is None:
        return

    # Get the sentence audio and transcription from the current card
    nid = self.card.nid
    note = self.mw.col.getNote(nid)
    audio_filename = note['Sentence Audio'].replace("[sound:", "").rstrip("]")
    # ~/.local/share/Anki2/User1/collection.media
    col_media_path = os.path.join(self.mw.pm.profileFolder(), "collection.media")
    audio_filepath = os.path.join(col_media_path, audio_filename)
    # Remove spaces and furigana annotations
    sentence = re.sub(r'\s+', '', re.sub(r'\[[^\]]*\]', '', note['Sentence']))

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
        div_content = f'Error: {detail}'

    div = f'<div id="speech_analysis">{div_content}</div>'

    self.web.eval(f"""
    if ($("#speech_analysis").length > 0)
      $('#speech_analysis').replaceWith('{div}');
    else
      $('body').prepend('{div}');
    """)


Reviewer.onReplayRecorded = wrap(Reviewer.onReplayRecorded, on_replay_recorded)