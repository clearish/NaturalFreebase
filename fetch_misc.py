"""Queries Freebase for information about types and the metaschema, and prints
it out in readable from.
"""

from __future__ import print_function

import re

from freebase_query import freebase_query

# =============================================================================
def print_types():
    """Queries Freebase for info about types and prints it out."""
# =============================================================================

    # For all types in /commons and /system, look up:
    #    name, id, (strictly) included types, number of instances.
    # Note, this discards any types with no instances.  Currently there's 65.
    # To see them, change to...
    #   'instance': [{ 'optional': 'forbidden', 'name': None }]

    query = [{
        'domain': { 'id': None, '/freebase/domain_profile/category': {
            'id|=': [ '/category/commons', '/category/system' ],
            'id': None } },
        'type': '/type/type', 'id': None, 'name': None,
        '/common/topic/alias': [{ 'lang': '/lang/en', 'value': None,
                                  'optional': 'optional' }],
        'properties': [{ 'name': None, 'id': None }],
        '/freebase/type_profile/property_count': None,
        '/freebase/type_profile/strict_included_types': [],
        '/freebase/type_hints/included_types': [],
        '/freebase/type_hints/minor': None,
        '/freebase/type_hints/mediator': None,
        '/freebase/type_hints/enumeration': None,
        '/freebase/type_hints/deprecated': None,
        '/freebase/type_hints/never_assert': None,
        'instance': { 'return': 'estimate-count' },
        'sort': '-instance.estimate-count'
    }]

    response = freebase_query(query, all=True, verbose=True)
    for type in response:
        print('ID: ' + str(type['id']))
        print('  Name: ' + str(type['name']))
        for alias in type['/common/topic/alias']:
            print('  Alias: ' + alias['value'])
        print('  Instances: ~' + str(type['instance']))
        print('  Minor: ' + str(type['/freebase/type_hints/minor']))
        print('  Mediator: ' + str(type['/freebase/type_hints/mediator']))
        print('  Enumeration: '
              + str(type['/freebase/type_hints/enumeration']))
        print('  Deprecated: ' + str(type['/freebase/type_hints/deprecated']))
        print('  Never Assert: '
              + str(type['/freebase/type_hints/never_assert']))
        for included in type['/freebase/type_profile/strict_included_types']:
            print('  Strictly Includes: ' + str(included))
        for included in type['/freebase/type_hints/included_types']:
            print('  Loosely Includes: ' + str(included))
        print('  Property Count: '
              + str(type['/freebase/type_profile/property_count']))
        for property in type['properties']:
            print('  Property: ' + property['id'] + ' "' + property['name']
                  + '"')  # str() breaks on utf8 names

# =============================================================================
def print_metaschema():
    """Queries Freebase for all metaschema structure and prints it out."""
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
    for predicate in response:
        print('Predicate: ' + str(predicate['name']))
        print('Operand: ' + str(predicate['search_filter_operand']))
        for path in predicate['paths']:
            path_id_long = path['id']
            # Cut off "/base/fbontology/metaschema/path_id/".
            path_id = re.search('/[^/]*$', path_id_long).group(0) 
            print('  Path: ' + path_id)
            index = 0
            for property in path['properties']:  # Already sorted by index.
                print('    Prop ' + str(index) + ': ' + str(property['id']))
                print('      Type: '
                      + str(property['/type/property/expected_type']))
                print('      Master: '
                      + str(property['/type/property/master_property']))
                print('      Reverse: '
                      + str(property['/type/property/reverse_property']))
                print('      Unique: '
                      + str(property['/type/property/unique']))
                print('      Schema: '
                      + str(property['/type/property/schema']))
                print('      Unit: '
                      + str(property['/type/property/unit']))
                index += 1

# =============================================================================

# print_types()
# print_metaschema()
