"""Define interpretation functions DP(), NP(), NBar(), A(), N() that take Tree
objects and return possible interpretations, as lists of TypedMeanings.
"""

import re
from nltk.tree import Tree

from compatibility import compatible
from lexicon import lexicon

FUZZY_NAMES = False

# Meanings not in ACCURACY most likely (by 'fit' score, ties included) get
# pruned at various steps of interpretation.  This is to avoid the overhead
# of further calculations combining with less likely meanings.
ACCURACY = 10

# Store whether any meanings were cut due to accuracy since the last time this
# was set.  This is useful for telling whether it would be worthwhile to run
# again with higher accuracy.
MADE_ACCURACY_CUTS = False

unique_prefix = 0

class TypedMeaning:
    """A TypedMeaning represents one possible interpretation of a Tree node,
    including its types, semantics, what relational noun (if any) heads the
    phrase, and how good a fit this meaning is.
    """

    def __init__(self, types=None, sem=None, reln=None, fit=1):
        self.types = types  # Set of required Freebase types.
        self.sem = sem      # Semantics, as a Freebase query.
        self.reln = reln    # Relational noun head of phrase.
        self.fit = fit      # How good a fit this meaning is.

def best(N, meanings):
    """Returns the N TypedMeanings with best fit.  Can return more than N in
    the case of ties (or near-ties) for the Nth best."""
    global MADE_ACCURACY_CUTS
    length = len(meanings)
    meanings_by_fit = sorted(meanings, key=lambda x: x.fit, reverse=True)
    if length <= N:
        return meanings_by_fit
    threshold = meanings_by_fit[N-1].fit
    cutoff = N
    # A tiny bit less counts as a tie.  This lets aliases and partial name
    # matches count as equally good and not be pruned.
    while cutoff < length and meanings_by_fit[cutoff].fit > threshold * 0.99:
        cutoff += 1
    if cutoff < length: MADE_ACCURACY_CUTS = True
    return meanings_by_fit[:cutoff]

def DP(tree):
    results = []
    if isinstance(tree[0], basestring):
        # Find in order of preference results where:
        #
        #     (1) Query matches 'name' field exactly.
        #     (2) Query matches 'alias' field exactly.
        #     (3) Query is contained as an entire word of 'name' field.
        #     (4) Query is contained as an entire word of 'alias' field.
        #
        # Note, the containing word match is too loose.  E.g. 'United States'
        # will match 'Folklore of the United States'.  I don't think there's an
        # easy way around this problem.

        # 'name' matches.
        results.append(TypedMeaning(types=set(),
                sem="'mid': null, 'name': '%s'" % tree[0], fit=1))
        # 'alias' matches.
        results.append(TypedMeaning(types=set(),
                sem="'mid': null, 'name': null, "
                      "'/common/topic/alias': '%s'"
                      % tree[0], fit=1-10**-6))  # Just a tad less than 1.
        if FUZZY_NAMES:
            # 'name' contains matching word.
            results.append(TypedMeaning(types=set(),
                    sem="'mid': null, 'name': null, 'name~=': '%s'"
                          % tree[0], fit=1-10**-4))  # A bit further from 1.
            # 'alias' contains matching word.
            results.append(TypedMeaning(types=set(),
                    sem="'mid': null, 'name': null,"
                          "'/common/topic/alias~=': '%s'"
                          % tree[0], fit=1-10**-2))  # Still further from 1.
    elif tree[0].node == 'NP':
        results = NP(tree[0])
    # Ignore determiners.
    elif tree[0].node == 'Det' and tree[1].node == 'NP':
        results = NP(tree[1])
    # Ignore brackets.
    elif tree[0].node == 'LBR':
        results = DP(tree[1])
    else: raise Exception("Can't interpret DP.")
    return best(ACCURACY, results)

def NP(tree):

