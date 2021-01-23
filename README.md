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
    - [`default4dist`](#default4dist)
    - [`keepassxc_browser_password`](#keepassxc_browser_password)
      - [Automatic Login (SSH And Become Password Lookup)](#automatic-login-ssh-and-become-password-lookup)
      - [Automatic Vault Decryption](#automatic-vault-decryption)
    - [`keepass_http_password`](#keepass_http_password)
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

#### `default4dist`

Creates distribution dependent values.

The default4dist lookup looks for a variable by a name prefix in combination with the OS distribution or family name and returns its value. This means, you don't have to create long chains of `ansible_distribution == 'Foo'` statements to build distribution dependent values.

The lookup will search for variables in form of `{prefix}{suffix}` or `{prefix}_{suffix}`. The first found variable will be used or optional combined (dict or list) with a default value. The suffix is constructed in the following order of precedence: 

- {distribution}_{version}
- {distribution}_{release}
- {distribution}_{major_version}
- {distribution}
- {familiy}_{version}
- {familiy}_{release}
- {familiy}_{major_version}
- {familiy}
- default

OS distribution and family names must be specified in lower case.

**Example:**

```yaml
# a simple value that differs on different Linux distributions
myvar: "{{
    'foo' if ansible_distribution == 'Debian' else
    'bar' if ansible_distribution == 'CentOS' and ansible_distribution_major_version == '8' else
    'baz'
}}"
# can be replaced by:
_myvar_default: baz
_myvar_debian: foo
_myvar_centos_8: bar
myvar: "{{ lookup('default4dist', '_myvar') }}"


# a dictionary that contains some distribution dependent values
myvar: "{{
    {'a': 1, 'b': foo} if ansible_distribution == 'Debian' else
    {'a': 2, 'b': bar} if ansible_distribution == 'CentOS' and ansible_distribution_major_version == '8' else
    {'a': 1, 'b': baz}
}}"
# can be replaced by:
_myvar_default: {'a': 1, 'b': baz}
_myvar_debian: {'b': bar}
_myvar_centos_8: {'a': 2, 'b': bar}
myvar: "{{ lookup('default4dist', '_myvar', recursive=True) }}"
```

#### `keepassxc_browser_password`

Retrieves a password from an opened KeePassXC database using the KeePassXC Browser protocol.

The plugin allows to automatically load sensitive information from KeePassXC into Ansible, thus can be used as an addition to or even replacement of the Ansible vault. Besides loading passwords for your database for example, you can also load the Ansible _become_ or _SSH_ password and avoid retyping it over and over again.

**Installation:**

The plugin requires the Python [`keepassxc_browser`](https://github.com/hrehfeld/python-keepassxc-browser) module. In particular the following version needs to be installed, wich contains a fix for an important bug:

```sh
pip install --user git+https://github.com/piegamesde/python-keepassxc-browser.git@cdf44db9f9fe696dd5863008b7c594f9e0bdaf28
```

**Example:**

```yml
- set_fact:
    # simple password lookup by URL
    var1: "{{ lookup('keepassxc_browser_password', 'https://example.org') }}"
    # password lookup by URL and login name
    # the protocol part 'ansible://' is required to form a valid URL, it doesn't have to be 'https://' or else
    var2: "{{ lookup('keepassxc_browser_password', 'url=ansible://mysql login=root') }}"
    # password lookup by URL and name
    var3: "{{ lookup('keepassxc_browser_password', 'url=ansible://secret name=\"My Secret\"') }}"
    # password lookup by URL and group
    var4: "{{ lookup('keepassxc_browser_password', 'url=ansible://secret group=department_x') }}"
```

##### Automatic Login (SSH And Become Password Lookup)

You can use the plugin to lookup the _Become_  and/or _SSH_ passwords on Ansible startup, so you don't have to type these in all the time. There are two things you need to do to make it work:

1. Add a lookup for your _Become_  and/or _SSH_ passwords:
    ```yml
    # group_vars/all
    _ansible_become_pass: "{{ lookup('keepass_http_password', 'ansible://linux-user login=foo') }}"
    _ansible_ssh_pass: "{{ lookup('keepass_http_password', 'ansible://linux-user login=foo') }}"
    ```

2. Statically evaluate the `ansible_ssh_pass` and `ansible_become_pass` in your playbook. This is a necessary step to avoid a relatively "slow" password lookup for every single task, because Ansible won't cache any lookups:
    ```yaml
    # playbook.yml
    - hosts: xxx
      pre_tasks:
        - set_fact:
            ansible_ssh_pass: "{{ ansible_ssh_pass | default(_ansible_ssh_pass) | default(omit) }}"
            ansible_become_pass: "{{ ansible_become_pass | default(_ansible_become_pass) | default(omit) }}"
          tags: always
          no_log: true
    ```

##### Automatic Vault Decryption

It is also possible to automate the vault decryption, it requires an additional script to accomplish though. I created a [Vault Password Client Script](https://docs.ansible.com/ansible/latest/user_guide/vault.html#vault-password-client-scripts) for that purpose, that reuses some of the code of the lookup plugin:

`vault-pass-client.py` :
```python
import argparse
import sys
from pathlib import Path

from ansible.errors import AnsibleError

RELATIVE_PATH_TO_PLUGIN_DIR = '../../plugins/lookup/'

sys.path.append(str(Path(__file__).parent.joinpath(RELATIVE_PATH_TO_PLUGIN_DIR).resolve()))
from keepassxc_browser import Connection, Identity, ProtocolError
from keepassxc_browser_password import KeePassXCBrowserPasswordLookup

__author__  = 'Andre Lehmann'
__email__   = 'aisberg@posteo.de'
__version__ = '1.1.0'
__license__ = 'MIT'


def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--vault-id', dest='vault_id', required=True, help='The vault ID')
    args = parser.parse_args(sys.argv[1:])

    try:
        lookup = KeePassXCBrowserPasswordLookup()
    except ProtocolError as excp:
        raise AnsibleError("Failed to establish a connection to KeePassXC: {}".format(excp))
    except Exception as excp:
        raise AnsibleError("KeePassXC password lookup execution failed: {}".format(excp))

    try:
        url = 'ansible://ansible-vault'
        filters = dict(login=args.vault_id)
        vault_pass = lookup.get_password(url=url, filters=filters)
    except Exception as ex:
        del lookup
        raise AnsibleError(str(ex))

    sys.stdout.write(vault_pass + '\n')


if __name__ == '__main__':
    main()
```

The script needs to be saved as `*-client.py` in order to work. One thing that need to be changed, is the path (`RELATIVE_PATH_TO_PLUGIN_DIR`) to the plugin dir containing the keepassxc_browser_password lookup plugin. That's done, you can use it as follows:

1. Save the vault password in KeePassXC:
   - Username: `myuser`
   - Password: `myvaultpass`
   - URL: `ansible://ansible-vault`
2. Run Ansible: `ansible-playbook --vault-id myuser@/path/to/vault-pass-client.py ...`

#### `keepass_http_password`

Retrieves a password from an opened KeePass database using the KeePass HTTP protocol.

This plugin works much like the [`keepassxc_browser_password`](#keepassxc_browser_password) plugin and offers similar features.

**Installation:**

The plugin requires the Python [`keepasshttp`](https://github.com/cyrbil/python_keepass_http) module. You can install it via `pip install --user keepasshttp`. After that the plugin just needs to be copied into dir `lookup_plugins` in your Ansible repository.

**Example:**

```yml
- set_fact:
    # simple password lookup by URL
    var1: "{{ lookup('keepass_http_password', 'https://example.org') }}"
    # password lookup by URL and login name
    # the protocol part 'ansible://' is required to form a valid URL, it doesn't have to be 'https://' or else
    var2: "{{ lookup('keepass_http_password', 'url=https://mysql login=root') }}"
    # password lookup by URL and name
    var3: "{{ lookup('keepass_http_password', 'url=https://secret name=\"My Secret\"') }}"
```

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
