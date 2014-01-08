"""Functions to query Freebase for the English words for types, properties,
metaschema relations, countries adjectives, ethnicities, etc. and print out
tables taking these words to their meanings.  (Or in the case of the type and
property tables, from Freebase meanings to English words).
"""

from __future__ import print_function

import re
import json
import inflect
import pprint

from freebase_query import freebase_query

def format_name(name, force_ascii=True, lowercase=True,
                back_to_forward_slash=True, underscore_to_space=True,
                no_quotes=True, no_commas=True):
    if force_ascii:
        name = name.encode('ascii', 'ignore')
    if lowercase:
        name = name.lower()
    if back_to_forward_slash:
        name = re.sub('\\\\', '/', name)
    if underscore_to_space:
        name = re.sub('_', ' ', name)
    if no_quotes:
        name = re.sub("'", '', name)
    # Commas seem to break NLTK (in Adj rule, they were causing trouble).
    if no_commas:
        name = re.sub(',', '', name)
    return name

# =============================================================================
def print_noun_table():
    """Print table mapping English nouns to Freebase types."""
# =============================================================================

    # For all types in /commons and /system, look up:
    #    name, id, (strictly) included types, number of instances.
    # Note, this will discard any types with no instances.
    # Currently there's 65.
    # To see them, change to...
    #    'instance': [{ 'optional': 'forbidden', 'name': None }]
    query = [{
        'domain': { 'id': None, '/freebase/domain_profile/category': {
            'id|=': [ '/category/commons', '/category/system' ],
            'id': None } },
        'type': '/type/type', 'id': None, 'name': None,
        '/common/topic/alias': [{ 'lang': '/lang/en', 'value': None,
                                  'optional': 'optional' }],
        '/freebase/type_profile/strict_included_types': [],
        '/freebase/type_hints/included_types': [],
        'instance': { 'return': 'estimate-count' },
        'sort': '-instance.estimate-count'
    }]

    response = freebase_query(query, all=True, verbose=True)

    print('"""This is an auto-generated file mapping an English noun to\n'
          '(potentially multiple) Freebase type interpretations.\n'
          '"""\n')
    print('# ===== Noun Table =====')
    print('table = \\')

    infl = inflect.engine()  # For making plurals.

    table = {}
    for type in response:
        id = str(type['id'])
        names = [type['name']] + \
                [ alias['value'] for alias in type['/common/topic/alias'] ]
        for name in names:
            name = format_name(name)
            for inflected in (name, infl.plural_noun(name)):
                if inflected not in table: table[inflected] = {id}
                else: table[inflected] |= {id}

    pprint.pprint(table)

# =============================================================================
def print_type_table():
    """Print table mapping Freebase types to English nouns."""
# =============================================================================

    # Same query as for noun table.
    query = [{
        'domain': { 'id': None, '/freebase/domain_profile/category': {
            'id|=': [ '/category/commons', '/category/system' ],
            'id': None } },
        'type': '/type/type', 'id': None, 'name': None,
        '/common/topic/alias': [{ 'lang': '/lang/en', 'value': None,
                                  'optional': 'optional' }],
        '/freebase/type_profile/strict_included_types': [],
        '/freebase/type_hints/included_types': [],
        'instance': { 'return': 'estimate-count' },
        'sort': '-instance.estimate-count'
    }]

    response = freebase_query(query, all=True, verbose=True)

    print('"""This is an auto-generated file mapping a Freebase type to a\n'
          'canonical name for that type.\n'
          '"""\n')
    print('# ===== Type Table =====')
    print('table = \\')

    table = {}
    for type in response:
        id = str(type['id'])
        table[id] = format_name(type['name'])

    pprint.pprint(table)

# =============================================================================
def print_property_table():
    """Print table mapping Freebase properties to English."""
