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


class GVariantEncoder(object):

    def encode(self, o):
        chunks = self._iterencode(o)
        if not isinstance(chunks, (list, tuple)):
            chunks = list(chunks)
        return ''.join(chunks)

    def _iterencode(self, o):
        if isinstance(o, str):
            yield "'" + o + "'"
        elif o is None:
            yield "null"
        elif o is True:
            yield "true"
        elif o is False:
            yield "false"
        elif isinstance(o, int):
            yield int.__str__(o)
        elif isinstance(o, float):
            yield float.__str__(o)
        elif isinstance(o, list):
            if not o:
                yield "[]"
                return
            yield "["
            first = True
            for item in o:
                if not first:
                    yield ", "
                yield from self._iterencode(item)
                first = False
            yield "]"
        elif isinstance(o, tuple):
            if not o:
                yield "()"
                return
            yield "("
            first = True
            for item in o:
                if not first:
                    yield ", "
                yield from self._iterencode(item)
                first = False
            yield ")"
        elif isinstance(o, dict):
            if not o:
                yield "{}"
                return
            yield "{"
            first = True
            for k, v in o.items():
                if not first:
                    yield ", "
                yield "'" + k + "': "
                yield from self._iterencode(v)
                first = False
            yield "}"
        else:
            raise TypeError(f"Object of type {o.__class__.__name__} is not GVariant serializable")


class FilterModule(object):

    def filters(self):
        return {
            "to_gvariant": self.to_gvariant,
        }

    def to_gvariant(self, value):
        """Convert a value to GVariant Text Format.

        All standard Python types are supported. Advanced GVariant types might
        be missing, but those might not really be required to use the 'dconf'
        module for example.

        Args: value (object): The object to be converted.

        Returns: str: GVariant text formatted string.
        """
        return GVariantEncoder().encode(value)
