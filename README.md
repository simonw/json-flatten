# json-flatten

[![PyPI](https://img.shields.io/pypi/v/json-flatten.svg)](https://pypi.org/project/json-flatten/)
[![Changelog](https://img.shields.io/github/v/release/simonw/json-flatten?include_prereleases&label=changelog)](https://github.com/simonw/json-flatten/releases)
[![Tests](https://github.com/simonw/json-flatten/workflows/Test/badge.svg)](https://github.com/simonw/json-flatten/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/json-flatten/blob/main/LICENSE)


Python functions for flattening a JSON object to a single dictionary of pairs, and unflattening that dictionary back to a JSON object.

Useful if you need to represent a JSON object using a regular HTML form or transmit it as a set of query string parameters.

For example:

```pycon
>>> import json_flatten
>>> json_flatten.flatten({"foo": {"bar": [1, True, None]}})
{'foo.bar.[0]$int': '1', 'foo.bar.[1]$bool': 'True', 'foo.bar.[2]$none': 'None'}
>>> json_flatten.unflatten(_)
{'foo': {'bar': [1, True, None]}}
```
