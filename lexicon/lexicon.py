"""Build the following lookup tables ready for use by the interpreter.  Some
   tables map English words onto useful information about these words.  For
   example, N_table maps (XXX not yet) English nouns onto an object containing
   the type restriction it imposes, its semantics, whether it can be used as
   a relational noun, and what its relational meaning is.  Others tables like
   prop_table and type_table go the other direction, mapping properties or
   types onto words that can describe them.

    N_table, A_table, pred_table, prop_table, type_table

(1) Populate each table with the automatically generated rules given in the
    corresponding rules file (e.g. rules_N.py)

(2) Modify the rules in any regular ways.  In the case of metaschema, stored in
    auto_predicate, this means using the translate_metaschema table to add
    lexicalizations for each metaschema predicate.

(3) Add additional handwritten entries.  These are either adding new words, or
    new senses of existing words.  The new entries are stored in separate files
    (e.g. add_N.py).
"""

from predicate_table import *

from auto_rules_N import table as auto_N
from auto_rules_A_country import table as auto_A_country
from auto_rules_predicate import table as auto_predicate
from auto_rules_property import table as auto_property
from auto_rules_type import table as auto_type

from translate_metaschema import translate_metaschema

import add_N
import add_A
import add_predicate

# --- Lexicon ---
(N_table, A_table, pred_table, prop_table, type_table) = ({}, {}, {}, {}, {})

# --- Grammar Rules ---
rules = { 'N':'', 'A':'', 'P':'' }


# =============================================================================
# Initialize the lexicon.
# =============================================================================

# ===== Type Table =====

type_table = auto_type

# ===== Property Table =====

prop_table = auto_property

# ===== Noun Table =====

N_table = auto_N 
add_N.add_to(N_table)

# ===== Adjective Table =====

for auto_rules in (auto_A_country, ):  # More auto Adj rules can go here.
    for adj in auto_rules:
        if adj not in A_table: A_table[adj] = []
        A_table[adj] += auto_rules[adj]

add_A.add_to(A_table)

# ===== Predicate Table =====

# Copy auto-generated metaschema contents into pred_table, using
# translate_metaschema to look up the lexicalizations.
for predicate in auto_predicate:
    senses = []
    for sense in auto_predicate[predicate]:
        senses.append(PredicateSense(sense[0], sense[1], sense[2]))
    lexicalizations = translate_metaschema[predicate]
    pred_table[predicate] = ConceptualPredicate(lexicalizations, senses)
# Add additional handwritten predicates and senses.
add_predicate.add_to(pred_table)


# =============================================================================
# Initialize the grammar rules.
# =============================================================================

for (cat, table) in (('N', N_table), ('A', A_table), ('P', pred_table)):
    rules[cat] += '# ===== Auto-Generated %s Grammar Rules =====\n' % cat
    rules[cat] += '%s ->' % cat
    if cat in {'N', 'A'}:
        rules[cat] += ' | '.join(["'" + x + "'" for x in sorted(table)])
    if cat in {'P'}:
        words = []
        for pred in table:
            words += [ lex[1] for lex in table[pred].lexicalizations ]
        rules[cat] += ' | '.join(["'" + x + "'" for x in sorted(words)])
