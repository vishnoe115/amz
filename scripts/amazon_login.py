"""Load the Amazon module once, triggering and persisting browser OAuth."""

from orpheus.core import Orpheus


orpheus = Orpheus()
orpheus.load_module("amazonmusic")
print("AMAZON_LOGIN_SUCCESS", flush=True)
