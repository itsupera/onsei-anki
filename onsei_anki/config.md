Onsei Anki: Anki plugin for pitch accent practice
==================================================

This addon helps you practice your Japanese pitch accent while you do your Anki reps on audio sentence cards !

It will compare your own recording with the card's sentence audio and show you where your intonation differed from it.

Parameters
-----------

- `api_url`: URL of the Onsei API to connect to
- `debug_use_ref_audio_as_my_recording`: If set to `true`, will compared the reference audio to itself for debugging purpose (to not have to record anything).
- `graph_height_in_pixels`: Height in pixels of the comparison graph.
- `remove_parenthesis`: If set to `true`, will ignore all the text between parenthesis, e.g., `(...)`, in the sentence transcript.
- `remove_square_brackets`: If set to `true`, will ignore all the text between square brackets, e.g., `[...]`, in the sentence transcript.
- `reveal_answer_after_recording`: If set to `true`, reveal the back of the card after recording your voice.
- `decks`: List of deck names to use Onsei with (must contain cards with a sentence transcript and audio).
- `sentence_audio_fields`: List of card field names to look for sentence audio (in order of priority).
- `sentence_transcript_fields`: List of card field names to look for sentence transcript (in order of priority). 
- `show_all_graphs`: If set to `true`, will show not only the comparison graph, but also graphs for the reference (sentence) audio and your own recording.
- `show_in_preview`: If set to `true`, will show the sentence audio graph when previewing cards.
- `show_in_question`: If set to `true`, will show the sentence audio graph when display the front of the card during reviews (instead of only for the back of the card).
