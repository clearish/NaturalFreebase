"""Add entries to a noun table.  These can either be new senses of existing
nouns, or entirely new nouns.
"""

# XXX: Eventually this list will include nouns that have meaning beyond a type,
# including 'woman', 'mayor', etc.  This will require making a data structure
# for the noun table, along the same lines as the predicate table.

import inflect

def add_to(n_table):

    infl = inflect.engine()

    def add(noun, senses, plural=True):
        forms = [noun]
        if plural: forms.append(infl.plural_noun(noun))
        for form in forms:
            if form not in n_table: n_table[form] = set()
            n_table[form] |= senses  # Potentially non-overlapping senses.

    add('actor', {'/film/actor', '/tv/actor'})
    add('album', {'/music/album'})
    add('anyone', {'/people/person'}, plural=False)
    add('anything', set(), plural=False)
    add('anywhere', {'/location/location'}, plural=False)
    add('artist', {'/music/artist'})
    add('character', {'/fictional_universe/fictional_character'})
    add('director', {'/film/director'})
    add('place', {'/location/location'})
    add('thing', set())
    add('recording', {'/music/recording'})
    add('release', {'/music/release'})
    add('someone', {'/people/person'}, plural=False)
    add('something', set(), plural=False)
    add('somewhere', {'/location/location'}, plural=False)
    add('work', {'/visual_art/artwork'})
