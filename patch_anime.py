import re

with open("plugins/anime.py", "r") as f:
    code = f.read()

# We'll completely replace the anime_cmd and handlers.
# Actually, let's just rewrite the entire plugins/anime.py to be safe and clean.
