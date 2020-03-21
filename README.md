# Ansible Plugins

This repository contains filter and test plugins to be used with Ansible.

**Table of contents:**

- [Filter Plugins](#filter-plugins)
  - [Install](#install)
  - [Reference](#reference)
    - [`selectattr2`](#selectattr2)
    - [`pbkdf2_hash`](#pbkdf2hash)
- [Test Plugins](#test-plugins)
  - [Install](#install-1)
  - [Reference](#reference-1)
    - [`bool`](#bool)
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

To install one or more _filters_ in an Ansible Playbook or Ansible Role, add a directory named `filter_plugins` and place the filter (Python script) inside it.

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

## Test Plugins

Tests are used to evaluate template expressions and return either True or False. Tests are used as follows:

```django
# using a test on `some_variable`
{% if some_variable is test %}{% endif %}

# a test with extra arguments
{% if some_variable is test(arg1='foo', arg2='bar') %}{% endif %}
```

### Install

To install one or more _tests_ in an Ansible Playbook or Ansible Role, add a directory named `test_plugins` and place the test (Python script) inside it.

### Reference

#### `bool`

Test if a value is of type boolean.

Example:
```django
{% if foo is bool %}{{ foo | ternary('yes', 'no') }}{% endif %}
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
