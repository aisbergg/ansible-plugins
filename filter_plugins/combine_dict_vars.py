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

import re
from collections.abc import MutableMapping, MutableSequence

from ansible import errors


class FilterModule(object):

    def filters(self):
        return {"combine_dict_vars": self.combine_dict_vars}

    def combine_dict_vars(self, vars, pattern, recursive=False, list_merge="replace"):
        """Combine mapping variables, that match a specified pattern into a single dict."""
        result = {}
        for key in sorted(vars.keys()):
            if re.match(pattern, key):
                value = vars[key]
                if not isinstance(value, dict):
                    raise errors.AnsibleFilterError("Failed to combine vars: '{}' is not of type 'dict'".format(key))
                result = merge_hash(result, value, recursive=recursive, list_merge=list_merge)
        return result

# taken from Ansible 2.10
# https://github.com/ansible/ansible/blob/03a395cba45d16fe2e6f339242692a9e6a403c00/lib/ansible/utils/vars.py#L97
def merge_hash(x, y, recursive=True, list_merge='replace'):
    """
    Return a new dictionary result of the merges of y into x,
    so that keys from y take precedence over keys from x.
    (x and y aren't modified)
    """
    if list_merge not in ('replace', 'keep', 'append', 'prepend', 'append_rp', 'prepend_rp'):
        raise AnsibleError("merge_hash: 'list_merge' argument can only be equal to 'replace', 'keep', 'append', 'prepend', 'append_rp' or 'prepend_rp'")

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
    for key, y_value in iteritems(y):
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
