"""Define how to present Freebase responses in user-friendly format."""

import re
import HTMLParser
import random
from lexicon.lexicon import prop_table

seen_anywhere = []

def present_response(response, query, max_per_level=10, indent=0, link="",
                     shallow=False):
    """Takes a Freebase query response as JSON and prints out the relevant
    parts of the response.

    response -- JSON object getting printed.
    query -- Input query for which Freebase gave this response.
    max_per_level -- Maximum elements to print per level.
    indent -- How far to indent this level (based on higher levels).
    link -- Name of parent property linking to this part of the response.
    shallow -- Print at most one name, then stop.
    
    Finds all 'name':___ results.
    Ignores cases like 'name~=':Canada', 'name':'Canada'.
    Catches cases like 'name~=':Obama', 'name':'Barack Obama'.
    Makes sure the original input query had 'name':None, rather than 
    'name':'Canada'
    """

    # Sort response list so differently ordered identical queries get caught as
    # identical.  Note this won't currently catch cases where an embedded list
    # is ordered differently.
    check_seen = response
    if isinstance(response, list):
        check_seen = sorted(response)
    if check_seen not in seen_anywhere:
        seen_anywhere.append(check_seen)

    # Randomize list order to get an interesting range of results.
    if isinstance(response, list):
	random.shuffle(response)
	response = sorted(response[:max_per_level],
		key=lambda x: x['name'] if 'name' in x else 0)

    next_indent = indent
    if 'name' in response: next_indent += 3

    name_output = ""
    daughter_output = ""
    element_num = 0
    seen_sister = []

    for element in response:
        if shallow and 'name' in response and element != 'name': continue

        if isinstance(element, basestring):  # Element is a dict key. 
            if element == 'name':
                name = response[element]
                if not name: name = '<no name>'
                html_parser = HTMLParser.HTMLParser()
                name = html_parser.unescape(name)
                print_link = link
                name_output = ' '*indent + print_link + name + '\n'
                if len(name_output) > 79:
                    name_output = name_output[:75] + ' ...\n'
                if shallow: break  # Printed a name, skip further material.
            elif not isinstance(response[element], basestring):
                m = re.search('/.*$', element)
                prop = m.group(0)
                next_link = prop_table[prop]  # Look up English name for prop.
                if '!' in element: next_link = '<- ' + next_link + ' <- '
                else: next_link = next_link + ': '
                daughter_output += present_response(response[element],
                        query[element], max_per_level, next_indent, next_link,
                        shallow)
        else:  # Element is a non-string list member.
            if element not in seen_sister:
                seen_sister.append(element)
                if element_num == max_per_level: break
                if element in seen_anywhere:
                    daughter_output += present_response(element, query[0],
                            max_per_level, indent, link, shallow=True)
                else:
                    daughter_output += present_response(element, query[0],
                            max_per_level, indent, link, shallow)

        element_num += 1

    return name_output + daughter_output
