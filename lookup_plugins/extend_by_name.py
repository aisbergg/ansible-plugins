# MIT License
#
# Copyright (c) 2021 Andre Lehmann
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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = '''
lookup: extend_by_name
author: Andre Lehmann <aisberg@posteo.de>
short_description: extends lists or mappings by variables found by a name prefix
description:
    - The extend_by_name lookup looks for variables by a name prefix and uses them to extend the given default value.
options:
    _terms:
        description: default value and variable prefix
        required: True
    default:
        description: default value that should be extended
        required: True
    prefix:
        description: prefix of variable names that should be used to extend the default value
        required: True
    recursive:
        description: merge dictionaries recursively
        type: boolean
        default: False
    list_merge:
        description: method to merge lists inside dictionaries
        default: replace
        type: string
        choices: ['replace', 'keep', 'append', 'prepend', 'append_rp', 'prepend_rp']
notes:
    - Requires Ansible >= 2.10
'''

EXAMPLES = '''
# defining variables with prefix '_myvar' somewhere will result in
_myvar_foo: [foo]
_myvar_bar: [bar]
_myvar_baz: [baz]
myvar: "{{ lookup('extend_by_name', [], '_myvar') }}"  # -> [foo, bar, baz]


# a dictionary that contains some distribution dependent values
myvar: "{{
    {'a': 1, 'b': foo} if ansible_distribution == 'Debian' else
    {'a': 2, 'b': bar} if ansible_distribution == 'CentOS' and ansible_distribution_major_version == '8' else
    {'a': 1, 'b': baz}
}}"
# can be replaced by:
_myvar_default: {'a': 1, 'b': baz}
_myvar_debian: {'b': bar}
_myvar_centos_8: {'a': 2, 'b': bar}
myvar: "{{ lookup('extend_by_name', [], '_myvar', recursive=True) }}"
'''

RETURN = '''
_raw:
  description:
    - the default value extended by variables found by a name prefix
'''

from distutils.util import strtobool

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.splitter import parse_kv
from ansible.plugins.lookup import LookupBase
from ansible.template import Templar
from ansible.utils.vars import merge_hash

__version__ = '1.0.0'
__license__ = 'MIT'
__email__ = 'aisberg@posteo.de'


class LookupModule(LookupBase):

    def _parse_parameters(self, args, kwargs):
        params = {
            'default': kwargs.get('default', None),
            'prefix': kwargs.get('prefix', None),
            'recursive': kwargs.get('recursive', None),
            'list_merge': kwargs.get('list_merge', None),
        }
        unknown_args = set(kwargs.keys()) - set(params.keys())
        if unknown_args:
            raise AnsibleParserError("Unsupported parameter passed to extend_by_name lookup: {}".format(
                ", ".join(unknown_args)))

        if len(args) > 0 and not params['default']:
            params['default'] = args[0]
        if len(args) > 1 and not params['prefix']:
            params['prefix'] = args[1]
        if len(args) > 2 and not params['recursive']:
            params['recursive'] = args[2]
        if len(args) > 3 and not params['list_merge']:
            params['list_merge'] = args[3]

        if params['default'] is None:
            raise AnsibleParserError("Missing default value")
        if not isinstance(params['default'], (list, dict)):
            raise AnsibleParserError("Default value must be of type list or dict")

        if params['recursive']:
            params['recursive'] = bool(strtobool(params['recursive']))
        else:
            params['recursive'] = False

        if not params['list_merge']:
            params['list_merge'] = 'replace'

        return params

    def run(self, terms, variables=None, **kwargs):
        variables = variables or {}
        params = self._parse_parameters(terms, kwargs)

        ret = params['default']
        prefix = params['prefix']
        recursive = params['recursive']
        list_merge = params['list_merge']

        # for rendering contained templates recursively
        loader = DataLoader()
        templar = Templar(loader, variables=variables)

        matching_vars = [name for name in sorted(variables.keys()) if name.startswith(prefix)]
        for name in matching_vars:
            value = templar.template(variables[name])

            if isinstance(ret, list):
                if not isinstance(value, list):
                    raise ValueError("Value type of '{}' must be 'list', same as the default value".format(name))
                ret = ret + value
            elif isinstance(ret, dict):
                if not isinstance(value, list):
                    raise ValueError("Value type of '{}' must be 'dict', same as the default value".format(name))
                ret = merge_hash(ret, value, recursive, list_merge)

        return [ret]
