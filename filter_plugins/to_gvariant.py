import json
from json.encoder import JSONEncoder, _make_iterencode


class GVariantDumper(JSONEncoder):

    def encode(self, o):
        if isinstance(o, str):
            return self.encode_basestring(o)
        return super().encode(o)

    def encode_basestring(self, value):
        """Encode strings with single quotes."""
        return f"'{value}'"

    def iterencode(self, o, _one_shot=False):
        _markers = None
        _encoder = self.encode_basestring
        _floatstr = float.__repr__
        _iterencode = _make_iterencode(_markers, self.default, _encoder, self.indent, _floatstr, self.key_separator,
                                       self.item_separator, self.sort_keys, self.skipkeys, _one_shot)
        return _iterencode(o, 0)


class FilterModule(object):

    def filters(self):
        return {
            "to_gvariant": self.to_gvariant,
        }

    def to_gvariant(self, value):
        """Convert a value to GVariant Text Format.

        The GVariant Text Format is quite similar to the JSON format, which
        inspired me to use the Python JSON encoder to create the GVariant Text
        Format. The encoder supports the basic types, but lacks the support of
        advanced GVariant types.

        Args: value (object): The object to be converted.

        Returns: str: GVariant text formatted string.
        """
        return json.dumps(value, cls=GVariantDumper)
