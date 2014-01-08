def noun_meaning(typ):
    sem = "'mid': null, 'name': null, 'type': '%s'" % typ
    types = {typ}
    typed_meaning = TypedMeaning(types=types, sem=sem)
    return lambda: typed_meaning

def calc_pred_meaning(nbar, dp, subj_typ, obj_type, path):
    """Checks if NBar (as subject) and DP (as object) are potentially
    compatible with the sense in question.  If so, returns the TypedMeaning
    result of combining the two in this sense.  Otherwise returns None.
    """

    global unique_prefix  # XXX This will have the wrong scope...
    comp_nbar = compatible(nbar.types, {subj_type})
    comp_dp = compatible(dp.types, {obj_type})
    if min(comp_nbar, comp_dp) == 0: return
    types = {subj_type} | nbar.types
    sem = "%s, 'ns%d:type': '%s'," % (nbar.sem, unique_prefix, subj_type)
    unique_prefix += 1
    for property in path:
        sem += " 'ns%d:%s': [{" % (unique_prefix, property)
    unique_prefix += 1
    sem += ' %s' % dp.sem
    for property in path:
        sem += ' }]'
    reln=nbar.reln
    fit=comp_nbar * comp_dp * nbar.fit * dp.fit
    return TypedMeaning(types, sem, reln, fit)

def pred_meaning(subj_typ, obj_type, path):
    return lambda nbar, dp: \
            calc_pred_meaning(nbar, dp, subj_type, obj_type, path)

class Sense:
    """One meaning of one lexical item.  Stored as a function that returns a
    typed meaning given a list of arguments appropriate for the item."""

    def __init__(self, typed_meaning):
        self.typed_meaning = typed_meaning


# =================================================================

# Example lexical entries

lexicon['N']['person'].append(Sense(noun_meaning('/people/person')))

lexicon['N']['author'].append(Sense(reln_meaning('/book/author', '/book/written_work', ['/book/author/works_written'])))

lexicon['P']['by'].append(Sense(pred_meaning('/book/written_work', '/book/author', ['/book/written_work/author'])))

# =================================================================

    # How prepositions will be used in interpretation
    if tree[1][0] in lexicon['P']:
        for sense in lexicon['P'][tree[1][0]]:
            typed_meaning = sense.typed_meaning(nbar, dp)
            if typed_meaning: results.append(typed_meaning)

    # How nouns will be used in interpretation
    if tree[0] in lexicon['N']
        for sense in lexicon['N'][tree[0]]:
            results.append(sense.typed_meaning())

    # How relational nouns will be used in interpretation
    # (1) N of DP:
    if tree[0] in lexicon['N']:
        for sense in lexicon['N'][tree[0]]:
            typed_meaning = sense.typed_meaning(dp)
            if typed_meaning: results.append(typed_meaning)
    # (2) NBar with DP:
    # XXX: Hard to do this if the relational noun encodes a fixed function.
    # Really, we want the relational noun to encode a PredicateSense, and keep
    # functions like calc_pred_meaning() above in interpret.py

# =================================================================

    # How predicates were used in interpretation
    for predicate in lexicon.pred_table.values():
        # Currently ignoring lexical category of predicate.
        lexical_items = [x[1] for x in predicate.lexicalizations]
        if tree[1][0] in lexical_items:
            for sense in predicate.senses:
                meaning = pred_meaning(sense, nbar, dp)
                if meaning: results.append(meaning)

    # How nouns were used in interpretation
    if tree[0] in lexicon.N_table:
        for sense in lexicon.N_table[tree[0]]:
            sem = "'mid': null, 'name': null, 'type': '%s'" % sense
            results.append(TypedMeaning(types={sense}, sem=sem))
        if not lexicon.N_table[tree[0]]:
            sem = "'mid': null, 'name': null"
            results.append(TypedMeaning(types=set(), sem=sem))