#   def add_NBar_modifier(NP_tree, NBar_modifier):
#       """Adds an NBar modifier to an NP tree.  This needs to look within the
#       NP past any Adj modifiers to the outermost NBar level, and then adds
#       the NBar modifier there.  Note, the NBar modifier is given as an NBar
#       containing an NBar as FIRST daughter.  (Assuming that all NBar
#       modifiers appear on the right.)  A more robust version would locate the
#       position of the NBar daughter within the modifier."""
#       if NP_tree[0].node == 'NBar':
#           new_NBar = NBar_modifier
#           new_NBar[0] = NP_tree[0] # Assume NBar is first within modifier.
#           NP_tree[0] = new_NBar
#           return NP_tree
#
#       elif NP_tree[1].node == 'NP':
#           NP_tree[1] = add_NP_modifier(NP_tree[1], NBar_modifier)
#           return NP_tree
#
#       # All NP rules other than NP -> NBar should have another NP as the
#       # second daughter.
#       assert False

    results = []
    if tree[0].node == 'NBar': results = NBar(tree[0])
    elif tree[0].node == 'LBR': results = NP(tree[1])

    # NP -> A NP
    elif tree[0].node == 'A':
        (a_meanings, np_meanings) = (A(tree[0]), NP(tree[1]))
        for a in a_meanings:
            for np in np_meanings:
                # Restaurant NP has cuisine-type A.
                comp_a = compatible(a.types, {'/dining/cuisine'})
                comp_np = compatible(np.types, {'/dining/restaurant'})
                if min(comp_a, comp_np) > 0:
                    results.append(TypedMeaning(
                            types={'/dining/restaurant'} | np.types,
                            sem=np.sem + ", '/dining/restaurant/cuisine': " \
                                       + "[{" + a.sem + "}]",
                            reln=np.reln, fit=comp_np*np.fit))
                # Person NP has nationality A.
                comp_a = compatible(a.types, {'/location/country'})
                comp_np = compatible(np.types, {'/people/person'})
                if min(comp_a, comp_np) > 0:
                    results.append(TypedMeaning(
                            types={'/people/person'} | np.types,
                            sem=np.sem + ", '/people/person/nationality': " \
                                       + "[{" + a.sem + "}]",
                            reln=np.reln, fit=comp_np*np.fit))
                # Person NP has ethnicity A.
                comp_a = compatible(a.types, {'/people/ethnicity'})
                comp_np = compatible(np.types, {'/people/person'})
                if min(comp_a, comp_np) > 0:
                    results.append(TypedMeaning(
                            types={'/people/person'} | np.types,
                            sem=np.sem + ", '/people/person/ethnicity': " \
                                       + "[{" + a.sem + "}]",
                            reln=np.reln, fit=comp_np*np.fit))
                # Person NP has gender A.
                comp_a = compatible(a.types, {'/people/gender'})
                comp_np = compatible(np.types, {'/people/person'})
                if min(comp_a, comp_np) > 0:
                    results.append(TypedMeaning(
                            types={'/people/person'} | np.types,
                            sem=np.sem + ", '/people/person/gender': " \
                                       + "[{" + a.sem + "}]",
                            reln=np.reln, fit=comp_np*np.fit))
                # Fictional character NP has (fictional) gender A.
                comp_a = compatible(a.types, \
                        {'/fictional_universe/character_gender'})
                comp_np = compatible(np.types, \
                        {'/fictional_universe/fictional_character'})
                if min(comp_a, comp_np) > 0:
                    results.append(TypedMeaning(
                            types={'/fictional_universe/fictional_' \
                                    + 'character'} | np.types,
                            sem=np.sem + ', ' + "'/fictional_universe/" \
                                       + "fictional_character/gender': "\
                                       + "[{" + a.sem + "}]",
                            reln=np.reln, fit=comp_np*np.fit))
    else: raise Exception("Can't interpret NP.")
    return results

def pred_meaning(sense, nbar, dp):
    """Checks if NBar (as subject) and DP (as object) are
    potentially compatible with the sense in question.  If so,
    returns the TypedMeaning result of combining the two in
    this sense.  Otherwise returns None.
    """

    global unique_prefix
    comp_nbar = compatible(nbar.types, {sense.S_type})
    comp_dp = compatible(dp.types, {sense.O_type})
    if min(comp_nbar, comp_dp) == 0: return
    types = {sense.S_type} | nbar.types
    sem = "%s, 'ns%d:type': '%s'," % (nbar.sem, unique_prefix,
                                      sense.S_type)
    unique_prefix += 1
    for property in sense.path:
        sem += " 'ns%d:%s': [{" % (unique_prefix, property)
    unique_prefix += 1
    sem += ' %s' % dp.sem
    for property in sense.path:
        sem += ' }]'
    reln=nbar.reln
    fit=comp_nbar * comp_dp * nbar.fit * dp.fit
    return TypedMeaning(types, sem, reln, fit)

