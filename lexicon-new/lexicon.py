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

class Sense:
    """One meaning of a lexical item, expressed as a list of argument type
    sets (one set of types per argument), a set of ArgRelations, and any
    additional content that needs to be added to the Freebase query resulting
    from the use of this sense.

    For example, one sense of 'by' is expressed by:
        arg_types -- ['/book/written_work', '/book/author']
        relations -- '/book/written_work/author'
    """
    def __init__(self, arg_types, relations=set(), content=None):
        # For convenience, translate:
        #     arg_types='foo'         ==> arg_types=[{'foo'}]
        #     arg_types=['foo','bar'] ==> arg_types=[{'foo'},{'bar'}]
        str_to_set = lambda x: {x} if isinstance(x, basestring) else x
        arg_types = str_to_set(arg_types)
        arg_types = map(str_to_set, arg_types)

        # For convenience, translate:
        #     relations='foo'         ==> relations={'foo'}
        #     relations={not_arg_rel} ==> relations={ArgRelation(not_arg_rel)}
        relations = str_to_set(relations)
        to_rel = lambda x: x if isinstance(x, ArgRelation) else ArgRelation(x)
        relations = map(to_rel, relations)

        self.arg_types = arg_types  # List of type sets, one per argument.
        self.relations = relations  # List of relations between arguments.
        self.content = content      # Extra content string.
        self.num_args = len(arg_types)
        assert self.num_args != 0

class ArgRelation:
    """Relates two arguments of a sense through a path."""
    def __init__(self, path, from_arg=0, to_arg=1):
        # For convenience, convert strings to paths (lists) of length 1.
        if isinstance(path, basestring):
            path = [path]
        self.path = path
        self.from_arg = from_arg
        self.to_arg = to_arg

# -----------------------------------------------------------------

# Sample lexicon:

lexicon = Lexicon()

lexicon.add('N', 'person', Sense('/people/person'))

lexicon.add('N', 'woman',
        Sense('/people/person',
              content="'/people/person/gender': [{ 'mid': '/m/02zsn' }]"))

lexicon.add('N', 'mayor',
        Sense('/government/politician',
              content="'!/government/government_position_held/office_holder': [{ '/government/government_position_held/jurisdiction_of_office': [{ 'name': null, 'mid': null }], '/government/government_position_held/basic_title': [{ 'name': 'Mayor' }] }]"))

lexicon.add('N', 'author',
        Sense(arg_types=['/book/author', '/book/written_work'],
              relations='/book/author/works_written'))

lexicon.add('P', 'by',
        Sense(arg_types=['/book/written_work', '/book/author'],
              relations='/book/written_work/author'))

# Think about:
#   Mexican films
#   Mexican people
#   Mexican restaurants

# XXX This is a different meaning for Canadian than we had in earlier verisons.
# XXX This is weird in that Canadian is a relation to an implicit object.
lexicon.add('A', 'Canadian',
        Sense(arg_types=['/people/person', '/location/country']
              relations='/people/person/nationality'))

senses = lexicon.senses('N', 'author')
print(senses[0].types)
print(senses[0].num_args)
print(senses[0].relations[0].path)

# =================================================================

# XXX: Rewrite noun_meaning for generalized senses.

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
