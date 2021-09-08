from anki.cards import Card
from aqt import mw
from aqt.reviewer import Reviewer

from onsei_anki import CONFIG
from onsei_anki.api import get_graph_from_api
from onsei_anki.config import SPINNER_PATH
from onsei_anki.extract import get_sentence_audio_filepath, get_sentence_transcript
from onsei_anki.html import display_html, error_div, inject_addon_div, generate_addon_div, remove_addon_div


def on_reviewer_did_show_question(card: Card):
    """ Hook to display a simple graph when the question is shown during review """
    deck_name = mw.col.decks.name(card.did)
    if deck_name not in CONFIG["decks"]:
        return

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
    deck_name = mw.col.decks.name(self.card.did)
    if deck_name not in CONFIG["decks"]:
        return

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
    deck_name = mw.col.decks.name(card.did)
    if deck_name not in CONFIG["decks"]:
        return text

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
    if mw.col.name() not in CONFIG["decks"]:
        return

    remove_addon_div(reviewer.web)