def NBar(tree):
    global unique_prefix
    results = []
    if len(tree) == 1 and tree[0].node == 'N': results = N(tree[0])
    elif tree[0].node == 'LBR': results = NBar(tree[1])

    # --- NBar -> N NBar ---
    elif tree[0].node == 'N' and tree[1].node == 'NBar':
        (n_meanings, nbar_meanings) = (N(tree[0]), NBar(tree[1]))
        for n in n_meanings:
            # Modify the noun semantics by removing redundant 'name' and 'mid'
            # fields and changing 'type' to 'ns5:type', where 'ns5' is a unique 
            # identifier (in case we have 'politician woman author').
            n.sem = re.sub(r"'name': null, ", '', n.sem)
            n.sem = re.sub(r"'mid': null, ", '', n.sem)
            n.sem = re.sub(r"'type':", "'ns" + str(unique_prefix) + ":type':",
                           n.sem)
            unique_prefix += 1
            for nbar in nbar_meanings:
                comp_n_nbar = compatible(n.types, nbar.types)
                if comp_n_nbar > 0:
                    results.append(TypedMeaning(types=n.types | nbar.types,
                            sem=n.sem + ', ' + nbar.sem, reln=nbar.reln,
                            fit=comp_n_nbar * nbar.fit))

    # --- NBar -> N OF DP ---
    elif tree[0].node == 'N' and tree[1].node == 'OF':
        (n_meanings, dp_meanings) = (N(tree[0]), DP(tree[2]))

        for n in n_meanings:
            for dp in dp_meanings:
                if n.reln == 'author':
                    comp_dp = compatible(dp.types, {'/book/written_work'})
                    if comp_dp > 0:
                        results.append(TypedMeaning(types=n.types,
                                sem="'mid': null, 'name': null, '/book/author/works_written': [{ " + dp.sem + " }]",
                                fit=comp_dp*dp.fit))
                if n.reln == 'child':
                    comp_dp = compatible(dp.types, {'/people/person'})
                    if comp_dp > 0:
                        results.append(TypedMeaning(types=n.types,
                                sem="'mid': null, 'name': null, '!/people/person/children': [{ " + dp.sem + " }]",
                                fit=comp_dp*dp.fit))
                if n.reln == 'mayor':
                    comp_dp = compatible(dp.types, {'/location/citytown'})
                    if comp_dp > 0:
                        results.append(TypedMeaning(types=n.types,
                                sem="'mid': null, 'name': null, '!/government/government_position_held/office_holder': [{ '/government/government_position_held/jurisdiction_of_office': [{ " + dp.sem + " }], '/government/government_position_held/basic_title': [{ 'name': 'Mayor' }] }]",
                                fit=comp_dp*dp.fit))

    # --- NBar -> NBar P DP ---
    elif tree[0].node == 'NBar' and tree[1].node == 'P':
        (nbar_meanings, dp_meanings) = (NBar(tree[0]), DP(tree[2]))

        suggestions = []
        for nbar in nbar_meanings:
            for dp in dp_meanings:

                # Add compatible interpretations from the predicate table.
                for predicate in lexicon.pred_table.values():
                    # Currently ignoring lexical category of predicate.
                    lexical_items = [x[1] for x in predicate.lexicalizations]
                    if tree[1][0] in lexical_items:
                        for sense in predicate.senses:
                            meaning = pred_meaning(sense, nbar, dp)
                            if meaning: results.append(meaning)

                if tree[1][0].lower() == 'rel':
                    meanings = []
                    for predicate in lexicon.pred_table.values():
                        for sense in predicate.senses:
                            meaning = pred_meaning(sense, nbar, dp)
                            if meaning:
                                meanings.append((meaning, sense,
                                        predicate.lexicalizations))
                    # # Sort list of meaning/sense/lexes tuples by meaning.fit
                    # meanings = sorted(meanings, key=lambda x: x[0].fit,
                    #                   reverse=True)
                    for (meaning, sense, lexes) in meanings:
                        S_type = lexicon.type_table[sense.S_type]
                        O_type = lexicon.type_table[sense.O_type]
                        # Rate relations involving 'topic' as slightly worse.
                        if S_type == 'topic' or O_type == 'topic':
                            meaning.fit *= 0.99
                        suggestions.append(
                                (meaning.fit, S_type, lexes[0][1], O_type))

                if tree[1][0] == 'with':
                    if dp.reln == 'author':
                        comp_nbar = compatible(nbar.types,
                                {'/book/written_work'})
                        comp_dp = compatible(dp.types, {'/book/author'})
                        if min(comp_nbar, comp_dp) > 0:
                            results.append(TypedMeaning(
                                    types={'/book/written_work'} | nbar.types,
                                    sem=nbar.sem + ", '/book/written_work/author': [{ " + dp.sem + " }]", reln=nbar.reln,
                                    fit=comp_nbar*comp_dp*nbar.fit*dp.fit))
                    if dp.reln == 'child':
                        comp_nbar = compatible(nbar.types, {'/people/person'})
                        comp_dp = compatible(dp.types, {'/people/person'})
                        if min(comp_nbar, comp_dp) > 0:
                            results.append(TypedMeaning(
                                    types={'/people/person'} | nbar.types,
                                    sem=nbar.sem + ", '/people/person/children': [{ " + dp.sem + " }]",
                                    reln=nbar.reln,
                                    fit=comp_nbar*comp_dp*nbar.fit*dp.fit))
                    if dp.reln == 'mayor':
                        comp_nbar = compatible(nbar.types,
                                {'/location/citytown'})
                        comp_dp = compatible(dp.types,
                                {'/government/politician'})
                        if min(comp_nbar, comp_dp) > 0:
                            results.append(TypedMeaning(
                                    types={'/location/citytown'} | nbar.types,
                                    sem=nbar.sem + ", '!/government/government_position_held/jurisdiction_of_office': [{ '/government/government_position_held/office_holder': [{ " + dp.sem + " }], '/government/government_position_held/basic_title': [{ 'name': 'Mayor' }] }]",
                                    reln=nbar.reln,
                                    fit=comp_nbar*comp_dp*nbar.fit*dp.fit))

        # If suggestions were generated, print the best N of them.
        # Skip repeated suggestions.
        if suggestions:
            HELP_SUGGESTS = 20
            seen_suggest = set()
            # Sort by fit > lowercase relation > relation > subject > length
            suggestions = sorted(suggestions, key=lambda x:
                    (-x[0], not x[2].islower(), x[2], x[1],
                     len(x[1]+x[2]+x[3])))
            i = 0
            fit = 1
            while i < len(suggestions) and (i < HELP_SUGGESTS or fit > 0.99):
                sugg = suggestions[i]
                fit = sugg[0]
                sugg_str = "%s '%s' %s" % (sugg[1], sugg[2], sugg[3])
                if sugg_str not in seen_suggest:
                    seen_suggest |= {sugg_str}
                    print("Help: (fit=%.2f) %s" % (sugg[0], sugg_str))
                    i += 1
                else: suggestions.pop(i)  # Skip this suggestion and try again.
            if i == HELP_SUGGESTS: print('...')
                

    # =========================================================================
    # Relative Clause Rule Goes Here?
    # Don't forget to add reln=nbar.reln
    # =========================================================================

    return results

