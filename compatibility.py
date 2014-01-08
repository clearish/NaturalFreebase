"""Define the compatibile() function, which calculates the compatibility
between two sets of types, given complete pairwise type intersection
information from compatibility_matrix.
"""

from __future__ import division

from compatibility_matrix import compatibility

DEBUG = False

# =============================================================================
def compatible(types1, types2):
    """
    Check if the union of two sets of types is internally pairwise compatible.
    If compatible, return a rough measure of (an upper bound) on how good the
    "Fit" is between the two sets.  In other words, given that the object is
    already in the intersection of types1, how likely is it to also be in the
    intersection of types2 (and vice versa)?  A simple formula that works
    fairly well is:

    smallest pairwise intersect of types1 union types2 /
        min(smallest pairwise intersect(types1),
                smallest pairwise intersect(types2))

    To help discourage the system from interpreting (to take just one example)
    'books about sports by athletes' as "books that are blogs about sports and
    are also quotations by athletes", it helps to increase the "fit" when the
    denominator in the equation above is large.  For example, use:
    
    (top / bottom) ** (1 / bottom ** 0.2)
    """
# =============================================================================

    if DEBUG: print("Compatible(%s, %s)" % (types1, types2))

    def estimate_instances(types):
        running_min = 1000000000 # billion
        for t1 in types:
            if t1 not in compatibility: return 0
            for t2 in types:
                if t2 not in compatibility[t1]: return 0
                running_min = min(running_min, compatibility[t1][t2])
        return running_min
                
    top = estimate_instances(types1 | types2)
    bottom = min(estimate_instances(types1), estimate_instances(types2))
    if bottom == 0: return 0

    if DEBUG: print("= %d / %d" % (top, bottom))

    # The "** (1 / bottom ** N)" biases toward large denominators.
    return (top / bottom) ** (1 / bottom ** 0.2)

# =============================================================================
def test_formula():
    """This is just a way to get a sense of how different formulae work."""
# =============================================================================
    for top in (1, 5, 50, 500):
        for bottom in (1, 2, 10, 100, 1000, 10000, 100000, 1000000, 10000000):
            if top > bottom: continue
            print("%d / %d --> %.4f"
                  % (top, bottom, (top / bottom) ** (1 / bottom ** 0.3)))
