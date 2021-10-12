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


from types import GeneratorType


class TestModule(object):

    def tests(self):
        return {
            'list': self.is_list,
        }

    def is_list(self, value):
        """Test if a value a list or generator type.

        Jinja2 provides the tests `iterable` and `sequence`, but those also
        match strings and dicts as well. To determine, if a value is essentially
        a list, you need to check the following:

            value is not string and value is not mapping and value is iterable

        This test is a shortcut, which allows to check for a list or generator
        simply with:

            value is list

        Args:
            value: A value, that shall be type tested

        Returns:
            bool: True, if value is of type list or generator, False otherwise.
        """
        return isinstance(value, (list, GeneratorType))
