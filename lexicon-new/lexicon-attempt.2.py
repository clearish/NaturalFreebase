class Lexicon:
    """A table storing for each word (or multi-word), its category (e.g. 'N')
    as well as a list of all of its senses.
    """

    def __init__(self):
        self.lexicon = {}

    def add(self, category, word, sense):
        if category not in self.lexicon:
            self.lexicon[category] = {}
        if word not in self.lexicon[category]:
            self.lexicon[category][word] = []
        self.lexicon[category][word].append(sense)

    def senses(self, category, word):
        return self.lexicon[category][word]

# =============================================================================

class NounSense:
    """A noun sense has a set of usually 1 or sometimes 0 types (e.g. 'thing'),
    and may also specify certain restrictive content (e.g. 'woman' is something
    of type '/people/person' that has female gender).  The extra content is
    given in the form of (a portion of) a Freebase query, so this can also be
    used to ensure that related info is printed out.  For example, 'mayor' will
    also query for and print the jurisdiction of office.
    """
    def __init__(self, types, content=None):
        self.types = types
        self.content = content

class RelNSense:
    """A relational noun sense is a relation connecting a relational noun to an
    object of a given type.
    """
    def __init__(self, reln_type, obj_type, path):
        self.reln_type = reln_type
        self.obj_type = obj_type
        self.path = path

class PredicateSense:
    """A predicate sense is a relation connecting a subject of a given type to
    an object of a given type.
    """
    def __init__(self, subj_type, obj_type, path):
        self.subj_type = subj_type
        self.obj_type = obj_type
        self.path = path

class AdjCountrySense:
    def __init__(self, country_id):
        self.country_id = country_id

# -----------------------------------------------------------------

# Sample lexicon with hard-coded senses:

lexicon = Lexicon()

lexicon.add('N', 'person', NounSense({'/people/person'}))
lexicon.add('N', 'woman',
        NounSense({'/people/person'},
                  content="'/people/person/gender': [{ 'mid': '/m/02zsn' }]"))

lexicon.add('N', 'mayor', NounSense({'/government/politician'}, content="'!/government/government_position_held/office_holder': [{ '/government/government_position_held/jurisdiction_of_office': [{ 'name': null, 'mid': null }], '/government/government_position_held/basic_title': [{ 'name': 'Mayor' }] }]"))

lexicon.add('N', 'author', RelNSense('/book/author', '/book/written_work',
                                 ['/book/author/works_written']))

lexicon.add('P', 'by', PredicateSense('/book/written_work', '/book/author',
                                  ['/book/written_work/author']))

lexicon.add('A', 'Canadian', AdjCountrySense('/m/0d060g'))

senses = lexicon.senses('N', 'person')
print([sense.types for sense in senses])

# =================================================================

# def noun_meaning(sense):
#     # XXX: Check if sense is a simple noun sense (not a RelN) !!
#     types = sense.types
#     type_str = ''
#     for typ in types: type_str += ", 'type': %s" % typ
#     if sense.content: sense.content = ', ' + sense.content
#     sem = "'mid': null, 'name': null" + typ_str + sense.content
#     return TypedMeaning(types, sem)

# # How prepositions will be used in interpretation
# if tree[1][0] in lexicon['P']:
#     for sense in lexicon['P'][tree[1][0]]:
#         typed_meaning = pred_meaning(sense, nbar, dp)  # See interpret.py
#         if typed_meaning: results.append(typed_meaning)

# # How nouns will be used in interpretation
# if tree[0] in lexicon['N']
#     for sense in lexicon['N'][tree[0]]:
#         typed_meaning = noun_meaning(sense)
#         results.append(typed_meaning)

# # How relational nouns will be used in interpretation
# # (1) N of DP:
# if tree[0] in lexicon['N']:
#     for sense in lexicon['N'][tree[0]]:
#         # XXX: Where should we check that the sense is a RelN sense?
#         typed_meaning = reln_meaning(sense, dp)
#         if typed_meaning: results.append(typed_meaning)

# # (2) NBar with DP:
# if dp.reln in lexicon['N']:
#     for sense in lexicon['N'][dp.reln]:
#         typed_meaning = reverse_reln_meaning(sense, dp)  # REVERSE!!
#         if typed_meaning: results.append(typed_meaning)
