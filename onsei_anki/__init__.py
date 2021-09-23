from anki.hooks import wrap
from aqt import gui_hooks
from aqt.reviewer import Reviewer

from onsei_anki.config import CONFIG
from onsei_anki.api import get_graph_from_api
from onsei_anki.extract import get_sentence_transcript, get_sentence_audio_filepath
from onsei_anki.hooks import on_reviewer_did_show_question, on_replay_recorded, on_card_will_show, \
    on_reviewer_did_answer_card, on_reviewer_did_show_question_cleanup
from onsei_anki.html import error_div, display_html, generate_addon_div, inject_addon_div, img_div


if CONFIG["show_in_preview"]:
    gui_hooks.card_will_show.append(on_card_will_show)

if CONFIG["show_in_question"]:
    gui_hooks.reviewer_did_show_question.append(on_reviewer_did_show_question)
else:
    gui_hooks.reviewer_did_show_question.append(on_reviewer_did_show_question_cleanup)

gui_hooks.reviewer_did_answer_card.append(on_reviewer_did_answer_card)

Reviewer.onReplayRecorded = wrap(Reviewer.onReplayRecorded, on_replay_recorded)
