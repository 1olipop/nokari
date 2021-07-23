"""The main entry of the program."""
import os

from dotenv import load_dotenv
from nokari.core import Nokari

if os.name != "nt":
    import uvloop  # pylint: disable=import-error

    uvloop.install()

load_dotenv()

for var in (
    "DISCORD_BOT_TOKEN",
    "POSTGRESQL_DSN",
    "SPOTIPY_CLIENT_ID",
    "SPOTIPY_CLIENT_SECRET",
):
    if var not in os.environ:
        raise RuntimeError(f"{var} env variable must be set.")

if browser := os.getenv("DISCORD_BROWSER"):
    from nokari.utils.monkey_patch import set_browser

    set_browser(browser)


Nokari().run()
