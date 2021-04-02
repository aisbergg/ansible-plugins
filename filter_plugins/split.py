class FilterModule(object):

    def filters(self):
        return {"split": self.split}

    def split(self, value, sep=None, maxsplit=-1):
        """Split a string by a specified seperator string.

        Splitting a string with Jinja can already accomplished by executing the
        "split" method on strings, but when you want to use split in combination
        with "map" for example, you need a filter like this one.

        Args:
            value (str): The string value to be splitted.
            sep (str, optional): The seperator string.
            maxsplit (int, optional): Number of splits to do. Defaults to "-1".

        Returns:
            list: A splitted representation of the string.

        Examples:
            {{ 'Hello World' | split(' ') }} -> ['Hello', 'World']
        """
        return str(value).split(sep, maxsplit)
