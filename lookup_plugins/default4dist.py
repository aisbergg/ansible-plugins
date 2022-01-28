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
lookup: default4dist
author: Andre Lehmann <aisberg@posteo.de>
short_description: creates OS distribution dependent values
description:
    - The default4dist lookup looks for a variable by a name prefix in combination with the OS distribution or family name and returns its value. This means, you don't have to create long chains of C(ansible_distribution == 'Foo') statements to build distribution dependent values.
options:
    _terms:
        description: name prefix of the variable
        required: True
        aliases: [ prefix ]
    prefix:
        description: name prefix of the variable
        required: True
    recursive:
        description: merge dictionaries recursively
        type: boolean
        default: False
    list_merge:
        description: method to merge lists
        default: replace
        type: string
        choices: ['replace', 'keep', 'append', 'prepend', 'append_rp', 'prepend_rp']
notes:
    - Requires Ansible >= 2.10
    - The lookup will search for variables in form of C({prefix}{suffix}) or C({prefix}_{suffix}). The first found variable will be used or optional combined (dict or list) with a default value. The suffix is constructed in the following order of precedence: C({distribution}_{version}), C({distribution}_{release}), C({distribution}_{major_version}), C({distribution}), C({familiy}_{version}), C({familiy}_{release}), C({familiy}_{major_version}), C({familiy}), C(default)
    - OS distribution and family names must be specified in lower case
'''

EXAMPLES = '''
# a simple value that differs on different Linux distributions
myvar: "{{
    'foo' if ansible_distribution == 'Debian' else
    'bar' if ansible_distribution == 'CentOS' and ansible_distribution_major_version == '8' else
    'baz'
}}"
# can be replaced by:
_myvar_default: baz
_myvar_debian: foo
_myvar_centos_8: bar
myvar: "{{ lookup('default4dist', '_myvar') }}"


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
myvar: "{{ lookup('default4dist', '_myvar', recursive=True) }}"
'''

RETURN = '''
_raw:
  description:
    - a value build from a distribution variable and optional a default value
'''

from distutils.util import strtobool

from ansible.errors import AnsibleLookupError, AnsibleParserError
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.splitter import parse_kv
from ansible.plugins.lookup import LookupBase
from ansible.template import Templar
from ansible.utils.vars import merge_hash

__version__ = '2.1.0'
__license__ = 'MIT'
__email__ = 'aisberg@posteo.de'

missing = type('MissingType', (), {'__repr__': lambda x: 'missing'})()


class LookupModule(LookupBase):

    def _parse_parameters(self, args, kwargs):
        params = {
            'prefix': kwargs.get('prefix', None),
            'recursive': kwargs.get('recursive', None),
            'list_merge': kwargs.get('list_merge', None),
        }
        unknown_args = set(kwargs.keys()) - set(params.keys())
        if unknown_args:
            raise AnsibleParserError("Unsupported parameter passed to default4dist lookup: {}".format(
                ", ".join(unknown_args)))

        if len(args) > 0 and not params['prefix']:
            params['prefix'] = args[0]
        if len(args) > 1 and not params['recursive']:
            params['recursive'] = args[1]
        if len(args) > 2 and not params['list_merge']:
            params['list_merge'] = args[2]

        if params['recursive']:
            params['recursive'] = bool(strtobool(params['recursive']))
        else:
            params['recursive'] = False

        if not params['list_merge']:
            params['list_merge'] = 'replace'

        return params

    def _get_value(self, variables, prefix, suffix):
        if (prefix + suffix) in variables:
            return variables[prefix + suffix]
        if (prefix + '_' + suffix) in variables:
            return variables[prefix + '_' + suffix]
        return missing

    def run(self, terms, variables=None, **kwargs):
        variables = variables or {}
        params = self._parse_parameters(terms, kwargs)

        ret = None
        prefix = params['prefix']
        recursive = params['recursive']
        list_merge = params['list_merge']

        # for rendering contained templates recursively
        loader = DataLoader()
        templar = Templar(loader, variables=variables)

        os_distribution = variables['ansible_distribution'].lower()
        os_familiy = variables['ansible_os_family'].lower()
        os_version = variables['ansible_distribution_version'].replace('.', '_')
        os_major_version = str(variables['ansible_distribution_major_version'])
        os_release = variables['ansible_distribution_release'].lower()

        # in order of preference
        suffixes = [
            os_distribution + "_" + os_release + "_" + os_version,
            os_distribution + "_" + os_release + "_" + os_major_version,
            os_distribution + "_" + os_release,
            os_distribution + "_" + os_version,
            os_distribution + "_" + os_major_version,
            os_distribution,
            os_familiy + "_" + os_release + "_" + os_version,
            os_familiy + "_" + os_release + "_" + os_major_version,
            os_familiy + "_" + os_release,
            os_familiy + "_" + os_version,
            os_familiy + "_" + os_major_version,
            os_familiy,
        ]

        # get default value
        default_value = templar.template(self._get_value(variables, prefix, 'default'))

        # get distribution specific values
        for suffix in suffixes:
            dist_value = templar.template(self._get_value(variables, prefix, suffix))
            if dist_value is missing:
                continue
            if default_value is missing:
                return [dist_value]
            if isinstance(default_value, dict):
                return [merge_hash(default_value, dist_value, recursive, list_merge)]
            if isinstance(default_value, list):
                # reuse the 'merge_hash' implementation for combining the lists
                return [merge_hash({'l': default_value}, {'l': dist_value}, False, list_merge)['l']]
            return [dist_value]

        if default_value is missing:
            raise AnsibleLookupError(
                "No variable with prefix '{}' found. Searched for one of the following variables: {}".format(
                    prefix, ', '.join([prefix + '_' + s for s in suffixes + ['default']])))

        return [default_value]
