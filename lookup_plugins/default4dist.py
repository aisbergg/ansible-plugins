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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = '''
lookup: default4dist
author: Andre Lehmann <aisberg@posteo.de>
short_description: creates distribution dependent values
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

from collections.abc import MutableMapping, MutableSequence
from distutils.util import strtobool

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.parsing.splitter import parse_kv
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

__version__ = '1.0.0'
__license__ = 'MIT'
__email__ = 'aisberg@posteo.de'

display = Display()


# taken from Ansible 2.10
# https://github.com/ansible/ansible/blob/03a395cba45d16fe2e6f339242692a9e6a403c00/lib/ansible/utils/vars.py#L97
def merge_hash(x, y, recursive=True, list_merge='replace'):
    """
    Return a new dictionary result of the merges of y into x,
    so that keys from y take precedence over keys from x.
    (x and y aren't modified)
    """
    if list_merge not in ('replace', 'keep', 'append', 'prepend', 'append_rp', 'prepend_rp'):
        raise AnsibleError(
            "merge_hash: 'list_merge' argument can only be equal to 'replace', 'keep', 'append', 'prepend', 'append_rp' or 'prepend_rp'"
        )

    # verify x & y are dicts
    # _validate_mutable_mappings(x, y)

    # to speed things up: if x is empty or equal to y, return y
    # (this `if` can be remove without impact on the function
    #  except performance)
    if x == {} or x == y:
        return y.copy()

    # in the following we will copy elements from y to x, but
    # we don't want to modify x, so we create a copy of it
    x = x.copy()

    # to speed things up: use dict.update if possible
    # (this `if` can be remove without impact on the function
    #  except performance)
    if not recursive and list_merge == 'replace':
        x.update(y)
        return x

    # insert each element of y in x, overriding the one in x
    # (as y has higher priority)
    # we copy elements from y to x instead of x to y because
    # there is a high probability x will be the "default" dict the user
    # want to "patch" with y
    # therefore x will have much more elements than y
    for key, y_value in y.items():
        # if `key` isn't in x
        # update x and move on to the next element of y
        if key not in x:
            x[key] = y_value
            continue
        # from this point we know `key` is in x

        x_value = x[key]

        # if both x's element and y's element are dicts
        # recursively "combine" them or override x's with y's element
        # depending on the `recursive` argument
        # and move on to the next element of y
        if isinstance(x_value, MutableMapping) and isinstance(y_value, MutableMapping):
            if recursive:
                x[key] = merge_hash(x_value, y_value, recursive, list_merge)
            else:
                x[key] = y_value
            continue

        # if both x's element and y's element are lists
        # "merge" them depending on the `list_merge` argument
        # and move on to the next element of y
        if isinstance(x_value, MutableSequence) and isinstance(y_value, MutableSequence):
            if list_merge == 'replace':
                # replace x value by y's one as it has higher priority
                x[key] = y_value
            elif list_merge == 'append':
                x[key] = x_value + y_value
            elif list_merge == 'prepend':
                x[key] = y_value + x_value
            elif list_merge == 'append_rp':
                # append all elements from y_value (high prio) to x_value (low prio)
                # and remove x_value elements that are also in y_value
                # we don't remove elements from x_value nor y_value that were already in double
                # (we assume that there is a reason if there where such double elements)
                # _rp stands for "remove present"
                x[key] = [z for z in x_value if z not in y_value] + y_value
            elif list_merge == 'prepend_rp':
                # same as 'append_rp' but y_value elements are prepend
                x[key] = y_value + [z for z in x_value if z not in y_value]
            # else 'keep'
            #   keep x value even if y it's of higher priority
            #   it's done by not changing x[key]
            continue

        # else just override x's element with y's one
        x[key] = y_value

    return x


class LookupModule(LookupBase):

    def _parse_parameters(self, term):
        if isinstance(term, str):
            params = parse_kv(term)
        elif isinstance(term, dict):
            params = term
        else:
            raise AnsibleParserError("Unsupported parameter type '{}' passed to default4dist lookup.".format(
                type(term)))

        prefix = params.get('prefix', None)
        recursive = params.get('recursive', None)
        list_merge = params.get('list_merge', None)

        if '_raw_params' in params:
            raw_params = params['_raw_params'].split(' ')
            if len(raw_params) > 0 and not prefix:
                prefix = raw_params[0]
            if len(raw_params) > 1 and not recursive:
                recursive = raw_params[1]
            if len(raw_params) > 2 and not list_merge:
                list_merge = raw_params[2]

        if recursive:
            recursive = bool(strtobool(recursive))
        else:
            recursive = False

        if not list_merge:
            list_merge = 'replace'

        return prefix, recursive, list_merge

    def run(self, terms, variables=None, **kwargs):
        variables = variables or {}
        ret = []
        get_value = lambda prefix, suffix: variables.get(prefix + suffix, None) or variables.get(
            prefix + '_' + suffix, None)
        for term in terms:
            prefix, recursive, list_merge = self._parse_parameters(term)

            os_distribution = variables['ansible_distribution'].lower()
            os_familiy = variables['ansible_os_family'].lower()
            os_version = variables['ansible_distribution_version']
            os_major_version = str(variables['ansible_distribution_major_version'])
            os_release = variables['ansible_distribution_release']

            suffixes = {
                os_distribution + "_" + os_version,
                os_distribution + "_" + os_release,
                os_distribution + "_" + os_major_version,
                os_distribution,
                os_familiy + "_" + os_version,
                os_familiy + "_" + os_release,
                os_familiy + "_" + os_major_version,
                os_familiy,
            }

            # get default value
            default_value = get_value(prefix, 'default')

            # get distribution specific values
            for suffix in suffixes:

                dist_value = get_value(prefix, suffix)
                if dist_value is not None:
                    if default_value is not None:
                        if isinstance(default_value, dict):
                            ret.append(merge_hash(default_value, dist_value, recursive, list_merge))
                        elif isinstance(default_value, list):
                            ret.append(default_value + dist_value)
                        else:
                            ret.append(dist_value)
                    else:
                        ret.append(dist_value)
                    break
            else:
                ret.append(default_value)

        return ret
