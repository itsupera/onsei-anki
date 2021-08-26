import os

from aqt import mw

CONFIG = mw.addonManager.getConfig(__name__)
ADDON_PATH = os.path.dirname(__file__)
ADDON_FOLDERNAME = mw.addonManager.addonFromModule(__name__)
mw.addonManager.setWebExports(__name__, r"web.*")
SPINNER_PATH = f"/_addons/{ADDON_FOLDERNAME}/web/spinner.gif"