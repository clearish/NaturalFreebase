"""Define classes for use in a predicate table."""

class PredicateSense:
    """A single interpretation of a conceptual predicate.  For example, one
    PredicateSense of 'PartOf' would represent the interpretation that book X 
    X occurs within book series Y.  Other PredicatesSenses would encode other
    ways for X to be PartOf Y.

    S_type -- The Freebase type imposed on the subject of this particular
            interpretation of the conceptual predicate.
    O_type -- Same for object.
    path -- A list of Freebase property links that you have to traverse in
            order to get from subjects (of type S_type) to objects (of type
            O_type) on the relevant interpretation of the conceptual predicate.
    """

    def __init__(self, S_type, O_type, path):
        self.S_type = S_type
        self.O_type = O_type
        self.path = path

    def __repr__(self):
        return "PredicateSense(%s, %s, %s)" \
               % (repr(self.S_type), repr(self.O_type), repr(self.path))

class ConceptualPredicate:
    """Syntactic and semantics facts about a conceptual predicate.  For
    example, for the predicate 'PartOf' we know that it can be expressed by the
    preposition 'in' or the verb 'contains', and we know that 'X PartOf Y'
    holds when book X occurs within book series Y, when actor X played a role
    in movie Y, and so on.

    lexicalizations -- What words can express this predicate, and what lexical
            category are they?  Each of these words should cover every
            use/sense given in 'senses'.  Encoded as a list of tuples,
            e.g. [('P', 'about'), ('V', 'concerns')].
    senses -- A list of specific relations that instantiate this predicate's
            meaning.  For example, "person X is a member of religion Y" would
            be one of many senses of the conceptual predicate 'PartOf'.
            Encoded as a list of PredicateSenses.
    """

    def __init__(self, lexicalizations=[], senses=[]):
        self.lexicalizations = lexicalizations
        self.senses = senses

    def __repr__(self):
        return "ConceptualPredicate(%s, %s)" \
               % (self.lexicalizations, self.senses)
