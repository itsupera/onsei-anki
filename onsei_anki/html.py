import base64

from aqt.webview import AnkiWebView


def img_div(content, height):
    b64_img = str(base64.b64encode(content), 'utf-8')
    style = f"max-height:{height};width:auto"
    return f'<img id="graph" style="{style}" src="data:image/png;base64,{b64_img}"></img>'


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


def remove_addon_div(web: AnkiWebView) -> None:
    script = f"""
        if ($("#onsei").length > 0) $("#onsei").remove();
    """
    web.eval(script)
