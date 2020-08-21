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
    - [`keepassxc_lookup`](#keepassxc_lookup)
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

Example:
```django
{{ plain_password | pbkdf2_hash(rounds=50000, scheme='sha512') }}
```

#### `to_gvariant`

Convert a value to GVariant Text Format.

Example:
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

#### `keepassxc_lookup`

Retrieves a password from an opened KeepassXC database using the KeepassXC Browser protocol.

The plugin requires the Python [`keepassxy_browser`](https://github.com/hrehfeld/python-keepassxc-browser) module. In particular the following version needs to be installed, wich contains a fix for an important bug:

```sh
pip install --user git+https://github.com/piegamesde/python-keepassxc-browser.git@cdf44db9f9fe696dd5863008b7c594f9e0bdaf28
```

Example:
```yml
- set_fact:
    # simple password lookup by URL
    var1: "{{ lookup('keepassxc_password', 'https://example.org') }}"
    # password lookup by URL and login name
    var2: "{{ lookup('keepassxc_password', 'url=ansible://mysql login=root') }}"
    # password lookup by URL and name
    var3: "{{ lookup('keepassxc_password', 'url=ansible://secret name=\"My Secret\"') }}"
    # password lookup by URL and group
    var4: "{{ lookup('keepassxc_password', 'url=ansible://secret group=department_x') }}"
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

Example:
```django
{% if foo is boolean %}{{ foo | ternary('yes', 'no') }}{% endif %}
```

#### `list`

Test if a value is of type list.

Example:
```django
{% if foo is list %}{{ foo | join(', ') }}{% endif %}
```

## License

MIT

## Author Information

Andre Lehmann (aisberg@posteo.de)
