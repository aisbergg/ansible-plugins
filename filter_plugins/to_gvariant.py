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
