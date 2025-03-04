# MIT License
#
# Copyright (c) 2022 Andre Lehmann
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
name: env_file
author: Andre Lehmann <aisberg@posteo.de>
short_description: return first file found in the environment by searching through C(group_files) and C(host_files)
description: []
options:
  _terms:
    description: A file name.
  name:
    description: A file name.
    type: str
  skip:
    type: boolean
    default: False
    description: Return an empty list if no file is found, instead of an error.
'''

EXAMPLES = ''''''

RETURN = '''
_raw:
  description:
    - path to file found
  type: list
  elements: path
'''

from pathlib import Path

from ansible.errors import AnsibleLookupError, AnsibleUndefinedVariable
from ansible.plugins.lookup import LookupBase
from jinja2.exceptions import UndefinedError

__version__ = '0.10.0'
__license__ = 'MIT'
__email__ = 'aisberg@posteo.de'


class LookupModule(LookupBase):
    _type = "files"

    def run(self, terms, variables=None, **kwargs):
        variables = variables or {}

        # no environment specified
        if not 'inventory_dir' in variables:
            return []

        base_path = Path(variables['inventory_dir'])
        skip = kwargs.get('skip', False)
        subdir = getattr(self, '_subdir', 'files')
        results = []
        for term in terms:
            if isinstance(term, dict):
                fn = term.get('name')
                skip = term.get('skip', skip)
            else:
                fn = term
            if not fn:
                continue

            # create a list of paths
            groups = sorted(variables['group_names'], reverse=True) + ['all']
            host = variables['inventory_hostname']
            paths = [str(base_path / f'host_{self._type}' / host / fn)] + \
                [str(base_path / f'group_{self._type}' / g / fn) for g in groups]

            for path in paths:
                try:
                    path = self._templar.template(path)
                except (AnsibleUndefinedVariable, UndefinedError):
                    continue
                path = self.find_file_in_search_path(variables, subdir, path, ignore_missing=True)
                if path is not None:
                    results.append(path)
                    break
            else:
                if skip:
                    return []
                raise AnsibleLookupError(f"No file was found. Searched in: {str(paths)}")

        return results
