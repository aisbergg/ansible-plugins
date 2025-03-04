# MIT License
#
# Copyright (c) 2025 Andre Lehmann
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
name: env_task
author: Andre Lehmann <aisberg@posteo.de>
short_description: return a list of task files found in the environment by searching through C(group_tasks) and C(host_tasks)
description: []
options:
  _terms:
    description: A file name.
  name:
    description: A file name.
    type: str
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

__version__ = '1.0.0'
__license__ = 'MIT'
__email__ = 'aisberg@posteo.de'


class LookupModule(LookupBase):
    _type = "tasks"

    def run(self, terms, variables=None, **kwargs):
        variables = variables or {}

        # no environment specified
        if not 'inventory_dir' in variables:
            return []

        base_path = Path(variables['inventory_dir'])
        subdir = getattr(self, '_subdir', 'files')
        results = []
        for term in terms:
            if isinstance(term, dict):
                fn = term.get('name')
            else:
                fn = term
            if not fn:
                continue

            # create a list of paths
            groups = ['all'] + sorted(variables['group_names'])
            host = variables['inventory_hostname']
            possible_task_files = [str(base_path / f'group_{self._type}' / g / fn) for g in groups] + \
                [str(base_path / f'host_{self._type}' / host / fn)]
            found_task_files = []
            for path in possible_task_files:
                try:
                    path = self._templar.template(path)
                except (AnsibleUndefinedVariable, UndefinedError) as e:
                    raise AnsibleLookupError(f"Failed to template path: {str(e)}")
                path = self.find_file_in_search_path(variables, subdir, path, ignore_missing=True)
                if path is not None:
                    results.append(path)

            # results.append(found_task_files)

        return results
