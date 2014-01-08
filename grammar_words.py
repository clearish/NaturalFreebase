"""Create a list of all the words in grammar.py"""

import re
from grammar import rules

# Fancy regex to match single-quoted strings (which can contain backslashed
# single quotes).
regex = re.compile(r"""(?<!\\)(?:\\\\)*'([^'\\]*(?:\\.[^'\\]*)*)'""",
                   re.MULTILINE)

words = set()
for match in regex.finditer(rules):
    words |= { match.group(1) }
