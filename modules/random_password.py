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

DOCUMENTATION = '''
module: random_password
author: Andre Lehmann <aisberg@posteo.de>
short_description: Generate a random password and optionally save it to a file on the target.
description:
    - This module generates a random password of specified length and character set. It can optionally save the generated password to a file.
options:
    chars:
        description: A comma-separated list of character sets to use for generating the password. Defaults to 'ascii_letters, digits, .,:-_'. Available character sets are 'ascii_letters', 'digits', 'punctuation', 'whitespace', 'printable', and 'custom'.
        type: str
        default: ""
    length:
        description: Length of the password to generate.
        type: int
        default: 20
    file:
        description: Path to the file where the generated password will be saved. Set to "/dev/null" to skip saving.
        type: str
        default: "/etc/ansible/password"
    var_name:
        description: If provided, the generated password will be assigned to this Ansible variable.
        type: str
        default: None
    mode:
        description: File mode (permissions) to set on the password file. Use octal notation, e.g., 0644.
        type: int
        default: None
    owner:
        description: Owner of the password file.
        type: str
        default: None
    group:
        description: Group owner of the password file.
        type: str
        default: None
notes:
    - This module can generate passwords using various character sets. Specify the desired character sets in the 'chars' option as a comma-separated list. For example, 'ascii_letters, digits'.
    - The generated password will be stored in the 'password' result field.
    - To skip saving the generated password to a file, set the 'file' option to "/dev/null".
    - This module supports check mode.
'''

EXAMPLES = '''
# Generate a random password with default settings and save it to /etc/ansible/password
- name: Generate and save a password
  random_password:

# Generate a random password using a custom character set and assign it to the 'my_password' variable
- name: Generate and assign a password
  random_password:
    chars: "digits, punctuation"
    length: 12
    var_name: my_password

# Generate a random password and set specific file permissions and ownership
- name: Generate and set file permissions
  random_password:
    mode: 0600
    owner: ansible
    group: ansible
'''

RETURN = '''
password:
    description: The generated random password.
    type: str
    returned: always
    sample: "aB3#dE6@"
changed:
    description: Indicates whether the password was changed (generated or saved).
    type: bool
    returned: always
    sample: true
ansible_facts:
    description: Ansible facts dictionary containing the generated password if 'var_name' is provided.
    type: dict
    returned: when 'var_name' is provided
    sample: {"my_password": "aB3#dE6@"}
'''

import random
import string
from pathlib import Path

from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.basic import AnsibleModule


def _create_password(chars_spec, length):
    chars_spec = chars_spec.strip()
    if chars_spec:
        chars_spec = [s.strip() for s in chars_spec.split(",")]
    else:
        chars_spec = ["ascii_letters", "digits", ".,:-_"]

    # turn chars spec into actual chars
    chars = [to_text(getattr(string, to_native(s), s), errors='strict') for s in chars_spec]
    chars = "".join(chars)

    return "".join(random.SystemRandom().choices(chars, k=length))


def _read_password_file(file_path):
    """Read the contents of a password file.

    Args:
        file_path (pathlib.Path): The path of the password file

    Returns:
        str or None: Content of the password file
    """
    content = None

    if file_path.exists():
        content = file_path.read_text()

    return content


def _write_password_file(file_path, content, mode):
    """Write a password to a file.

    Args:
        file_path (pathlib.Path): Path of the password file.
        content (str): Content to be saved to the password file.
        mode (int): File mode of the password file.

    Raises:
        OSError: If directories could not be created or failed to write to file.
    """
    if file_path == "/dev/null":
        return

    if file_path.exists() and not file_path.is_file():
        raise OSError("Failed to save password to file, the given path '{}' exists and is not a file".format(
            str(file_path)))

    # create parent directory
    try:
        file_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    except Exception as ex:
        raise OSError("Failed to create parent directory '{}': {}".format(str(file_path.parent), str(ex)))

    # save password to file
    try:
        with file_path.open(mode="w") as fid:
            file_path.chmod(mode)
            fid.write(content)
    except Exception as ex:
        raise OSError("Failed to save password to file '{}': {}".format(str(file_path.parent), str(ex)))


def main():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        chars=dict(type="str", default=""),
        length=dict(type="int", default=20),
        file=dict(type="str", default="/etc/ansible/passwords/password"),
        var_name=dict(type="str", default=None),
    )
    module = AnsibleModule(
        argument_spec=module_args,
        add_file_common_args=True,
        supports_check_mode=True,
    )

    chars_spec = module.params["chars"]
    length = module.params["length"]
    file_path = Path(module.params["file"])
    var_name = module.params["var_name"]
    mode = module.params["mode"] or 0o400
    owner = module.params["owner"]
    group = module.params["group"]

    result = dict(changed=False)

    # load password from file, if exists
    if file_path != Path("/dev/null") and file_path.exists():
        try:
            result["password"] = _read_password_file(file_path)
        except Exception as ex:
            module.fail_json(msg="Failed to read password file '{}': {}".format(str(file_path), str(ex)), **result)

    # create new password and save to file for idempotence
    else:
        # create password
        result["password"] = _create_password(chars_spec, length)

        if module.check_mode:
            result["changed"] = True
            module.exit_json(**result)

        # write password to file
        try:
            _write_password_file(file_path, result["password"], mode)
        except OSError as ex:
            module.fail_json(msg=str(ex), **result)

    # set owner, group and mode
    if mode is not None:
        module.set_mode_if_different(file_path, mode, False)
    if owner is not None:
        module.set_owner_if_different(file_path, owner, False)
    if group is not None:
        module.set_group_if_different(file_path, group, False)

    if var_name:
        result["ansible_facts"] = {var_name: result["password"]}

    # end
    module.exit_json(**result)


if __name__ == '__main__':
    main()
