"""A general method for querying out to Freebase."""

from __future__ import print_function

import json
import urllib
import codecs
import locale
import sys
import time

# Wrap sys.stdout into a StreamWriter to allow writing unicode.
sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout) 

api_key = open(".freebase_api_key").read()
service_url = 'https://www.googleapis.com/freebase/v1/mqlread'

# =============================================================================
def freebase_query(query, all=False, verbose=False):
    """Return the results of running a Freebase query.
    If all is set, repeats the query using a cursor to get all results.
    Otherwise, results beyond limit (around 100 by default?) are cut off.
    """
# =============================================================================

    if verbose: sys.stderr.write('Querying Freebase: ')

    results = []
    cursor = ''

    while True:

        params = {
            'query': json.dumps(query),
            'key': api_key,
            'cursor': cursor
        }

        url = service_url + '?' + urllib.urlencode(params)

        time.sleep(0.1)
        if verbose: sys.stderr.write('(')
        response = json.loads(urllib.urlopen(url).read())
        if verbose: sys.stderr.write(')')

        if 'cursor' in response: cursor = response['cursor']
        else:
            if verbose: sys.stderr.write('\nError!\n')
            if verbose: sys.stderr.write('Parameters: %s\n' % params)
            return response  # Return complete response, containing error.

        results += response['result']

        if (not all) or (not cursor): break

    if verbose: sys.stderr.write('\n')

    return results