# =============================================================================

    query = [{
        'schema': {
            'domain': { 'id': None, '/freebase/domain_profile/category': {
                'id|=': [ '/category/commons', '/category/system' ],
                'id': None } } },
        'type': '/type/property', 'id': None, 'name': None
    }]

    response = freebase_query(query, all=True, verbose=True)

    print('"""This is an auto-generated file mapping a Freebase property to\n'
          'a canonical English equivalent.\n'
          '"""\n')
    print('# ===== Property Table =====')
    print('table = \\')

    prop_table = {}
    for property in response:
        if property['name']:
            prop_table[str(property['id'])] = \
                    format_name(property['name'])

    pprint.pprint(prop_table)

# =============================================================================
def print_metaschema_table():
    """Print table mapping each Freebase metaschema relation onto a list of
    triples (S_type, O_type, path).
    """
# =============================================================================

    query = [{
        'type': '/base/fbontology/semantic_predicate',
        'name': None,
        'search_filter_operand': None,
        'paths': [{
            'id': None,
            'properties': [{
                'id': None,
                'index': None,
                '/type/property/expected_type': None,
                '/type/property/master_property': None,
                '/type/property/reverse_property': None,
                '/type/property/unique': None,
                '/type/property/schema': None,
                '/type/property/unit': None,
                'sort': 'index' }]
        }]
    }]

    response = freebase_query(query, all=True, verbose=True)

    print('"""This is an auto-generated file mapping a Freebase metaschema\n'
          "predicate to a list of tuples:\n\n"
          "    (S_type, O_type, path)\n\n"
          "... where 'S_type' and 'O_type' are the types of the predicate's\n"
          "subject and object (on that interpretation), and 'path' is a list\n"
          "of Freebase property links you have to traverse (in order) to get\n"
          "from subjects of the relevant type to objects of the relevant\n"
          "type, related by the predicate.\n"
          '"""\n')
    print('# ===== Metaschema Table =====')
    print('table = \\')

    table = {}
    for predicate in response:
        operand = str(predicate['name'])
        table[operand] = []
        for path in predicate['paths']:
            properties_json = path['properties']  # Already sorted by index.
            first_type = str(properties_json[0]['/type/property/schema'])
            # For length one path, this is the same property.
            last_type = str(properties_json[-1] \
                                           ['/type/property/expected_type'])
            # Skip cases where schema or expected_type aren't defined.
            if first_type == 'None' or last_type == 'None': continue
            # Skip cases referring to '/base/'
            if '/base/' in first_type + last_type: continue
            properties = [str(prop['id']) for prop in properties_json]
            table[operand].append((first_type, last_type, properties))

    pprint.pprint(table)

# =============================================================================
def print_country_table():
    """Print table mapping adjectives onto countries."""
# =============================================================================

    query = [{
        'type': '/location/country',
        'name': None,
        'mid': None,
        '/location/location/adjectival_form': [{ 'lang': '/lang/en',
                'value': None, 'optional': 'optional' }],
    }]
    
    response = freebase_query(query, all=True, verbose=True)

    print('"""This is an auto-generated file mapping a country adjective\n'
          "like 'Canadian' onto a set of IDs of countries denoted\n"
          "(typically one).\n"
          '"""\n')
    print('# ===== Adjective Country Table =====')
    print('table = \\')

    adj_table = {}
    for country in response:
        adjs = country['/location/location/adjectival_form']
        for adj in adjs:
            adj_fmt = format_name(adj['value'], lowercase=False)
            if adj_fmt.lower() == 'none': continue
            if adj_fmt not in adj_table: adj_table[adj_fmt] = set()
            adj_table[adj_fmt] |= { str(country['mid']) }

    pprint.pprint(adj_table)

# =============================================================================
def print_ethnicity_table():
    """Print Freebase ethnicity info as table and rules."""
# =============================================================================

    query = [{
        'type': '/people/ethnicity',
        'name': None,
        '/common/topic/alias': [{ 'lang': '/lang/en', 'value': None,
                                  'optional': 'optional' }],
        'people': { 'return': 'count' },
        'sort': '-people.count'
    }]

    response = freebase_query(query, all=True, verbose=True)
