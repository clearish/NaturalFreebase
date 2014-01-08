"""Defines the context free grammar rules that will be used to parse the
English query.  All non-terminal rules appear hear.  Terminal rules that are
autogenerated from Freebase types, metaschema, etc. are imported from the
lexicon.
"""

from lexicon import lexicon

rules = "% start DP\n"

# Add all the auto-generated rules from the lexicon.
rules += '\n'.join(lexicon.rules.values())

rules += """

# ===== Brackets =====

# Note, these will sometimes add vacuous ambiguity.
# We could filter out parses with identical semantics at the end.

LBR -> '['
RBR -> ']'

DP -> LBR DP RBR
NBar -> LBR NBar RBR
NP -> LBR NP RBR

# ===== Non-Lexical Rules =====

DP -> NP | Det NP | Name
NP -> NBar | A NP
NBar -> N

# relational nouns
NBar -> N OF DP

# compounds (woman authors)
NBar -> N NBar

# PP modifiers (people from Canada)
NBar -> NBar P DP

# ===== Handwritten Lexical Rules =====

Det -> 'a' | 'an' | 'any' | 'some' | 'what' | 'which'
OF -> 'of'
# Magic operator for "Subj REL Obj" queries
P -> 'rel' | 'Rel' | 'REL'
P -> 'with'
A -> 'different'
A -> 'female' | 'male'
# Magic operator for "help N" queries
N -> 'help' | 'Help' | 'HELP'
# Relational nouns
N -> 'author' | 'authors' | 'child' | 'children' | 'kid' | 'kids' | 'mayor' | 'mayors'
# Nouns with type + property meaning
N -> 'man' | 'men' | 'novel' | 'novels' | 'woman' | 'women'
N -> 'anyone' | 'anything' | 'someone' | 'something' | 'thing' | 'things'

"""
