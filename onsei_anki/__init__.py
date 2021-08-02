import base64
import os
import re
from typing import Optional

import requests
from anki.cards import Card
from anki.hooks import wrap
from anki.notes import Note
from aqt import gui_hooks
from aqt import mw
from aqt.reviewer import Reviewer
from aqt.webview import AnkiWebView
from bs4 import BeautifulSoup

CONFIG = mw.addonManager.getConfig(__name__)
ADDON_PATH = os.path.dirname(__file__)
ADDON_FOLDERNAME = mw.addonManager.addonFromModule(__name__)
mw.addonManager.setWebExports(__name__, r"web.*")
SPINNER_PATH = f"/_addons/{ADDON_FOLDERNAME}/web/spinner.gif"
HOST = CONFIG["api_url"]


def on_reviewer_did_show_question(card: Card):
    """ Hook to display a simple graph when the question is shown during review """
    web = mw.reviewer.web

    nid = card.nid
    note = mw.col.getNote(nid)

    audio_filepath = get_sentence_audio_filepath(note)
    if not audio_filepath:
        if audio_filepath is None:
            display_html(error_div(f"Could not find sentence audio field ! Tried with: "
                                   f"{','.join(CONFIG['sentence_audio_fields'])}"), web)
        else:
            display_html(error_div("Sentence audio field is empty !"), web)
        return

    sentence = get_sentence_transcript(note)
    if not sentence:
        if sentence is None:
            display_html(error_div(f"Could not find sentence transcript field ! Tried with: "
                                   f"{','.join(CONFIG['sentence_transcript_fields'])}"), web)
        else:
            display_html(error_div("Sentence transcript field is empty !"), web)
        return

    div = get_graph_from_api(audio_filepath, sentence)
    inject_addon_div(div, web)


def on_replay_recorded(self: Reviewer):
    """ Hook to display a comparison graph when audio is recording by the user during a review """

    # Has audio been recorded yet ?
    if self._recordedAudio is None:
        return

    web = self.web

    display_html(f'<img height="100px" src="{SPINNER_PATH}"></img>', web, close_button=False)

    nid = self.card.nid
    note = self.mw.col.getNote(nid)

    audio_filepath = get_sentence_audio_filepath(note)
    if not audio_filepath:
        if audio_filepath is None:
            display_html(error_div(f"Could not find sentence audio field ! Tried with: "
                                   f"{','.join(CONFIG['sentence_audio_fields'])}"), web)
        else:
            display_html(error_div("Sentence audio field is empty !"), web)
        return

    sentence = get_sentence_transcript(note)
    if not sentence:
        if sentence is None:
            display_html(error_div(f"Could not find sentence transcript field ! Tried with: "
                                   f"{','.join(CONFIG['sentence_transcript_fields'])}"), web)
        else:
            display_html(error_div("Sentence transcript field is empty !"), web)
        return

    # showInfo(f"Will compare {self._recordedAudio} to {audio_filepath}")

    recorded_audio = self._recordedAudio
    if CONFIG["debug_use_ref_audio_as_my_recording"]:
        # For debugging purpose, will compare the reference audio with itself, so we don't have to record anything
        recorded_audio = audio_filepath

    div = get_graph_from_api(audio_filepath, sentence, recorded_audio)
    inject_addon_div(div, web)

    if CONFIG["reveal_answer_after_recording"]:
        self._showAnswer()


def on_card_will_show(text: str, card: Card, kind: str) -> str:
    """ Hook to show a graph in the card preview """

    if not kind.startswith("preview"):
        return text

    nid = card.nid
    note = mw.col.getNote(nid)

    audio_filepath = get_sentence_audio_filepath(note)
    if not audio_filepath:
        if audio_filepath is None:

            html = generate_addon_div(error_div(f"Could not find sentence audio field ! Tried with: "
                                                f"{','.join(CONFIG['sentence_audio_fields'])}"))
        else:
            html = generate_addon_div(error_div("Sentence audio field is empty !"))
        return html + text

    sentence = get_sentence_transcript(note)
    if not sentence:
        if sentence is None:
            html = generate_addon_div(error_div(f"Could not find sentence transcript field ! Tried with: "
                                                f"{','.join(CONFIG['sentence_transcript_fields'])}"))
        else:
            html = generate_addon_div(error_div("Sentence transcript field is empty !"))
        return html + text

    html = get_graph_from_api(audio_filepath, sentence)

    return html + text


def on_reviewer_did_answer_card(reviewer: Reviewer, card: Card, ease: int):
    """ Hook to remove the addon div after the card has been answered """
    script = f"""
    if ($("#onsei").length > 0) $("#onsei").remove();
    """
    reviewer.web.eval(script)


def get_sentence_transcript(note: Note) -> Optional[str]:
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


def get_graph_from_api(audio_filepath: str, sentence: str, recorded_audio: Optional[str] = None):

    if recorded_audio:
        # Comparing our recorded audio with the reference audio
        url = f"{HOST}/compare/graph.png"
        data = {"sentence": sentence, "show_all_graphs": CONFIG["show_all_graphs"]}
        files = {
            "teacher_audio_file": open(audio_filepath, 'rb'),
            "student_audio_file": open(recorded_audio, 'rb'),
        }
    else:
        # Displaying a graph for the reference audio only
        url = f"{HOST}/graph.png"
        data = {"sentence": sentence}
        files = {
            "audio_file": open(audio_filepath, 'rb'),
        }

    try:
        res = requests.post(url, data=data, files=files)
        if res.ok:
            b64_img = str(base64.b64encode(res.content), 'utf-8')
            height = CONFIG["graph_height_in_pixels"]
            style = f"max-height:{height};width:auto"
            div_content = f'<img id="graph" style="{style}" src="data:image/png;base64,{b64_img}"></img>'
        else:
            detail = res.json()['detail']
            div_content = error_div(detail)
    except requests.exceptions.ConnectionError:
        div_content = error_div("Could not connect to the Onsei API !")

    div = generate_addon_div(div_content)
    return div


def error_div(detail: str) -> str:
    return f"""
    <div style="color: #ba3939; background: #ffe0e0; border: 1px solid #a33a3a; padding: 10px; margin: 10px;">
        <b>Error</b>: {detail}
    </div>
    """


def display_html(div_content: str, web: AnkiWebView, close_button: bool = True):
    """
    Display the given HTML content at the beginning of the card's view, with a button to close.
    """
    div = generate_addon_div(div_content, close_button=close_button)
    inject_addon_div(div, web)


def generate_addon_div(div_content: str, close_button: bool = True):
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
    return div


def inject_addon_div(div: str, web: AnkiWebView) -> None:
    script = f"""
        if ($("#onsei").length > 0)
          $('#onsei').replaceWith('{div}');
        else
          $('body').prepend('{div}');
        """
    web.eval(script)


if CONFIG["show_in_preview"]:
    gui_hooks.card_will_show.append(on_card_will_show)
if CONFIG["show_in_question"]:
    gui_hooks.reviewer_did_show_question.append(on_reviewer_did_show_question)
gui_hooks.reviewer_did_answer_card.append(on_reviewer_did_answer_card)
Reviewer.onReplayRecorded = wrap(Reviewer.onReplayRecorded, on_replay_recorded)