def A(tree):

    results = []

    if tree[0] == 'Mexican': results.append(TypedMeaning(
            types={'/dining/cuisine'}, sem="'mid': '/m/051zk'"))
    if tree[0] == 'female': results.append(TypedMeaning(
            types={'/people/gender'}, sem="'mid': '/m/02zsn'"))
    if tree[0] == 'male': results.append(TypedMeaning(
            types={'/people/gender'}, sem="'mid': '/m/05zppz'"))

    # =========================================================================
    # Insert Auto-Generated Adj Interpretation Rules Here
    # =========================================================================

    # ===== Automated A() Interpretation Rules for Countries =====
    if tree[0] in {'American'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/09c7w0'"))
    if tree[0] in {'German'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0345h'"))
    if tree[0] in {'Australian', 'Aussie'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0chghy'"))
    if tree[0] in {'Iranian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03shp'"))
    if tree[0] in {'British'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/07ssc'"))
    if tree[0] in {'Hongkongese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03h64'"))
    if tree[0] in {'Icelander'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03rj0'"))
    if tree[0] in {'French'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0f8l9c'"))
    if tree[0] in {'Indian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03rk0'"))
    if tree[0] in {'Canadian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0d060g'"))
    if tree[0] in {'Russian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06bnz'"))
    if tree[0] in {'Japanese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03_3d'"))
    if tree[0] in {'Italian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03rjj'"))
    if tree[0] in {'Filipino'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05v8c'"))
    if tree[0] in {'South African'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0hzlz'"))
    if tree[0] in {'Thai'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/07f1x'"))
    if tree[0] in {'Polish'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05qhw'"))
    if tree[0] in {'English'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02jx1'"))
    if tree[0] in {'Irish'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03rt9'"))
    if tree[0] in {'Brazilian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/015fr'"))
    if tree[0] in {'Argentine', 'Argentinean'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0jgd'"))
    if tree[0] in {'Belgian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0154j'"))
    if tree[0] in {'Netherlander', 'Hollander', 'Dutch'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/059j2'"))
    if tree[0] in {'Dane', 'Danish'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0k6nt'"))
    if tree[0] in {'Swede', 'Swedish'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0d0vqn'"))
    if tree[0] in {'Turk', 'Turkish'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01znc_'"))
    if tree[0] in {'Venezuelan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/07ylj'"))
    if tree[0] in {'North Korean'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05b7q'"))
    if tree[0] in {'South Korean'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06qd3'"))
    if tree[0] in {'Mexican'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0b90_r'"))
    if tree[0] in {'Czechoslovakian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01mk6'"))
    if tree[0] in {'Russian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0cdbq'"))
    if tree[0] in {'Kiwi', 'New Zealand'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0ctw_b'"))
    if tree[0] in {'Lithuanian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04gzd'"))
    if tree[0] in {'Spaniard', 'Spanish'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06mkj'"))
    if tree[0] in {'West German'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/082fr'"))
    if tree[0] in {'Singaporean'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06t2t'"))
    if tree[0] in {'Norwegian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05b4w'"))
    if tree[0] in {'Czech'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01mjq'"))
    if tree[0] in {'Croat', 'Croatian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01pj7'"))
    if tree[0] in {'Slovak', 'Slovakian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06npd'"))
    if tree[0] in {'Moroccan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04wgh'"))
    if tree[0] in {'Luxembourger'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04g61'"))
    if tree[0] in {'Pakistani'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05sb1'"))
    if tree[0] in {'Finn', 'Finnish'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02vzc'"))
    if tree[0] in {'Swiss'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06mzp'"))
    if tree[0] in {'Motswana', 'Batswana'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0166v'"))
    if tree[0] in {'Malaysian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/09pmkv'"))
    if tree[0] in {'Egyptian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02k54'"))
    if tree[0] in {'Hungarian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03gj2'"))
    if tree[0] in {'Andorran'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0hg5'"))
    if tree[0] in {'Emirian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0j1z8'"))
    if tree[0] in {'Afghan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0jdd'"))
    if tree[0] in {'Albanian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0jdx'"))
    if tree[0] in {'Armenian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0jgx'"))
    if tree[0] in {'Angolan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0j4b'"))
    if tree[0] in {'Austrian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0h7x'"))
    if tree[0] in {'Aruban'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0j11'"))
    if tree[0] in {'Azerbaijani'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0jhd'"))
    if tree[0] in {'Bosnian', 'Herzegovinian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0166b'"))
    if tree[0] in {'Barbadian', 'Bajun'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0162v'"))
    if tree[0] in {'Bangladeshi'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0162b'"))
    if tree[0] in {'Burkinabe', 'Burkinab'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01699'"))
    if tree[0] in {'Bulgarian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/015qh'"))
    if tree[0] in {'Bahraini'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0161c'"))
    if tree[0] in {'Burundian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0169t'"))
    if tree[0] in {'Beninese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0164v'"))
    if tree[0] in {'Bermudan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0165b'"))
    if tree[0] in {'Bruneian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0167v'"))
    if tree[0] in {'Bolivian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0165v'"))
    if tree[0] in {'Bahaman'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0160w'"))
    if tree[0] in {'Bhutanese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/07bxhl'"))
    if tree[0] in {'Belarusian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0163v'"))
    if tree[0] in {'Belizean'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0164b'"))
    if tree[0] in {'Central African'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01nyl'"))
    if tree[0] in {'Congolese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01rxw'"))
    if tree[0] in {'Ivorian', 'Ivoirian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0fv4v'"))
    if tree[0] in {'Chilean'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01p1v'"))
    if tree[0] in {'Cameroonian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01nln'"))
    if tree[0] in {'Chinese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0d05w3'"))
    if tree[0] in {'Colombian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01ls2'"))
    if tree[0] in {'Costa Rican'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01p8s'"))
    if tree[0] in {'Serbian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/077qn'"))
    if tree[0] in {'Cuban'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0d04z6'"))
    if tree[0] in {'Cape Verdean'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01nqj'"))
    if tree[0] in {'Cypriot'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01ppq'"))
    if tree[0] in {'Djibouti'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/027jk'"))
    if tree[0] in {'Dominican'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/027nb'"))
    if tree[0] in {'Dominican'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/027rn'"))
    if tree[0] in {'Algerian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0h3y'"))
    if tree[0] in {'Ecuadorean'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02k1b'"))
    if tree[0] in {'Estonian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02kmm'"))
    if tree[0] in {'Eritrean'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02khs'"))
    if tree[0] in {'Ethiopian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/019pcs'"))
    if tree[0] in {'Fijian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02wt0'"))
    if tree[0] in {'Grenadian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/035yg'"))
    if tree[0] in {'Georgian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0d0kn'"))
    if tree[0] in {'Ghanaian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/035dk'"))
    if tree[0] in {'Gambian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0hdx8'"))
    if tree[0] in {'Guinean'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03676'"))
    if tree[0] in {'Guadeloupean'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/037nm'"))
    if tree[0] in {'Equatorial Guinean', 'Equatoguinean'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02kcz'"))
    if tree[0] in {'Greek'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/035qy'"))
    if tree[0] in {'Guatemalan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0345_'"))
    if tree[0] in {'Guamanian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/034tl'"))
    if tree[0] in {'Guinea-Bissauan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/036b_'"))
    if tree[0] in {'Guyanese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/034m8'"))
    if tree[0] in {'Honduran'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03h2c'"))
    if tree[0] in {'Haitian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03gyl'"))
    if tree[0] in {'Indonesian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03ryn'"))
    if tree[0] in {'Israeli'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03spz'"))
    if tree[0] in {'Iraqi'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0d05q4'"))
    if tree[0] in {'Jamaican'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03_r3'"))
    if tree[0] in {'Jordanian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03__y'"))
    if tree[0] in {'Kenyan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/019rg5'"))
    if tree[0] in {'Cambodian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01xbgx'"))
    if tree[0] in {'I-Kiribati'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/047t_'"))
    if tree[0] in {'Comoran'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01n6c'"))
    if tree[0] in {'Kittian', 'Nevisian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06ryl'"))
    if tree[0] in {'Kuwaiti'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/047yc'"))
    if tree[0] in {'Kazakhstani'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/047lj'"))
    if tree[0] in {'Lao', 'Laotian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04hhv'"))
    if tree[0] in {'Lebanese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04hqz'"))
    if tree[0] in {'Saint Lucian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06s0l'"))
    if tree[0] in {'Liechtensteiner'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04j53'"))
    if tree[0] in {'Sri Lankan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06m_5'"))
    if tree[0] in {'Liberian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04hzj'"))
    if tree[0] in {'Mosotho', 'Basotho'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04hvw'"))
    if tree[0] in {'Latvian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04g5k'"))
    if tree[0] in {'Libyan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04gqr'"))
    if tree[0] in {'Monegasque', 'Monacan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04w58'"))
    if tree[0] in {'Moldovan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04w4s'"))
    if tree[0] in {'Malagasy'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04sj3'"))
    if tree[0] in {'Marshallese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04v6v'"))
    if tree[0] in {'Macedonian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0bjv6'"))
    if tree[0] in {'Malian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04v09'"))
    if tree[0] in {'Mongolian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04w8f'"))
    if tree[0] in {'Mauritanian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04vjh'"))
    if tree[0] in {'Maltese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04v3q'"))
    if tree[0] in {'Mauritian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04vs9'"))
    if tree[0] in {'Maldivan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04ty8'"))
    if tree[0] in {'Malawian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04tr1'"))
    if tree[0] in {'Mozambican'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04wlh'"))
    if tree[0] in {'Namibian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05bmq'"))
    if tree[0] in {'Nigerien'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05cc1'"))
    if tree[0] in {'Nigerian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05cgv'"))
    if tree[0] in {'Nicaraguan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05c74'"))
    if tree[0] in {'Nepalese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/016zwt'"))
    if tree[0] in {'Nauruan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05br2'"))
    if tree[0] in {'Omani'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05l8y'"))
    if tree[0] in {'Panamanian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05qx1'"))
    if tree[0] in {'Peruvian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/016wzw'"))
    if tree[0] in {'French Polynesian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02wzv'"))
    if tree[0] in {'Papua New Guinean'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05qkp'"))
    if tree[0] in {'Puerto Rican'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05r7t'"))
    if tree[0] in {'Portuguese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05r4w'"))
    if tree[0] in {'Paraguayan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05v10'"))
    if tree[0] in {'Qatari'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0697s'"))
    if tree[0] in {'Romanian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06c1y'"))
    if tree[0] in {'Rwandan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06dfg'"))
    if tree[0] in {'Saudi', 'Saudi Arabian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01z215'"))
    if tree[0] in {'Solomon Islander'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01n8qg'"))
    if tree[0] in {'Seychellois'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06sw9'"))
    if tree[0] in {'Sudanese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06tw8'"))
    if tree[0] in {'Slovene', 'Slovenian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06t8v'"))
    if tree[0] in {'Sierra Leonean'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06s_2'"))
    if tree[0] in {'Sammarinese', 'San Marinese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06sff'"))
    if tree[0] in {'Senegalese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06srk'"))
    if tree[0] in {'Somali'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06tgw'"))
    if tree[0] in {'Surinamer'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06nnj'"))
    if tree[0] in {'Salvadoran'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02k8k'"))
    if tree[0] in {'Syrian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06vbd'"))
    if tree[0] in {'Swazi'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06v36'"))
    if tree[0] in {'Chadian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01p1b'"))
    if tree[0] in {'Togolese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/07f5x'"))
    if tree[0] in {'Tajik', 'Tadzhik'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/07dvs'"))
    if tree[0] in {'Turkmen(s)'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01c4pv'"))
    if tree[0] in {'Tunisian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/07fj_'"))
    if tree[0] in {'Tongan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/07fb6'"))
    if tree[0] in {'Trinidadian', 'Tobagonian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/09lxtg'"))
    if tree[0] in {'Tuvaluan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/07fsv'"))
    if tree[0] in {'Tanzanian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/07dzf'"))
    if tree[0] in {'Ukrainian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/07t21'"))
    if tree[0] in {'Ugandan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/07tp2'"))
    if tree[0] in {'Uruguayan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/07twz'"))
    if tree[0] in {'Uzbek', 'Uzbekistani'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/07t_x'"))
    if tree[0] in {'none'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/07ytt'"))
    if tree[0] in {'Vietnamese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01crd5'"))
    if tree[0] in {'Ni-Vanuatu'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/07z5n'"))
    if tree[0] in {'Yemeni', 'Yemenite'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01z88t'"))
    if tree[0] in {'Zambian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/088vb'"))
    if tree[0] in {'Zimbabwean'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/088q4'"))
    if tree[0] in {'Burmese', 'Myanmarese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/04xn_'"))
    if tree[0] in {'Montenegrin'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/056vv'"))
    if tree[0] in {'Palauan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05tr7'"))
    if tree[0] in {'Northern Irish'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05bcl'"))
    if tree[0] in {'Scottish'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06q1r'"))
    if tree[0] in {'Welsh'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0j5g9'"))
    if tree[0] in {'Samoan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06s9y'"))
    if tree[0] in {'Congolese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/088xp'"))
    if tree[0] in {'East Timorese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02lx0'"))
    if tree[0] in {'Yugoslavian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/087vz'"))
    if tree[0] in {'Dutch'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/049nq'"))
    if tree[0] in {'Gabonese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03548'"))
    if tree[0] in {'Spartan'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/09472'"))
    if tree[0] in {'Palestinian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0604m'"))
    if tree[0] in {'Palestinian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0h44w'"))
    if tree[0] in {'Taiwanese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06f32'"))
    if tree[0] in {'Hungarian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03l5m1'"))
    if tree[0] in {'Roman'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03gk2'"))
    if tree[0] in {'British'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/014tss'"))
    if tree[0] in {'Macedonian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0bk25'"))
    if tree[0] in {'English'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/024pcx'"))
    if tree[0] in {'Roman'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06cmp'"))
    if tree[0] in {'Ottoman'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05kyr'"))
    if tree[0] in {'South African'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0c4b8'"))
    if tree[0] in {'New Guinean'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/09wfqp'"))
    if tree[0] in {'Rhodesian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06jnv'"))
    if tree[0] in {'Roman'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06frc'"))
    if tree[0] in {'Polish'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03pn9'"))
    if tree[0] in {'French'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0gtzp'"))
    if tree[0] in {'Yugoslavian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/018j0w'"))
    if tree[0] in {'Italian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05jt5h'"))
    if tree[0] in {'Irish'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/016jz3'"))
    if tree[0] in {'Western Roman'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02jbz2'"))
    if tree[0] in {'Spanish'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01s47p'"))
    if tree[0] in {'Bohemian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0410vqb'"))
    if tree[0] in {'Mongolian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01jv68'"))
    if tree[0] in {'Rhodesian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01ptlk'"))
    if tree[0] in {'German'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03b79'"))
    if tree[0] in {'Aragonian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02srrt'"))
    if tree[0] in {'Athenian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03nmzqx'"))
    if tree[0] in {'Albanian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06857n'"))
    if tree[0] in {'Hawaiian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/019kzh'"))
    if tree[0] in {'Czechoslovakian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05yt6l'"))
    if tree[0] in {'Prussian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01k6y1'"))
    if tree[0] in {'Confederate'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/020d5'"))
    if tree[0] in {'Romanian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01rdm0'"))
    if tree[0] in {'Serbian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06swt'"))
    if tree[0] in {'Palestinian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0nyg5'"))
    if tree[0] in {'Austrasia'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0gytv'"))
    if tree[0] in {'Sicilian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02zqdb'"))
    if tree[0] in {'Soviet'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05vz3zq'"))
    if tree[0] in {'Byzantine'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/017cw'"))
    if tree[0] in {'Iraqi'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02p717m'"))
    if tree[0] in {'Austrian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01nhhz'"))
    if tree[0] in {'Soviet'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01mzwp'"))
    if tree[0] in {'Italian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02psqkz'"))
    if tree[0] in {'German'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01qlyt'"))
    if tree[0] in {'Japanese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0193qj'"))
    if tree[0] in {'Bulgarian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03bxbql'"))
    if tree[0] in {'Hawaiian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01hlvc'"))
    if tree[0] in {'Hungarian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02rnb5c'"))
    if tree[0] in {'French'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01flgk'"))
    if tree[0] in {'Swedish'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01fvhp'"))
    if tree[0] in {'Chechen'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0dfrl8'"))
    if tree[0] in {'Dutch'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0dv0z'"))
    if tree[0] in {'Welsh'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0576g9'"))
    if tree[0] in {'Bavarian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02vkbz_'"))
    if tree[0] in {'Emirian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0c75f'"))
    if tree[0] in {'French'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0152tq'"))
    if tree[0] in {'Serbian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/025scy1'"))
    if tree[0] in {'Yugoslavian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01hs96'"))
    if tree[0] in {'Serbian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0821k6'"))
    if tree[0] in {'Greek'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/088q1s'"))
    if tree[0] in {'Babylonian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0cn3b'"))
    if tree[0] in {'Sicilian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0bd46l'"))
    if tree[0] in {'Brazilian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01nr2h'"))
    if tree[0] in {'Zairian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0k5vl'"))
    if tree[0] in {'French'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0cn_tpv'"))
    if tree[0] in {'South Sudanese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/05rznz'"))
    if tree[0] in {'Zulu'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/03gwrmk'"))
    if tree[0] in {'Croatian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/025scyf'"))
    if tree[0] in {'Portuguese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0285m87'"))
    if tree[0] in {'French'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01fmy9'"))
    if tree[0] in {'Roman'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/06gb8'"))
    if tree[0] in {'English'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0210n'"))
    if tree[0] in {'Burmese'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/027g22f'"))
    if tree[0] in {'Polish'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/02z1d_'"))
    if tree[0] in {'Kirghiz', 'Kyrgyz'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/0jt3tjf'"))
    if tree[0] in {'Palestinian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01k0p4'"))
    if tree[0] in {'Prussian'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/020g9r'"))
    if tree[0] in {'Saxon'}: results.append(TypedMeaning(types={'/location/country'}, sem="'name': null, 'mid': '/m/01n45v'"))

    # =========================================================================
    # End Auto-Generated Adj Interpretation Rules
    # =========================================================================

    return results

def N(tree):
    results = []

    # Add all interpretations from the noun table.
    if tree[0] in lexicon.N_table:
        for sense in lexicon.N_table[tree[0]]:
            sem = "'mid': null, 'name': null, 'type': '%s'" % sense
            results.append(TypedMeaning(types={sense}, sem=sem))
        if not lexicon.N_table[tree[0]]:
            sem = "'mid': null, 'name': null"
            results.append(TypedMeaning(types=set(), sem=sem))

    # Add handwritten noun rules.
    # (Eventually put these into the noun table in a separate module.)
    if tree[0] in {'author', 'authors'}: results.append(TypedMeaning(
            types={'/book/author'},
            sem="'mid': null, 'name': null, 'type': '/book/author'",
            reln='author'))
    if tree[0] in {'child', 'children', 'kid', 'kids'}:
        results.append(TypedMeaning(types={'/people/person'},
                sem="'mid': null, 'name': null", reln='child'))
    if tree[0] in {'man', 'men'}: results.append(TypedMeaning(
            types={'/people/person'},
            sem="'mid': null, 'name': null, 'type': '/people/person', '/people/person/gender': [{ 'mid': '/m/05zppz' }]"))
    if tree[0] in {'mayor', 'mayors'}: results.append(TypedMeaning(
            types={'/government/politician'},
            sem="'mid': null, 'name': null, '!/government/government_position_held/office_holder': [{ '/government/government_position_held/jurisdiction_of_office': [{ 'name': null, 'mid': null }], '/government/government_position_held/basic_title': [{ 'name': 'Mayor' }] }]",
            reln='mayor'))
    if tree[0] in {'novel', 'novels'}: results.append(TypedMeaning(
            types={'/book/book'},
            sem="'mid': null, 'name': null, 'type': '/book/book', '/book/book/genre': [{ 'mid': '/m/05hgj' }]"))
    if tree[0] in {'woman', 'women'}: results.append(TypedMeaning(
            types={'/people/person'}, sem="'mid': null, 'name': null, 'type': '/people/person', '/people/person/gender': [{ 'mid': '/m/02zsn' }]"))

    return results
