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

from ansible import errors


class FilterModule(object):

    def filters(self):
        return {"pbkdf2_hash": self.pbkdf2_hash}

    def pbkdf2_hash(self, password, rounds=29000, scheme="sha256"):
        """Create a password hash using pbkdf2.

        Args:
            password (str): The plaintext password to be hashed.
            rounds (int, optional): The number of hashing rounds to be applied.
                Defaults to 29000.
            scheme (str, optional): The hashing scheme to be used. Defaults to
                "sha256".

        Raises:
            errors.AnsibleFilterError: If the 'passlib' is missing or an
                unknown hash scheme was specified

        Returns:
            str: Hashed representation of the password.
        """
        try:
            import passlib.hash
        except ImportError:
            raise errors.AnsibleFilterError("Missing required Python module 'passlib'")

        hash_function = {
            "sha1": passlib.hash.pbkdf2_sha1,
            "sha256": passlib.hash.pbkdf2_sha256,
            "sha512": passlib.hash.pbkdf2_sha512,
        }

        if not scheme in hash_function:
            raise errors.AnsibleFilterError("Unknown hash scheme '{}'".format(scheme))

        return hash_function[scheme].using(rounds=rounds, salt_size=16).hash(password)
