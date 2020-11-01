# MIT License
#
# Copyright (c) 2020 Andre Lehmann
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
lookup: keepass_http_password
author: Andre Lehmann <aisberg@posteo.de>
short_description: retrieve a password from an opened KeePass database
description:
    - Retrieves a password from an opened KeePass database using the KeePass HTTP protocol.
options:
    _terms:
        description:
           - an url identifying the password
        required: True
        aliases: [ url ]
    required: True
    name:
        description:
            - a name identifying the password
    login:
        description:
            - a login name that is associated with the password entry
notes:
    - When first querying a password, an association needs to be formed with an opened KeePass database. This means,
      a window of KeePass will pop up and ask for an association name. Once the association is formed and stored in a
      file called C(.keepass-assoc), the lookup will try to retrieved the given password.
    - Due to the nature of the KeePass protocol, a password is queried using an url. This might lead to multiple
      passwords being found. Therefore to uniquely identify a password the parameters C(name), and C(login) can be used
      to trim down the results.
    - The plugin configuration can be controlled by defining variables in Ansible. Following variables affect the
      plugins behavior:
        - C(keepass_http_password_url): KeePass HTTPPass plugin connection URL (default: http://localhost:19455/)
        - C(keepass_http_password_state_file): Name of the state file (default: C(.keepass-assoc))
'''

EXAMPLES = '''
- name: create a mysql user with a password retrieved from KeePass db
  mysql_user:
    name: myuser
    password: "{{ lookup('keepass_http_password', 'url=https://mysql-root login=myuser') }}"
'''

RETURN = '''
_raw:
  description:
    - a password
'''

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display
from ansible.parsing.splitter import parse_kv

from requests.exceptions import ConnectionError

try:
    from keepasshttp import KeePassHTTP, KeePassHTTPException
    KEEPASS_HTTP_MODULE_AVAILABLE = True
except ImportError:
    KEEPASS_HTTP_MODULE_AVAILABLE = False

__version__ = '1.2.0'
__license__ = 'MIT'
__email__ = 'aisberg@posteo.de'

display = Display()


class KeePassHTTPPasswordLookup(object):

    STATE_FILE_DEFAULT = '.keepass-assoc'
    URL_DEFAULT = 'http://localhost:19455/'

    def __init__(self, state_file=None, url=None):
        self._state_file = state_file or self.STATE_FILE_DEFAULT
        self._url = url or self.URL_DEFAULT

        self._connection = None
        # cache for password lookups
        self._cache = {}

        self._open_connection()

    def _open_connection(self):
        if not self._connection:
            self._connection = KeePassHTTP(storage=self._state_file, url=self._url)
            try:
                self._connection._load()
            except ConnectionError:
                raise ConnectionError(
                    "Failed to establish a connection to KeePass. Check if KeePass is running actually.")
            except KeePassHTTPException as ex:
                raise KeePassHTTPException("Failed to establish a connection to KeePass database: {}".format(str(ex)))

    def lookup(self, url, filters=None):
        filters = filters or {}

        # lookup from cache
        cache_key = str({'url': url, **filters})
        if cache_key in self._cache:
            return self._cache[cache_key]

        # lookup from KeePass
        logins = self._connection.search(url, sort_keys=True)
        if not logins:
            raise LookupError("No password found for url '{}'".format(url))

        # use filters to trim down result list
        if filters:
            for login in logins:
                for k, v in filters.items():
                    if v != getattr(login, k):
                        break
                else:
                    return login.password

            raise LookupError("No password found for {}".format(cache_key))

        # get password for given url
        return logins[0].password


class LookupModule(LookupBase):

    def _parse_parameters(self, term):
        if isinstance(term, str):
            params = parse_kv(term)
        elif isinstance(term, dict):
            params = term
        else:
            raise AnsibleParserError("Unsupported parameter type '{}' passed to keepass_http_password lookup.".format(
                type(term)))

        url = params.get('url', None)

        if '_raw_params' in params:
            if not url:
                url = ''.join((params['_raw_params']))
            del params['_raw_params']

        if not url:
            raise AnsibleParserError("Missing 'url' parameter for keepass_http_password lookup")

        # check for invalid parameters
        valid_params = frozenset(('url', 'name', 'login'))
        invalid_params = frozenset(params.keys()).difference(valid_params)
        if invalid_params:
            raise AnsibleParserError("Unrecognized parameter(s) given to keepass_http_password lookup: {}".format(
                ', '.join(invalid_params)))

        if 'url' in params:
            del params['url']
        filters = params

        return url, filters

    def run(self, terms, variables=None, **kwargs):
        if not KEEPASS_HTTP_MODULE_AVAILABLE:
            raise AnsibleError("The keepasshttp module is required to use the keepass_http_password lookup plugin")

        variables = variables or {}
        kp_state_file = variables.get('keepass_http_password_state_file', KeePassHTTPPasswordLookup.STATE_FILE_DEFAULT)
        kp_url = variables.get('keepass_http_password_url', KeePassHTTPPasswordLookup.URL_DEFAULT)

        try:
            lookup = KeePassHTTPPasswordLookup(state_file=kp_state_file, url=kp_url).lookup
        except Exception as ex:
            raise AnsibleError(str(ex)) from ex

        ret = []
        for term in terms:
            url, filters = self._parse_parameters(term)
            req = {'url': url, **filters}
            display.vvvv("keepass_http_password: Lookup {}".format(str(req)))

            # now lookup the password
            try:
                ret.append(lookup(url=url, filters=filters))
            except Exception as ex:
                raise AnsibleError(str(ex)) from ex

        return ret
