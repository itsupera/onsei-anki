from typing import Optional

import requests

from onsei_anki.html import img_div, error_div, generate_addon_div
from onsei_anki.config import CONFIG

HOST = CONFIG["api_url"]


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
            div_content = img_div(res.content, CONFIG["graph_height_in_pixels"])
        else:
            detail = res.json()['detail']
            div_content = error_div(detail)
    except requests.exceptions.ConnectionError:
        div_content = error_div("Could not connect to the Onsei API !")

    div = generate_addon_div(div_content)
    return div
