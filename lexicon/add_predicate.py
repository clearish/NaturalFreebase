"""Add additional entries to a predicate table (i.e. the one generated directly
from the Freebase metaschema).  This can be new senses of existing predicates,
or entirely new predicates.
"""

from predicate_table import *

def add_to(pred_table):

    def add_lex(key, lex):
        if key not in pred_table:
            pred_table[key] = ConceptualPredicate([lex], senses=[])
        else: pred_table[key].lexicalizations += [lex]

    def add_sense(key, S, O, path):
        assert key in pred_table
        pred_table[key].senses.append(PredicateSense(S, O, path))

    add_sense('CreatedBy',
            '/film/film',
            '/film/director',
            ['/film/film/directed_by'])
    add_sense('HasChild',
            '/fictional_universe/fictional_character',
            '/fictional_universe/fictional_character',
            ['/fictional_universe/fictional_character/children'])
    add_lex('RecordingOnAlbum', ('P', 'on'))
    add_sense('RecordingOnAlbum', 
            '/music/recording',
            '/music/album',
            ['/music/recording/tracks',
             '/music/release_track/release',
             '/music/release/album'])
    add_lex('BasedOn', ('P', 'based on'))
    add_sense('BasedOn', 
            '/fictional_universe/fictional_character',
            '/fictional_universe/person_in_fiction',
            ['/fictional_universe/fictional_character/based_on'])
