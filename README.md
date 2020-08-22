# Ansible Plugins

This repository contains custom Ansible plugins, that can be used in Ansible Roles and Playbooks.

**Table of contents:**

- [Filter Plugins](#filter-plugins)
  - [Install](#install)
  - [Reference](#reference)
    - [`selectattr2`](#selectattr2)
    - [`pbkdf2_hash`](#pbkdf2_hash)
    - [`to_gvariant`](#to_gvariant)
- [Lookup Plugins](#lookup-plugins)
  - [Install](#install-1)
  - [Reference](#reference-1)
    - [`keepassxc_password`](#keepassxc_password)
- [Test Plugins](#test-plugins)
  - [Install](#install-2)
  - [Reference](#reference-2)
    - [`boolean`](#boolean)
    - [`list`](#list)
- [License](#license)
- [Author Information](#author-information)

---

## Filter Plugins

Filters are used to transform data inside template expressions. In general filters are used in the following fashion:

```django
# apply a filter to `some_variable`
{{ some_variable | filter }}

# apply a filter with extra arguments
{{ some_variable | filter(arg1='foo', arg2='bar') }}
```

### Install

To install one or more _filters_ in an Ansible Playbook or Ansible Role, add a directory named `filter_plugins` and place the _filters_ (Python scripts) inside it.

### Reference

#### `selectattr2`

Filter a sequence of objects by applying a test to the specified attribute of each object, and only selecting the objects with the test succeeding.

The built-in Jinja2 filter [`selectattr`](https://jinja.palletsprojects.com/en/2.11.x/templates/#selectattr) fails whenever the attribute is missing in one or more objects of the sequence. The `selectattr2` is designed to not fail under such conditions and allows to specify a default value for missing attributes.

Examples:
```django
# select objects, where the attribute is defined
{{ users | selectattr2('name', 'defined') | list }}

# select objects, where the attribute is equal to a value
{{ users | selectattr2('state', '==', 'present', default='present') | list }}
```

#### `pbkdf2_hash`

Create a password hash using pbkdf2.

**Example:**

```django
{{ plain_password | pbkdf2_hash(rounds=50000, scheme='sha512') }}
```

#### `to_gvariant`

Convert a value to GVariant Text Format.

**Example:**

```django
{{ [1, 3.14, True, "foo", {"bar": 0}, ("foo", "bar")] | to_gvariant() }}
-> [1, 3.14, true, 'foo', {'bar': 0}, ('foo', 'bar')]
```

## Lookup Plugins

Lookup plugins allow Ansible to access data from outside sources. Lookups are used as follows:

```yaml
- set_fact:
    # retrieve or generate a random password
    var: "{{ lookup('password', '/tmp/passwordfile') }}"
```

### Install

To install one or more _lookups_ in an Ansible Playbook or Ansible Role, add a directory named `lookup_plugins` and place the _lookups_ (Python scripts) inside it.

### Reference

#### `keepassxc_password`

Retrieves a password from an opened KeepassXC database using the KeepassXC Browser protocol.

The plugin allows to automatically load sensitive information from KeepassXC into Ansible, thus can be used as an addition to or even replacement of the Ansible vault. Besides loading passwords for your database for example, you can also load the Ansible _become_ or _SSH_ password and avoid retyping it over and over again.

**Installation:**

The plugin requires the Python [`keepassxy_browser`](https://github.com/hrehfeld/python-keepassxc-browser) module. In particular the following version needs to be installed, wich contains a fix for an important bug:

```sh
pip install --user git+https://github.com/piegamesde/python-keepassxc-browser.git@cdf44db9f9fe696dd5863008b7c594f9e0bdaf28
```

**Example:**

```yml
- set_fact:
    # simple password lookup by URL
    var1: "{{ lookup('keepassxc_password', 'https://example.org') }}"
    # password lookup by URL and login name
    # the protocol part 'ansible://' is required to form a valid URL, it doesn't have to be 'https://' or else
    var2: "{{ lookup('keepassxc_password', 'url=ansible://mysql login=root') }}"
    # password lookup by URL and name
    var3: "{{ lookup('keepassxc_password', 'url=ansible://secret name=\"My Secret\"') }}"
    # password lookup by URL and group
    var4: "{{ lookup('keepassxc_password', 'url=ansible://secret group=department_x') }}"
```

To automatically load the _become_  or _SSH_ password on Ansible startup, simply add a lookup to your `group_vars/all`:

```yml
ansible_become_pass: "{{ lookup('keepassxc_password', 'ansible://linux-user login=andre') }}"
ansible_ssh_pass: "{{ lookup('keepassxc_password', 'ansible://linux-user login=andre') }}"
```

It is also possible to automate the vault decryption, it requires an additional script to accomplish though. I created a [Vault Password Client Script](https://docs.ansible.com/ansible/latest/user_guide/vault.html#vault-password-client-scripts) for that purpose, that reuses some of the code of the lookup plugin:

`vault-pass-client.py` :
```python
import argparse
import sys
from pathlib import Path

from ansible.errors import AnsibleError

RELATIVE_PATH_TO_PLUGIN_DIR = "../../plugins/lookup/"

sys.path.append(str(Path(__file__).parent.joinpath(RELATIVE_PATH_TO_PLUGIN_DIR).resolve()))
from keepassxc_browser import Connection, Identity, ProtocolError
from keepassxc_password import KeepassXCPasswordLookup

__author__  = "Andre Lehmann"
__email__   = "aisberg@posteo.de"
__version__ = "1.0.0"
__license__ = "MIT"


def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-id", dest="vault_id", required=True, help="The vault ID")
    args = parser.parse_args(sys.argv[1:])

    try:
        lookup = KeepassXCPasswordLookup()
    except ProtocolError as excp:
        raise AnsibleError("Failed to establish a connection to KeepassXC: {}".format(excp))
    except Exception as excp:
        raise AnsibleError("KeepassXC password lookup execution failed: {}".format(excp))

    try:
        url = "ansible://ansible-vault"
        specifiers = dict(login=args.vault_id)
        vault_pass = lookup.get_password(url=url, specifiers=specifiers)
    except Exception as ex:
        del lookup
        raise AnsibleError(str(ex))

    sys.stdout.write(vault_pass + "\n")


if __name__ == "__main__":
    main()
```

The script needs to be saved as `*-client.py` in order to work. One thing that need to be changed, is the path (`RELATIVE_PATH_TO_PLUGIN_DIR`) to the plugin dir containing the keepassxc_password lookup plugin. That's done, you can use it as follows:

1. Save the vault password in KeepassXC:
   - Username: `myuser`
   - Password: `myvaultpass`
   - URL: `ansible://ansible-vault`
2. Run Ansible: `ansible-playbook --vault-id myuser@/path/to/vault-pass-client.py ...`

## Test Plugins

Tests are used to evaluate template expressions and return either True or False. Tests are used as follows:

```django
# using a test on `some_variable`
{% if some_variable is test %}{% endif %}

# a test with extra arguments
{% if some_variable is test(arg1='foo', arg2='bar') %}{% endif %}
```

### Install

To install one or more _tests_ in an Ansible Playbook or Ansible Role, add a directory named `test_plugins` and place the _tests_ (Python scripts) inside it.

### Reference

#### `boolean`

Test if a value is of type boolean.

This test plugin can be used until Ansible adapts Jinja2 version 2.11, which comes with this filter built-in ([see](https://jinja.palletsprojects.com/en/2.11.x/templates/#boolean)). 

**Example:**

```django
{% if foo is boolean %}{{ foo | ternary('yes', 'no') }}{% endif %}
```

#### `list`

Test if a value is of type list.

**Example:**

```django
{% if foo is list %}{{ foo | join(', ') }}{% endif %}
```

## License

MIT

## Author Information

Andre Lehmann (aisberg@posteo.de)
